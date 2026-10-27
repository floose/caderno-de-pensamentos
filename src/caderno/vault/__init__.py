"""Offline encrypted vault API (CPV1)."""

from .api import VaultSession, create_vault, open_vault
from .model import DurabilityUncertainError, VaultAttachment, VaultSnapshot

__all__ = [
    "DurabilityUncertainError", "VaultAttachment", "VaultSession", "VaultSnapshot",
    "create_vault", "open_vault",
]
