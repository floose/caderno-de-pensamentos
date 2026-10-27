"""Immutable in-memory snapshot model for vault contents."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class VaultAttachment:
    """Anexo imutável armazenado em bytes e associado por ID ao documento."""
    id: str
    name: str
    media_type: str
    data: bytes


@dataclass(frozen=True, slots=True, init=False)
class VaultSnapshot:
    """Cópia imutável do documento JSON e dos anexos de uma revisão do cofre."""
    _document_json: str
    attachments: tuple[VaultAttachment, ...]

    def __init__(self, document: Mapping[str, Any], attachments=()):
        """Copia entradas mutáveis e valida que o documento pode ser serializado em JSON."""
        frozen_attachments = tuple(_freeze_attachment(item) for item in attachments)
        doc_copy = copy.deepcopy(dict(document))
        json.dumps(doc_copy, ensure_ascii=False, allow_nan=False)
        ids = [a.id for a in frozen_attachments]
        if len(set(ids)) != len(ids):
            raise ValueError("IDs de anexo duplicados")
        object.__setattr__(self, "_document_json", json.dumps(doc_copy, ensure_ascii=False))
        object.__setattr__(self, "attachments", frozen_attachments)

    @property
    def document(self) -> dict[str, Any]:
        """Devolve uma cópia nova para impedir mutação do estado interno."""
        return json.loads(self._document_json)


def _freeze_attachment(item) -> VaultAttachment:
    if not isinstance(item, VaultAttachment):
        raise TypeError("Anexos precisam ser VaultAttachment")
    if not all(isinstance(value, str) for value in (item.id, item.name, item.media_type)):
        raise TypeError("ID, nome e MIME type do anexo precisam ser textos")
    if not isinstance(item.data, (bytes, bytearray, memoryview)):
        raise TypeError("Dados do anexo precisam ser bytes ou bytes-like")
    return VaultAttachment(item.id, item.name, item.media_type, bytes(item.data))

class VaultError(Exception):
    """Base exception for vault operations."""


class InvalidVaultError(VaultError):
    """O arquivo ou seu conteúdo não corresponde a uma estrutura CPV1 válida."""
    pass


class AuthenticationError(VaultError):
    """Senha incorreta ou dados autenticados ausentes, alterados ou malformados."""
    pass


class ConcurrentModificationError(VaultError):
    """O arquivo mudou desde a abertura e não pode ser sobrescrito por esta sessão."""
    pass


class DurabilityUncertainError(VaultError):
    """A substituição ocorreu, mas a persistência da entrada de diretório é incerta."""
    pass
