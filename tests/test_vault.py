import json
import io
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
    document = json.loads((ROOT / "fixtures/cofre_exemplo.json").read_text())
    image = (ROOT / "fixtures/pixel.png").read_bytes()
    attachment = VaultAttachment("fixture-image-1", "pixel.png", "image/png", image)
    return VaultSnapshot(document, [attachment])


def plaintext(snapshot):
    return b"".join(_records(snapshot))


def test_snapshot_is_immutable_from_callers():
    document = {"items": [{"text": "original"}]}
    snapshot = VaultSnapshot(document)
    document["items"][0]["text"] = "changed"
    returned = snapshot.document
    returned["items"].clear()
    assert snapshot.document == {"items": [{"text": "original"}]}


def test_fixture_roundtrips_manifest_and_binary_attachment():
    original = fixture_snapshot()
    restored = _parse_plaintext(plaintext(original))
    assert restored.document == original.document
    assert restored.attachments == original.attachments
    assert restored.attachments[0].data.startswith(b"\x89PNG\r\n\x1a\n")


def test_manifest_and_record_attachment_ids_must_match():
    snapshot = fixture_snapshot()
    content = bytearray(plaintext(snapshot))
    manifest_size = struct.unpack_from(">I", content, 1)[0]
    marker = content.find(b"fixture-image-1", 5 + manifest_size)
    content[marker:marker + len("fixture-image-1")] = b"fixture-image-2"
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(bytes(content))


def test_rejects_unbounded_manifest_before_parsing():
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(b"\x01" + struct.pack(">I", 0xFFFFFFFF))


def test_manifest_is_json_and_contains_binary_size_only():
    raw = _manifest(fixture_snapshot())
    manifest = json.loads(raw)
    assert manifest["attachments"][0]["size"] == len(fixture_snapshot().attachments[0].data)
    assert "iVBOR" not in raw.decode()


def test_schema_version_is_required():
    raw = json.dumps({"document": {}, "attachments": []}).encode()
    with pytest.raises(InvalidVaultError):
        _parse_plaintext(b"\x01" + struct.pack(">I", len(raw)) + raw)


def test_rejects_truncated_frame_and_bad_header_without_crypto_backend():
    with pytest.raises(AuthenticationError):
        _read_cipher_frame(io.BytesIO(b"\x00\x00\x00\x20short"), 9)
    bad = HEADER.pack(b"BADMAGIC", 1, 1, 1, 0, 3, 268435456, b"s" * 16, b"h" * 24)
    with pytest.raises(InvalidVaultError):
        _read_header(io.BytesIO(bad))


def test_short_file_is_rejected_before_kdf_or_backend_import(tmp_path):
    from caderno.vault.codec import decrypt_file

    target = tmp_path / "header-only.cpv"
    target.write_bytes(HEADER.pack(b"CPVAULT\0", 1, 1, 1, 0, 3, 268435456, b"s" * 16, b"h" * 24))
    with pytest.raises(InvalidVaultError):
        decrypt_file(str(target), "password")


def test_final_tag_must_be_empty_and_trailing_bytes_are_rejected():
    assert _is_final_frame(b"", 2, 0, 2)
    with pytest.raises(AuthenticationError):
        _is_final_frame(b"x", 2, 0, 2)
    with pytest.raises(AuthenticationError):
        _is_final_frame(b"", 3, 0, 2)
    with pytest.raises(AuthenticationError):
        _require_eof(io.BytesIO(b"extra"))


def test_create_no_overwrite_stale_session_and_failed_replace(tmp_path, monkeypatch):
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
    pytest.importorskip("nacl")
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
