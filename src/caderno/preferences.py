"""Preferências locais que não contêm dados do cofre nem credenciais."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path


def _preferences_file() -> Path:
    """Retorna preferências macOS, aceitando pasta isolada para testes manuais."""
    override = os.environ.get("CADERNO_CONFIG_DIR")
    if override:
        return Path(override).expanduser() / "preferences.json"
    return Path.home() / "Library" / "Application Support" / "Caderno de Pensamentos" / "preferences.json"


def load_last_vault() -> Path | None:
    """Lê somente o caminho salvo; ignora preferências ausentes ou inválidas."""
    target = _preferences_file()
    try:
        if target.is_symlink() or not target.is_file():
            return None
        if target.stat().st_mode & 0o077:
            return None
        value = json.loads(target.read_text(encoding="utf-8"))
        path = value.get("last_vault") if isinstance(value, dict) else None
        return Path(path).expanduser() if isinstance(path, str) and path else None
    except (OSError, ValueError, TypeError):
        return None


def save_last_vault(path: Path) -> None:
    """Grava atomicamente apenas o caminho, com permissões locais restritas."""
    target = _preferences_file()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if target.parent.is_symlink():
        raise OSError("Diretório de preferências inválido")
    os.chmod(target.parent, 0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=".preferences-", dir=target.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            descriptor = -1
            json.dump({"last_vault": str(path)}, output, ensure_ascii=False)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, target)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)
