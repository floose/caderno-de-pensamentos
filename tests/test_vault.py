import json
import io
import mimetypes
import random
import struct
from pathlib import Path

import pytest

from caderno.vault.codec import (
    HEADER, _is_final_frame, _manifest, _parse_plaintext, _read_cipher_frame,
    _read_header, _records, _require_eof,
)
from caderno.vault.model import AuthenticationError, InvalidVaultError, VaultAttachment, VaultSnapshot

ROOT = Path(__file__).parent


def fixture_snapshot():
    """Monta as duas notas curtas e a imagem PNG sintética usadas nos testes básicos."""
    document = json.loads((ROOT / "fixtures/cofre_exemplo.json").read_text())
    image = (ROOT / "fixtures/pixel.png").read_bytes()
    attachment = VaultAttachment("fixture-image-1", "pixel.png", "image/png", image)
    return VaultSnapshot(document, [attachment])


def volume_snapshot():
    """Carrega cinco notas longas e imagens locais; usa o PNG sintético se a pasta estiver vazia."""
    document = json.loads((ROOT / "fixtures/cofre_volume.json").read_text())
    image_dir = ROOT / "fixtures/imagens"
    image_paths = sorted(path for path in image_dir.iterdir() if path.is_file() and not path.name.startswith("."))
    if not image_paths:
        image_paths = [ROOT / "fixtures/pixel.png"]
    attachments = []
    for index, path in enumerate(image_paths, start=1):
        media_type = mimetypes.guess_type(path.name)[0]
        if not media_type or not media_type.startswith("image/"):
            raise ValueError(f"Arquivo de teste não reconhecido como imagem: {path.name}")
        attachment_id = f"volume-image-{index}"
        entry = document["entries"][(index - 1) % len(document["entries"])]
        entry["attachments"].append(attachment_id)
        document["attachments"].append({
            "id": attachment_id,
            "entry_id": entry["id"],
            "filename": path.name,
            "media_type": media_type,
        })
        attachments.append(VaultAttachment(attachment_id, path.name, media_type, path.read_bytes()))
    return VaultSnapshot(document, attachments)


def million_word_snapshot():
    """Gera 200 notas sintéticas de 5.000 palavras e associa as imagens de teste."""
    source = json.loads((ROOT / "fixtures/cofre_volume.json").read_text(encoding="utf-8"))
    vocabulary = [word.strip(".,") for entry in source["entries"] for word in entry["body_markdown"].split()]
    rng = random.Random(20261024)
    entries = []
    for index in range(200):
        body = " ".join(rng.choice(vocabulary) for _ in range(5000))
        entries.append({
            "id": f"million-entry-{index:03}",
            "title": f"Nota sintética {index + 1}",
            "body_markdown": body,
            "collection_id": "million-collection",
            "tags": ["teste-volume"],
            "created_at": "2026-10-24T09:00:00Z",
            "updated_at": "2026-10-24T09:00:00Z",
            "published_at": "2026-10-24T09:00:00Z",
            "favorite": False,
            "attachments": [],
        })
    document = {
        "schema_version": 1,
        "collections": [{"id": "million-collection", "name": "Coleção sintética"}],
        "attachments": [],
        "entries": entries,
    }
    attachments = volume_snapshot().attachments
    for index, attachment in enumerate(attachments):
        entry = entries[index % len(entries)]
        entry["attachments"].append(attachment.id)
        document["attachments"].append({
            "id": attachment.id,
            "entry_id": entry["id"],
            "filename": attachment.name,
            "media_type": attachment.media_type,
        })
    return VaultSnapshot(document, attachments)


def plaintext(snapshot):
    """Monta os registros internos sem cifrar, para testar o parser isoladamente."""
    return b"".join(_records(snapshot))


def test_snapshot_is_immutable_from_callers():
    """Confirma que alterações no JSON de entrada ou na cópia lida não mudam o snapshot."""
    document = {"items": [{"text": "original"}]}
    snapshot = VaultSnapshot(document)
    document["items"][0]["text"] = "changed"
    returned = snapshot.document
    returned["items"].clear()
    assert snapshot.document == {"items": [{"text": "original"}]}


