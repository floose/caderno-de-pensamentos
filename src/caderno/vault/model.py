"""Immutable in-memory snapshot model for vault contents."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class VaultAttachment:
    id: str
    name: str
    media_type: str
    data: bytes


@dataclass(frozen=True, slots=True, init=False)
class VaultSnapshot:
    _document_json: str
    attachments: tuple[VaultAttachment, ...]

    def __init__(self, document: Mapping[str, Any], attachments=()):
        frozen_attachments = tuple(
            VaultAttachment(str(a.id), str(a.name), str(a.media_type), bytes(a.data))
            for a in attachments
        )
        doc_copy = copy.deepcopy(dict(document))
        json.dumps(doc_copy, ensure_ascii=False, allow_nan=False)
        ids = [a.id for a in frozen_attachments]
        if len(set(ids)) != len(ids):
            raise ValueError("IDs de anexo duplicados")
        object.__setattr__(self, "_document_json", json.dumps(doc_copy, ensure_ascii=False))
        object.__setattr__(self, "attachments", frozen_attachments)

    @property
    def document(self) -> dict[str, Any]:
        return json.loads(self._document_json)


class VaultError(Exception):
    """Base exception for vault operations."""


class InvalidVaultError(VaultError):
    pass


class AuthenticationError(VaultError):
    pass


class ConcurrentModificationError(VaultError):
    pass


class DurabilityUncertainError(VaultError):
    pass
