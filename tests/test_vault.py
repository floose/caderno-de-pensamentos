import json
import io
import copy
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


@pytest.mark.parametrize(
    "attachment",
    [
        VaultAttachment(7, "image.png", "image/png", b"x"),
        VaultAttachment("id", None, "image/png", b"x"),
        VaultAttachment("id", "image.png", 7, b"x"),
        VaultAttachment("id", "image.png", "image/png", [120]),
    ],
)
def test_snapshot_rejects_coerced_or_non_bytes_attachment_fields(attachment):
    """Não converte tipos inválidos de metadados ou dados de anexo silenciosamente."""
    with pytest.raises(TypeError):
        VaultSnapshot({}, [attachment])


def test_snapshot_copies_mutable_bytes_like_data():
    source = bytearray(b"image")
    snapshot = VaultSnapshot({}, [VaultAttachment("id", "image.png", "image/png", source)])
    source[0] = ord("X")
    assert snapshot.attachments[0].data == b"image"


def test_schema_complexity_rejects_wide_list_before_queue_expansion():
    from caderno.vault.schema import _check_complexity

    with pytest.raises(InvalidVaultError):
        _check_complexity({"wide": [None] * 100_001})


def test_fixture_roundtrips_manifest_and_binary_attachment():
    """Testa serialização e leitura de texto/anexo, sem executar a cifra."""
    original = fixture_snapshot()
    restored = _parse_plaintext(plaintext(original))
    assert restored.document == original.document
    assert restored.attachments == original.attachments
    assert restored.attachments[0].data.startswith(b"\x89PNG\r\n\x1a\n")


def test_schema_v1_accepts_both_synthetic_fixtures():
    """Confirma compatibilidade do contrato v1 com fixtures curta e de volume."""
    assert _manifest(fixture_snapshot())
    assert _manifest(volume_snapshot())


@pytest.mark.parametrize(
    "mutate",
    [
        lambda doc: doc["entries"][0].pop("title"),
        lambda doc: doc["entries"][0].__setitem__("favorite", "false"),
        lambda doc: doc["entries"][0].__setitem__("collection_id", "missing-collection"),
        lambda doc: doc["entries"][0].__setitem__("created_at", "2026-10-24T09:00:00"),
        lambda doc: doc["entries"][0].__setitem__("id", doc["collections"][0]["id"]),
        lambda doc: doc["attachments"][0].__setitem__("media_type", "text/plain"),
        lambda doc: doc["attachments"][0].__setitem__("filename", "../pixel.png"),
        lambda doc: doc["attachments"][0].__setitem__("filename", "."),
        lambda doc: doc["attachments"][0].__setitem__("filename", ".."),
        lambda doc: doc["entries"][0]["attachments"].append("missing-attachment"),
        lambda doc: doc.__setitem__("schema_version", 2),
    ],
)
def test_schema_v1_rejects_invalid_fields_types_ids_and_references(mutate):
    """Rejeita campos ausentes, tipos errados, IDs repetidos e referências quebradas."""
    snapshot = fixture_snapshot()
    document = copy.deepcopy(snapshot.document)
    mutate(document)
    with pytest.raises(InvalidVaultError):
        _manifest(VaultSnapshot(document, snapshot.attachments))


def test_schema_v1_allows_unpublished_entry_and_rejects_metadata_mismatch():
    """Aceita rascunho sem publicação e exige metadados binários idênticos."""
    snapshot = fixture_snapshot()
    draft = copy.deepcopy(snapshot.document)
    draft["entries"][0]["published_at"] = None
    assert _manifest(VaultSnapshot(draft, snapshot.attachments))
    draft["attachments"][0]["filename"] = "other.png"
    with pytest.raises(InvalidVaultError):
        _manifest(VaultSnapshot(draft, snapshot.attachments))


def test_reader_rejects_invalid_schema_before_returning_snapshot():
    """O parser CPV1 não devolve snapshot se um documento autenticado viola schema v1."""
    document = volume_snapshot().document
    document["entries"][0]["favorite"] = 1
    raw_manifest = json.dumps({"document": document, "attachments": []}, separators=(",", ":")).encode()
    raw = b"\x01" + struct.pack(">I", len(raw_manifest)) + raw_manifest
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(raw)


def test_reader_rejects_duplicate_json_keys():
    """Não deixa o parser escolher silenciosamente o último valor de uma chave repetida."""
    document = volume_snapshot().document
    inner = json.dumps({"document": document, "attachments": []}, separators=(",", ":"))
    inner = inner.replace('"schema_version":1', '"schema_version":1,"schema_version":1', 1)
    raw_manifest = inner.encode()
    raw = b"\x01" + struct.pack(">I", len(raw_manifest)) + raw_manifest
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(raw)


