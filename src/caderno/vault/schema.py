"""Strict schema v1 checks for the synthetic journal document format."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Iterable

from .model import InvalidVaultError, VaultAttachment

ROOT_KEYS = {"schema_version", "collections", "attachments", "entries"}
COLLECTION_KEYS = {"id", "name"}
ENTRY_KEYS = {
    "id", "title", "body_markdown", "collection_id", "tags", "created_at",
    "updated_at", "published_at", "favorite", "attachments",
}
ATTACHMENT_KEYS = {"id", "entry_id", "filename", "media_type"}
MIME_PATTERN = re.compile(r"^image/[A-Za-z0-9.+-]+$")


def _invalid(message: str):
    raise InvalidVaultError(f"Schema v1 inválido: {message}")


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    """JSON hook that rejects duplicate object keys instead of keeping the last value."""
    result = {}
    for key, value in pairs:
        if key in result:
            _invalid("chave JSON duplicada")
        result[key] = value
    return result


def _check_complexity(document: dict):
    pending = [(document, 0)]
    discovered = 1
    while pending:
        value, depth = pending.pop()
        if depth > 64:
            _invalid("estrutura excede limite de valores/profundidade")
        if isinstance(value, dict):
            children = len(value)
            _check_queue_size(discovered, children)
            discovered += children
            pending.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            children = len(value)
            _check_queue_size(discovered, children)
            discovered += children
            pending.extend((item, depth + 1) for item in value)


def _check_queue_size(discovered: int, children: int):
    if discovered + children > 100_000:
        _invalid("estrutura excede limite de valores")


def _string(value, label: str, nonempty=True, max_length=4096) -> str:
    if not isinstance(value, str) or (nonempty and not value.strip()) or len(value) > max_length:
        _invalid(f"campo de texto inválido: {label}")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        _invalid(f"texto não é UTF-8 válido: {label}")
    return value


def _identifier(value, label: str) -> str:
    ident = _string(value, label, max_length=256)
    if any(ord(char) < 32 for char in ident):
        _invalid(f"identificador inválido: {label}")
    return ident


def _utc_datetime(value, label: str, nullable=False):
    if value is None and nullable:
        return
    if not isinstance(value, str):
        _invalid(f"data/hora inválida: {label}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _invalid(f"data/hora inválida: {label}")
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        _invalid(f"data/hora precisa estar em UTC: {label}")


def _validate_collections(items: list, all_ids: set) -> set[str]:
    if not isinstance(items, list) or len(items) > 10000:
        _invalid("collections precisa ser uma lista")
    ids = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != COLLECTION_KEYS:
            _invalid("campos de coleção inválidos")
        ident = _identifier(item["id"], "collection.id")
        _string(item["name"], "collection.name")
        if ident in all_ids:
            _invalid("ID duplicado")
        ids.add(ident)
        all_ids.add(ident)
    return ids


def _validate_entries(items: list, collection_ids: set[str], all_ids: set) -> dict[str, set[str]]:
    if not isinstance(items, list) or len(items) > 100_000:
        _invalid("entries precisa ser uma lista")
    references = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != ENTRY_KEYS:
            _invalid("campos de entrada inválidos")
        ident = _identifier(item["id"], "entry.id")
        if ident in all_ids:
            _invalid("ID duplicado")
        all_ids.add(ident)
        collection_id = _identifier(item["collection_id"], "entry.collection_id")
        if collection_id not in collection_ids:
            _invalid("collection_id sem referência")
        _string(item["title"], "entry.title")
        _string(item["body_markdown"], "entry.body_markdown", nonempty=False, max_length=8 * 1024 * 1024)
        if type(item["favorite"]) is not bool:
            _invalid("favorite precisa ser booleano")
        _validate_entry_lists(item)
        _utc_datetime(item["created_at"], "created_at")
        _utc_datetime(item["updated_at"], "updated_at")
        _utc_datetime(item["published_at"], "published_at", nullable=True)
        references[ident] = set(item["attachments"])
    return references


def _validate_entry_lists(entry: dict):
    tags = entry["tags"]
    attachments = entry["attachments"]
    if not isinstance(tags, list):
        _invalid("tags precisa ser uma lista de textos não vazios")
    for tag in tags:
        _string(tag, "entry.tags", max_length=256)
    if len(tags) != len(set(tags)):
        _invalid("tags duplicadas")
    if not isinstance(attachments, list):
        _invalid("attachments precisa ser uma lista")
    for ident in attachments:
        _identifier(ident, "entry.attachments")
    if len(attachments) != len(set(attachments)):
        _invalid("referência de anexo duplicada na entrada")


def _validate_descriptors(items: list, entry_ids: set[str], all_ids: set) -> dict[str, dict]:
    if not isinstance(items, list) or len(items) > 256:
        _invalid("attachments precisa ser uma lista")
    descriptors = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != ATTACHMENT_KEYS:
            _invalid("campos de anexo inválidos")
        ident = _identifier(item["id"], "attachment.id")
        entry_id = _identifier(item["entry_id"], "attachment.entry_id")
        filename = _string(item["filename"], "attachment.filename")
        media_type = _string(item["media_type"], "attachment.media_type")
        if filename in {".", ".."} or "/" in filename or "\\" in filename or "\x00" in filename:
            _invalid("filename deve ser um nome simples")
        if not MIME_PATTERN.fullmatch(media_type):
            _invalid("media_type precisa ser image/*")
        if entry_id not in entry_ids:
            _invalid("entry_id do anexo sem referência")
        if ident in all_ids:
            _invalid("ID duplicado")
        all_ids.add(ident)
        descriptors[ident] = item
    return descriptors


def validate_document_v1(document: dict, attachments: Iterable[VaultAttachment]):
    """Validate v1 fields, unique IDs, UTC dates, references and binary metadata."""
    if not isinstance(document, dict) or set(document) != ROOT_KEYS:
        _invalid("campos de nível superior inválidos")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        _invalid("schema_version desconhecida")
    _check_complexity(document)
    all_ids = set()
    collection_ids = _validate_collections(document["collections"], all_ids)
    entry_refs = _validate_entries(document["entries"], collection_ids, all_ids)
    entry_ids = set(entry_refs)
    descriptors = _validate_descriptors(document["attachments"], entry_ids, all_ids)
    _validate_references(entry_refs, descriptors)
    _validate_binary_attachments(attachments, descriptors)


def _validate_references(entry_refs: dict[str, set[str]], descriptors: dict[str, dict]):
    descriptor_refs = {ident: item["entry_id"] for ident, item in descriptors.items()}
    if set(descriptor_refs) != {ident for refs in entry_refs.values() for ident in refs}:
        _invalid("referências de anexos não correspondem aos descritores")
    for entry_id, refs in entry_refs.items():
        if any(descriptor_refs[ident] != entry_id for ident in refs):
            _invalid("anexo atribuído à entrada errada")


def _validate_binary_attachments(attachments: Iterable[VaultAttachment], descriptors: dict[str, dict]):
    items = tuple(attachments)
    binaries = {item.id: item for item in items}
    if len(binaries) != len(items) or set(binaries) != set(descriptors):
        _invalid("anexos binários não correspondem aos descritores")
    for ident, binary in binaries.items():
        descriptor = descriptors[ident]
        if binary.name != descriptor["filename"] or binary.media_type != descriptor["media_type"]:
            _invalid("metadados binários não correspondem aos descritores")