def test_fixture_roundtrips_manifest_and_binary_attachment():
    """Testa serialização e leitura de texto/anexo, sem executar a cifra."""
    original = fixture_snapshot()
    restored = _parse_plaintext(plaintext(original))
    assert restored.document == original.document
    assert restored.attachments == original.attachments
    assert restored.attachments[0].data.startswith(b"\x89PNG\r\n\x1a\n")


def test_manifest_and_record_attachment_ids_must_match():
    """Confirma que o parser rejeita um ID de anexo divergente do manifesto."""
    snapshot = fixture_snapshot()
    content = bytearray(plaintext(snapshot))
    manifest_size = struct.unpack_from(">I", content, 1)[0]
    marker = content.find(b"fixture-image-1", 5 + manifest_size)
    content[marker:marker + len("fixture-image-1")] = b"fixture-image-2"
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(bytes(content))


def test_rejects_unbounded_manifest_before_parsing():
    """Confirma que um tamanho de manifesto acima do limite é rejeitado."""
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(b"\x01" + struct.pack(">I", 0xFFFFFFFF))


def test_manifest_is_json_and_contains_binary_size_only():
    """Confirma que o manifesto é JSON e não contém a imagem codificada em Base64."""
    raw = _manifest(fixture_snapshot())
    manifest = json.loads(raw)
    assert manifest["attachments"][0]["size"] == len(fixture_snapshot().attachments[0].data)
    assert "iVBOR" not in raw.decode()


def test_schema_version_is_required():
    """Confirma que o conteúdo precisa declarar uma versão de schema reconhecida."""
    raw = json.dumps({"document": {}, "attachments": []}).encode()
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(b"\x01" + struct.pack(">I", len(raw)) + raw)


def test_rejects_truncated_frame_and_bad_header_without_crypto_backend():
    """Testa framing inválido sem exigir PyNaCl nem derivar uma chave."""
    with pytest.raises(AuthenticationError):
        _read_cipher_frame(io.BytesIO(b"\x00\x00\x00\x20short"), 9)
    bad = HEADER.pack(b"BADMAGIC", 1, 1, 1, 0, 3, 268435456, b"s" * 16, b"h" * 24)
    with pytest.raises(InvalidVaultError):
        _read_header(io.BytesIO(bad))


def test_short_file_is_rejected_before_kdf_or_backend_import(tmp_path):
    """Confirma que arquivo curto é rejeitado antes de importar o backend criptográfico."""
    from caderno.vault.codec import decrypt_file

    target = tmp_path / "header-only.cpv"
    target.write_bytes(HEADER.pack(b"CPVAULT\0", 1, 1, 1, 0, 3, 268435456, b"s" * 16, b"h" * 24))
    with pytest.raises(InvalidVaultError):
        decrypt_file(str(target), "password")


def test_final_tag_must_be_empty_and_trailing_bytes_are_rejected():
    """Confirma que o stream termina em TAG_FINAL vazio e imediatamente chega ao EOF."""
    assert _is_final_frame(b"", 2, 0, 2)
    with pytest.raises(AuthenticationError):
        _is_final_frame(b"x", 2, 0, 2)
    with pytest.raises(AuthenticationError):
        _is_final_frame(b"", 3, 0, 2)
    with pytest.raises(AuthenticationError):
        _require_eof(io.BytesIO(b"extra"))


def test_create_no_overwrite_stale_session_and_failed_replace(tmp_path, monkeypatch):
    """Simula falhas de persistência, destino existente e edição concorrente."""
    import caderno.vault.api as api

    monkeypatch.setattr(api, "new_key", lambda password: (b"s" * 16, b"k" * 32))
    monkeypatch.setattr(api, "encrypt_file", lambda output, snapshot, salt, key: output.write(b"CPV test"))
    target = tmp_path / "test.cpv"
    session = api.create_vault(target, "password", fixture_snapshot())
    assert not hasattr(session, "_password")
    original = target.read_bytes()
    with pytest.raises(FileExistsError):
        api.create_vault(target, "password", fixture_snapshot())
    target.write_bytes(b"external edit")
    with pytest.raises(api.ConcurrentModificationError):
        session.save(fixture_snapshot())
    target.write_bytes(original)
    before = target.read_bytes()
    monkeypatch.setattr(api.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("simulated")))
    with pytest.raises(OSError):
        session.save(fixture_snapshot())
    assert target.read_bytes() == before
    session.close()