def test_schema_and_snapshot_reject_per_attachment_and_aggregate_limits(monkeypatch):
    """Verifica limites de anexos sem alocar imagens grandes de teste."""
    import caderno.vault.codec as codec

    original = fixture_snapshot()
    monkeypatch.setattr(codec, "MAX_ATTACHMENT", len(original.attachments[0].data) - 1)
    with pytest.raises(ValueError):
        _manifest(original)

    monkeypatch.setattr(codec, "MAX_ATTACHMENT", 100)
    monkeypatch.setattr(codec, "MAX_AGGREGATE", 100)
    document = original.document
    document["entries"][0]["attachments"].append("fixture-image-2")
    document["attachments"].append({
        "id": "fixture-image-2", "entry_id": "fixture-entry-1",
        "filename": "pixel-2.png", "media_type": "image/png",
    })
    second = VaultAttachment("fixture-image-2", "pixel-2.png", "image/png", b"x" * 40)
    with pytest.raises(ValueError):
        _manifest(VaultSnapshot(document, (*original.attachments, second)))


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


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [("kdf", 2), ("stream", 2), ("flags", 1), ("opslimit", 4), ("memlimit", 64 * 1024 * 1024)],
)
def test_header_profile_rejected_before_argon2_kdf(tmp_path, monkeypatch, field, invalid_value):
    """Prova por spy que qualquer perfil CPV1 desconhecido é recusado antes de Argon2id."""
    import caderno.vault.codec as codec

    target = tmp_path / f"invalid-{field}.cpv"
    header = list(HEADER.unpack(HEADER.pack(b"CPVAULT\0", 1, 1, 1, 0, 3, 268435456, b"s" * 16, b"h" * 24)))
    index = {"kdf": 2, "stream": 3, "flags": 4, "opslimit": 5, "memlimit": 6}[field]
    header[index] = invalid_value
    target.write_bytes(HEADER.pack(*header) + struct.pack(">I", 17) + b"x" * 17)
    calls = []
    monkeypatch.setattr(codec, "_derive", lambda *args: calls.append(args))
    with pytest.raises(InvalidVaultError):
        codec.decrypt_file(str(target), "password")
    assert calls == []


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
    assert target.stat().st_mode & 0o777 == 0o600
    assert open_vault(target, "senha de teste").snapshot.document == original.document
    with pytest.raises(FileExistsError):
        create_vault(target, "outra", original)
    with pytest.raises(AuthenticationError):
        open_vault(target, "senha errada")
    session.close()


def test_crypto_backend_rejects_tampered_stream_without_publishing_snapshot(tmp_path, monkeypatch):
    """Rejeita mutações reais do envelope sem construir uma sessão parcial."""
    from caderno.vault import api

    original = fixture_snapshot()
    source = tmp_path / "original.cpv"
    session = api.create_vault(source, "senha de teste", original)
    session.close()
    encrypted = source.read_bytes()
    final_start = HEADER.size
    while True:
        frame_size = struct.unpack_from(">I", encrypted, final_start)[0]
        next_frame = final_start + 4 + frame_size
        if next_frame == len(encrypted):
            break
        final_start = next_frame
    mutations = [
        ("salt.cpv", encrypted[:25] + bytes([encrypted[25] ^ 1]) + encrypted[26:], AuthenticationError),
        ("cipher.cpv", encrypted[:HEADER.size + 4] + bytes([encrypted[HEADER.size + 4] ^ 1]) + encrypted[HEADER.size + 5:], AuthenticationError),
        ("truncated.cpv", encrypted[:-1], AuthenticationError),
        ("no-final.cpv", encrypted[:final_start], AuthenticationError),
        ("trailing.cpv", encrypted + b"x", AuthenticationError),
        ("unknown-kdf.cpv", encrypted[:10] + b"\x02" + encrypted[11:], InvalidVaultError),
    ]
    published = []
    monkeypatch.setattr(api, "VaultSession", lambda *args, **kwargs: published.append(args))
    for name, altered, expected_error in mutations:
        target = tmp_path / name
        target.write_bytes(altered)
        with pytest.raises(expected_error):
            api.open_vault(target, "senha de teste")
        assert published == []


def test_crypto_backend_saves_changes_and_reopens_file(tmp_path):
    """Persiste texto alterado e preserva imagem e metadados após fechar a sessão."""
    from caderno.vault.api import create_vault, open_vault

    original = fixture_snapshot()
    target = tmp_path / "saved.cpv"
    session = create_vault(target, "senha de teste", original)

    updated_document = original.document
    updated_document["entries"][0]["body_markdown"] += " Alteração persistida na revisão dois."
    updated_document["attachments"][0]["filename"] = "pixel-atualizado.png"
    original_image = original.attachments[0]
    updated_image = VaultAttachment(
        original_image.id,
        "pixel-atualizado.png",
        original_image.media_type,
        original_image.data,
    )
    updated = VaultSnapshot(updated_document, [updated_image])

    session.save(updated)
    assert session.snapshot == updated
    session.close()

    reopened = open_vault(target, "senha de teste")
    assert reopened.snapshot.document == updated.document
    assert reopened.snapshot.attachments == updated.attachments
    reopened.close()


def test_crypto_backend_changes_password_and_preserves_snapshot(tmp_path):
    """Troca a senha real, rejeita a antiga e conserva textos e bytes dos anexos."""
    from caderno.vault.api import create_vault, open_vault

    original = fixture_snapshot()
    target = tmp_path / "password-change.cpv"
    session = create_vault(target, "senha antiga", original)
    session.change_password("senha nova")
    session.close()

    with pytest.raises(AuthenticationError):
        open_vault(target, "senha antiga")
    reopened = open_vault(target, "senha nova")
    assert reopened.snapshot.document == original.document
    assert reopened.snapshot.attachments == original.attachments
    reopened.close()


