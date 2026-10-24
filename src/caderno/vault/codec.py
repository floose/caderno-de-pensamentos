"""CPV1 file codec backed by PyNaCl/libsodium secretstream."""

from __future__ import annotations

import hashlib
import io
import json
import os
import struct
import unicodedata

from .model import AuthenticationError, InvalidVaultError, VaultAttachment, VaultSnapshot

MAGIC = b"CPVAULT\0"
VERSION = 1
OPS = 3
MEM = 268435456
SALT_BYTES = 16
CHUNK = 65536
STREAM_ABYTES = 17
MAX_FILE = 14 * 1024 * 1024
MAX_PLAINTEXT = 10 * 1024 * 1024
MAX_MANIFEST = 1 * 1024 * 1024
MAX_ATTACHMENTS = 256
MAX_ATTACHMENT = 8 * 1024 * 1024
MAX_AGGREGATE = 8 * 1024 * 1024
HEADER = struct.Struct(">8sHBBBIQ16s24s")


def _bindings():
    """Importa PyNaCl sob demanda para permitir inspecionar o pacote sem backend."""
    from nacl import bindings, pwhash

    return bindings, pwhash


def _password_bytes(password: str) -> bytes:
    """Aplica a normalização CPV1 e impõe o limite de bytes antes da KDF."""
    if not isinstance(password, str):
        raise TypeError("A senha deve ser texto")
    encoded = unicodedata.normalize("NFC", password).encode("utf-8")
    if not encoded or len(encoded) > 1024:
        raise ValueError("A senha deve ter entre 1 e 1024 bytes UTF-8")
    return encoded


def _derive(password: str, salt: bytes) -> bytes:
    """Deriva a chave CPV1 com perfil Argon2id fixo, nunca controlado pelo arquivo."""
    _, pwhash = _bindings()
    return pwhash.argon2id.kdf(32, _password_bytes(password), salt, opslimit=OPS, memlimit=MEM)


def _validate_file_size(size: int):
    """Rejeita arquivos fora dos limites globais antes de carregar o backend/KDF."""
    minimum = HEADER.size + 4 + STREAM_ABYTES
    if size < minimum or size > MAX_FILE:
        raise InvalidVaultError("Tamanho de arquivo CPV1 inválido")


def new_key(password: str) -> tuple[bytes, bytes]:
    """Gera salt aleatório e deriva a chave para uma nova gravação de cofre."""
    salt = os.urandom(SALT_BYTES)
    return salt, _derive(password, salt)