def test_post_replace_directory_fsync_failure_updates_session(tmp_path, monkeypatch):
    """Simula falha de durabilidade após replace e verifica o estado visível da sessão."""
    import caderno.vault.api as api

    monkeypatch.setattr(api, "new_key", lambda password: (b"s" * 16, b"k" * 32))
    monkeypatch.setattr(api, "encrypt_file", lambda output, snapshot, salt, key: output.write(key[:4]))
    target = tmp_path / "durability.cpv"
    session = api.create_vault(target, "password", fixture_snapshot())
    original_snapshot = session.snapshot
    monkeypatch.setattr(api, "new_key", lambda password: (b"t" * 16, b"n" * 32))
    monkeypatch.setattr(api, "_sync_parent", lambda path: (_ for _ in ()).throw(
        api.DurabilityUncertainError("simulated directory fsync failure")
    ))
    with pytest.raises(api.DurabilityUncertainError):
        session.change_password("new password")
    assert target.read_bytes() == b"nnnn"
    assert session.snapshot == original_snapshot
    assert session._key == b"n" * 32
    assert session._fingerprint == api._fingerprint(target)
    session.close()


def test_crypto_backend_roundtrip_and_authentication(tmp_path):
    """Usa PyNaCl real para criar/abrir um cofre e rejeitar senha incorreta."""
    from caderno.vault.api import create_vault, open_vault
    from caderno.vault.model import AuthenticationError

    target = tmp_path / "fixture.cpv"
    original = fixture_snapshot()
    session = create_vault(target, "senha de teste", original)
    assert open_vault(target, "senha de teste").snapshot.document == original.document
    with pytest.raises(FileExistsError):
        create_vault(target, "outra", original)
    with pytest.raises(AuthenticationError):
        open_vault(target, "senha errada")
    session.close()


def test_crypto_backend_roundtrips_volume_fixture_and_images(tmp_path):
    """Usa PyNaCl real para cifrar e reabrir as notas longas e as imagens da fixture."""
    from caderno.vault.api import create_vault, open_vault

    original = volume_snapshot()
    target = tmp_path / "volume.cpv"
    session = create_vault(target, "senha de teste", original)
    encrypted = target.read_bytes()
    for entry in original.document["entries"]:
        assert entry["title"].encode("utf-8") not in encrypted
        assert entry["body_markdown"].encode("utf-8") not in encrypted
    for attachment in original.attachments:
        assert attachment.name.encode("utf-8") not in encrypted
        assert attachment.data and attachment.data[:32] not in encrypted
    reopened = open_vault(target, "senha de teste")
    assert reopened.snapshot.document == original.document
    assert reopened.snapshot.attachments == original.attachments
    reopened.close()
    session.close()


def test_crypto_backend_roundtrips_one_million_words(tmp_path):
    """Cifra e reabre um milhão de palavras e as imagens de teste sem gravar fixture gigante."""
    from caderno.vault.api import create_vault, open_vault

    original = million_word_snapshot()
    assert sum(len(entry["body_markdown"].split()) for entry in original.document["entries"]) == 1_000_000
    target = tmp_path / "million-words.cpv"
    session = create_vault(target, "senha de teste", original)
    encrypted = target.read_bytes()
    for entry in original.document["entries"][::40]:
        assert entry["title"].encode("utf-8") not in encrypted
        assert entry["body_markdown"].encode("utf-8") not in encrypted
    reopened = open_vault(target, "senha de teste")
    assert reopened.snapshot.document == original.document
    assert reopened.snapshot.attachments == original.attachments
    reopened.close()
    session.close()