def test_crypto_backend_replace_failure_preserves_original_and_cleans_temp(tmp_path, monkeypatch):
    """Falha pré-replace preserva o arquivo/snapshot anterior e remove temporário cifrado."""
    import caderno.vault.api as api

    original = fixture_snapshot()
    target = tmp_path / "replace-failure.cpv"
    session = api.create_vault(target, "senha de teste", original)
    original_bytes = target.read_bytes()
    changed_document = original.document
    changed_document["entries"][0]["body_markdown"] += " alteração que não deve persistir"
    changed = VaultSnapshot(changed_document, original.attachments)
    monkeypatch.setattr(api.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("replace simulado")))

    with pytest.raises(OSError, match="replace simulado"):
        session.save(changed)

    assert target.read_bytes() == original_bytes
    assert session.snapshot.document == original.document
    assert session.snapshot.attachments == original.attachments
    reopened = api.open_vault(target, "senha de teste")
    assert reopened.snapshot.document == original.document
    assert reopened.snapshot.attachments == original.attachments
    assert list(tmp_path.glob(".cpvault-*")) == []
    reopened.close()
    monkeypatch.undo()
    session.save(changed)
    assert session.snapshot == changed
    assert session._fingerprint == api._fingerprint(target)
    saved = api.open_vault(target, "senha de teste")
    assert saved.snapshot.document == changed.document
    assert saved.snapshot.attachments == changed.attachments
    assert list(tmp_path.glob(".cpvault-*")) == []
    saved.close()
    session.close()


def test_real_save_tempfile_excludes_selected_plaintext_markers(tmp_path, monkeypatch):
    """Busca marcadores sintéticos selecionados antes de delegar ao replace real."""
    import caderno.vault.api as api

    original = fixture_snapshot()
    target = tmp_path / "encrypted-temp.cpv"
    session = api.create_vault(target, "senha de teste", original)
    observed = []
    real_replace = api.os.replace

    def inspect_then_replace(source, destination, *args, **kwargs):
        data = Path(source).read_bytes()
        observed.append(data)
        return real_replace(source, destination, *args, **kwargs)

    monkeypatch.setattr(api.os, "replace", inspect_then_replace)
    changed_doc = original.document
    changed_doc["entries"][0]["body_markdown"] += " marker-plaintext-temporary"
    session.save(VaultSnapshot(changed_doc, original.attachments))

    assert len(observed) == 1
    encrypted_temp = observed[0]
    plaintext_markers = [
        b"senha de teste",
        session._key,
        original.document["entries"][0]["title"].encode(),
        changed_doc["entries"][0]["body_markdown"].encode(),
        original.attachments[0].name.encode(),
        original.attachments[0].data[:32],
    ]
    assert all(marker not in encrypted_temp for marker in plaintext_markers)
    assert target.read_bytes() == encrypted_temp
    assert list(tmp_path.glob(".cpvault-*")) == []
    session.close()


def test_closed_session_rejects_operations_before_kdf(tmp_path, monkeypatch):
    """Sessão fechada rejeita leitura/escrita sem derivar chave de senha nova."""
    import caderno.vault.api as api

    session = api.create_vault(tmp_path / "closed.cpv", "senha de teste", fixture_snapshot())
    session.close()
    kdf_calls = []
    monkeypatch.setattr(api, "new_key", lambda password: kdf_calls.append(password))
    with pytest.raises(RuntimeError):
        _ = session.snapshot
    with pytest.raises(RuntimeError):
        session.save(fixture_snapshot())
    with pytest.raises(RuntimeError):
        session.change_password("não derivar")
    assert kdf_calls == []


def test_two_real_sessions_reject_stale_save_without_overwriting(tmp_path):
    """Duas sessões reais não permitem que uma revisão obsoleta sobrescreva a nova."""
    from caderno.vault.api import ConcurrentModificationError, create_vault, open_vault

    original = fixture_snapshot()
    target = tmp_path / "two-sessions.cpv"
    creator = create_vault(target, "senha de teste", original)
    first = open_vault(target, "senha de teste")
    stale = open_vault(target, "senha de teste")
    creator.close()
    newer_document = first.snapshot.document
    newer_document["entries"][0]["body_markdown"] += " revisão mais recente"
    newer = VaultSnapshot(newer_document, first.snapshot.attachments)
    first.save(newer)
    saved_bytes = target.read_bytes()
    stale_document = stale.snapshot.document
    stale_document["entries"][1]["body_markdown"] += " alteração obsoleta"
    with pytest.raises(ConcurrentModificationError):
        stale.save(VaultSnapshot(stale_document, stale.snapshot.attachments))
    assert target.read_bytes() == saved_bytes
    assert stale.snapshot == original
    reopened = open_vault(target, "senha de teste")
    assert reopened.snapshot == newer
    reopened.close()
    first.close()
    stale.close()


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