def _manifest(snapshot: VaultSnapshot) -> bytes:
    """Serializa documento e descritores; dados binários ficam em registros próprios."""
    attachments = []
    total = 0
    for item in snapshot.attachments:
        size = len(item.data)
        total += size
        attachments.append({"id": item.id, "name": item.name, "media_type": item.media_type, "size": size})
    if len(attachments) > MAX_ATTACHMENTS or total > MAX_AGGREGATE:
        raise ValueError("Limites de anexos excedidos")
    if any(len(a.data) > MAX_ATTACHMENT for a in snapshot.attachments):
        raise ValueError("Limite por anexo excedido")
    raw = json.dumps({"document": snapshot.document, "attachments": attachments}, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_MANIFEST:
        raise ValueError("Manifesto excede o limite")
    return raw


def _records(snapshot: VaultSnapshot):
    """Produz manifesto primeiro e registros binários de anexos na ordem declarada."""
    manifest = _manifest(snapshot)
    yield b"\x01" + struct.pack(">I", len(manifest)) + manifest
    for attachment in snapshot.attachments:
        ident = attachment.id.encode("utf-8")
        if not ident or len(ident) > 65535:
            raise ValueError("ID de anexo inválido")
        yield b"\x02" + struct.pack(">H", len(ident)) + ident + struct.pack(">Q", len(attachment.data))
        for offset in range(0, len(attachment.data), CHUNK):
            yield attachment.data[offset:offset + CHUNK]


def _header(salt: bytes, key: bytes):
    """Inicializa secretstream e monta o cabeçalho CPV1 usado como AAD."""
    bindings, _ = _bindings()
    state = bindings.crypto_secretstream_xchacha20poly1305_state()
    stream_header = bindings.crypto_secretstream_xchacha20poly1305_init_push(state, key)
    data = HEADER.pack(MAGIC, VERSION, 1, 1, 0, OPS, MEM, salt, stream_header)
    return data, key, state


def _write_frame(output, state, plaintext: bytes, aad: bytes, tag: int):
    """Autentica e grava um frame, respeitando o limite total do arquivo."""
    bindings, _ = _bindings()
    cipher = bindings.crypto_secretstream_xchacha20poly1305_push(state, plaintext, aad, tag)
    if output.tell() + 4 + len(cipher) > MAX_FILE:
        raise ValueError("Arquivo de cofre excede o limite")
    output.write(struct.pack(">I", len(cipher)))
    output.write(cipher)


def encrypt_file(output, snapshot: VaultSnapshot, salt: bytes, key: bytes):
    """Cifra registros em frames e encerra com TAG_FINAL; não fecha o stream."""
    bindings, _ = _bindings()
    aad, _, state = _header(salt, key)
    tag_message = bindings.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE
    tag_final = bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL
    output.write(aad)
    pending = bytearray()
    for record in _records(snapshot):
        pending.extend(record)
        while len(pending) >= CHUNK:
            _write_frame(output, state, bytes(pending[:CHUNK]), aad, tag_message)
            del pending[:CHUNK]
    if pending:
        _write_frame(output, state, bytes(pending), aad, tag_message)
    _write_frame(output, state, b"", aad, tag_final)
    output.flush()
    os.fsync(output.fileno())


def _read_header(source):
    """Valida todos os IDs e o perfil permitido antes de executar Argon2id."""
    raw = source.read(HEADER.size)
    if len(raw) != HEADER.size:
        raise InvalidVaultError("Arquivo de cofre inválido")
    magic, version, kdf, stream, flags, ops, mem, salt, stream_header = HEADER.unpack(raw)
    if (magic, version, kdf, stream, flags, ops, mem) != (MAGIC, 1, 1, 1, 0, OPS, MEM):
        raise InvalidVaultError("Arquivo de cofre inválido")
    return raw, salt, stream_header


def _read_cipher_frame(source, file_size: int) -> bytes:
    """Lê um frame limitado pelo tamanho restante e pelo máximo do protocolo."""
    frame_header = source.read(4)
    if len(frame_header) != 4:
        raise AuthenticationError("Senha incorreta ou arquivo alterado")
    frame_size = struct.unpack(">I", frame_header)[0]
    if frame_size < STREAM_ABYTES or frame_size > CHUNK + STREAM_ABYTES:
        raise AuthenticationError("Senha incorreta ou arquivo alterado")
    if frame_size > file_size - source.tell():
        raise AuthenticationError("Senha incorreta ou arquivo alterado")
    frame = source.read(frame_size)
    if len(frame) != frame_size:
        raise AuthenticationError("Senha incorreta ou arquivo alterado")
    return frame


def _require_eof(source):
    """Exige EOF logo após TAG_FINAL para rejeitar bytes anexados ao arquivo."""
    if source.read(1):
        raise AuthenticationError("Senha incorreta ou arquivo alterado")


def _is_final_frame(message: bytes, tag: int, tag_message: int, tag_final: int) -> bool:
    """Aceita mensagens de dados ou um marcador final vazio, rejeitando outras tags."""
    if tag == tag_final and not message:
        return True
    if tag == tag_message:
        return False
    raise AuthenticationError("Senha incorreta ou arquivo alterado")


def decrypt_file(path: str, password: str):
    """Valida, autentica e interpreta o cofre; retorna snapshot, chave e salt."""
    _validate_file_size(os.path.getsize(path))
    bindings, _ = _bindings()
    state = bindings.crypto_secretstream_xchacha20poly1305_state()
    tag_message = bindings.crypto_secretstream_xchacha20poly1305_TAG_MESSAGE
    tag_final = bindings.crypto_secretstream_xchacha20poly1305_TAG_FINAL
    try:
        return _decrypt(path, password, bindings, state, tag_message, tag_final)
    except AuthenticationError:
        raise
    except Exception as exc:
        raise AuthenticationError("Senha incorreta ou arquivo alterado") from exc


def _decrypt(path, password, bindings, state, tag_message, tag_final):
    """Autentica o stream inteiro antes de expor qualquer snapshot ao chamador."""
    size = os.path.getsize(path)
    _validate_file_size(size)
    with open(path, "rb") as source:
        aad, salt, stream_header = _read_header(source)
        key = _derive(password, salt)
        bindings.crypto_secretstream_xchacha20poly1305_init_pull(state, stream_header, key)
        plaintext = bytearray()
        final_seen = False
        while not final_seen:
            ciphertext = _read_cipher_frame(source, size)
            message, tag = bindings.crypto_secretstream_xchacha20poly1305_pull(state, ciphertext, aad)
            final_seen = _is_final_frame(message, tag, tag_message, tag_final)
            if not final_seen:
                if len(plaintext) + len(message) > MAX_PLAINTEXT:
                    raise InvalidVaultError("Conteúdo do cofre excede o limite")
                plaintext.extend(message)
        _require_eof(source)
    return _parse_plaintext(bytes(plaintext)), key, salt


def _parse_plaintext(raw: bytes) -> VaultSnapshot:
    """Valida framing, manifesto e schema antes de construir o snapshot imutável."""
    if len(raw) < 5 or raw[0] != 1:
        raise InvalidVaultError("Registros CPV1 inválidos")
    manifest_size = struct.unpack_from(">I", raw, 1)[0]
    if manifest_size > MAX_MANIFEST or 5 + manifest_size > len(raw):
        raise InvalidVaultError("Manifesto CPV1 inválido")
    manifest = json.loads(raw[5:5 + manifest_size].decode("utf-8"))
    if not isinstance(manifest, dict) or not isinstance(manifest.get("document"), dict):
        raise InvalidVaultError("Documento inválido")
    if manifest["document"].get("schema_version") != 1:
        raise InvalidVaultError("Versão de schema inválida")
    _check_document_bounds(manifest["document"])
    pos = 5 + manifest_size
    descriptors = manifest.get("attachments")
    if not isinstance(descriptors, list) or len(descriptors) > MAX_ATTACHMENTS:
        raise InvalidVaultError("Manifesto CPV1 inválido")
    attachments = _parse_attachments(raw, pos, descriptors)
    return VaultSnapshot(manifest["document"], attachments)


def _check_document_bounds(document: dict):
    """Limita nós e profundidade para conter estruturas JSON patológicas."""
    pending = [(document, 0)]
    nodes = 0
    while pending:
        value, depth = pending.pop()
        nodes += 1
        if nodes > 100_000 or depth > 64:
            raise InvalidVaultError("Estrutura do documento excede os limites")
        if isinstance(value, dict):
            pending.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)


def _parse_attachments(raw: bytes, pos: int, descriptors: list) -> tuple[VaultAttachment, ...]:
    """Confere IDs, referências e tamanhos dos anexos contra o manifesto autenticado."""
    expected = {str(item["id"]): item for item in descriptors}
    if len(expected) != len(descriptors):
        raise InvalidVaultError("IDs duplicados no manifesto")
    found = []
    seen = set()
    total = 0
    for _ in descriptors:
        if pos + 3 > len(raw) or raw[pos] != 2:
            raise InvalidVaultError("Registro de anexo inválido")
        ident_size = struct.unpack_from(">H", raw, pos + 1)[0]
        pos += 3
        if pos + ident_size + 8 > len(raw):
            raise InvalidVaultError("Registro de anexo truncado")
        ident = raw[pos:pos + ident_size].decode("utf-8")
        pos += ident_size
        size = struct.unpack_from(">Q", raw, pos)[0]
        pos += 8
        total += size
        if ident in seen or ident not in expected or size != expected[ident]["size"] or size > MAX_ATTACHMENT or total > MAX_AGGREGATE:
            raise InvalidVaultError("Anexo não corresponde ao manifesto")
        seen.add(ident)
        if pos + size > len(raw):
            raise InvalidVaultError("Dados de anexo truncados")
        found.append(VaultAttachment(ident, expected[ident]["name"], expected[ident]["media_type"], raw[pos:pos + size]))
        pos += size
    if pos != len(raw) or {a.id for a in found} != set(expected):
        raise InvalidVaultError("Registros extras ou ausentes")
    return tuple(found)
