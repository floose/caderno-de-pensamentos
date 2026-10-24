"""Small filesystem facade around CPV1 encrypted snapshots."""

from __future__ import annotations

import fcntl
import hashlib
import os
import stat
import tempfile
from pathlib import Path

from .codec import decrypt_file, encrypt_file, new_key
from .model import ConcurrentModificationError, DurabilityUncertainError, VaultSnapshot


def _canonical(path) -> Path:
    target = Path(path).expanduser().absolute()
    cursor = target
    while cursor != cursor.parent:
        if cursor.is_symlink():
            raise ValueError("Caminhos com symlink não são suportados")
        cursor = cursor.parent
    parent_stat = target.parent.stat()
    if not stat.S_ISDIR(parent_stat.st_mode):
        raise ValueError("O diretório do cofre precisa ser uma pasta")
    if parent_stat.st_mode & 0o022 and not parent_stat.st_mode & stat.S_ISVTX:
        raise ValueError("Diretórios graváveis por terceiros não são suportados")
    if target.exists() and target.stat().st_uid != os.getuid() and parent_stat.st_mode & stat.S_ISVTX:
        raise ValueError("Cofres de outro usuário não são suportados")
    return target.resolve(strict=False)


def _fingerprint(path: Path) -> bytes:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.digest()


def _lock(path: Path):
    lock_dir = Path(tempfile.gettempdir()) / f"caderno-vault-locks-{os.getuid()}"
    try:
        lock_dir.mkdir(mode=0o700)
    except FileExistsError:
        pass
    info = lock_dir.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise PermissionError("Diretório privado de locks inseguro")
    dir_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    directory_fd = os.open(lock_dir, dir_flags)
    key = hashlib.sha256(os.fsencode(path)).hexdigest()
    try:
        descriptor = os.open(key, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600,
                             dir_fd=directory_fd)
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return descriptor
    finally:
        os.close(directory_fd)


def _write_atomic(path: Path, snapshot: VaultSnapshot, salt: bytes, key: bytes, create: bool):
    if create and path.exists():
        raise FileExistsError(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".cpvault-", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as output:
            descriptor = -1
            encrypt_file(output, snapshot, salt, key)
        if create:
            os.link(temporary, path, follow_symlinks=False)
            os.unlink(temporary)
        else:
            os.replace(temporary, path)
        _sync_parent(path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)


def _sync_parent(path: Path):
    descriptor = -1
    try:
        descriptor = os.open(path.parent, os.O_RDONLY)
        os.fsync(descriptor)
    except OSError as exc:
        raise DurabilityUncertainError("Arquivo substituído; durabilidade após falha de energia incerta") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


class VaultSession:
    def __init__(self, path: Path, salt: bytes, key: bytes, snapshot: VaultSnapshot, fingerprint=None):
        self._path = path
        self._salt = salt
        self._key = key
        self._snapshot = snapshot
        self._fingerprint = fingerprint if fingerprint is not None else _fingerprint(path)
        self._closed = False

    def _ensure_open(self):
        if self._closed:
            raise RuntimeError("Sessão fechada")

    @property
    def snapshot(self) -> VaultSnapshot:
        self._ensure_open()
        return self._snapshot

    def save(self, snapshot: VaultSnapshot) -> None:
        self._store(snapshot, self._salt, self._key)

    def change_password(self, new_password: str) -> None:
        salt, key = new_key(new_password)
        self._store(self._snapshot, salt, key)

    def _store(self, snapshot: VaultSnapshot, salt: bytes, key: bytes):
        self._ensure_open()
        descriptor = _lock(self._path)
        try:
            if _fingerprint(self._path) != self._fingerprint:
                raise ConcurrentModificationError("O cofre foi alterado por outra sessão")
            _write_atomic(self._path, snapshot, salt, key, create=False)
            self._snapshot = snapshot
            self._salt = salt
            self._key = key
            self._fingerprint = _fingerprint(self._path)
        except DurabilityUncertainError:
            self._snapshot = snapshot
            self._salt = salt
            self._key = key
            self._fingerprint = _fingerprint(self._path)
            raise
        finally:
            os.close(descriptor)

    def close(self):
        self._salt = None
        self._key = None
        self._snapshot = None
        self._closed = True


def create_vault(path, password: str, snapshot: VaultSnapshot) -> VaultSession:
    target = _canonical(path)
    if not target.parent.is_dir():
        raise FileNotFoundError(target.parent)
    if target.exists():
        raise FileExistsError(target)
    descriptor = _lock(target)
    try:
        salt, key = new_key(password)
        _write_atomic(target, snapshot, salt, key, create=True)
        fingerprint = _fingerprint(target)
        return VaultSession(target, salt, key, snapshot, fingerprint)
    finally:
        os.close(descriptor)


def open_vault(path, password: str) -> VaultSession:
    target = _canonical(path)
    descriptor = _lock(target)
    try:
        snapshot, key, salt = decrypt_file(str(target), password)
        fingerprint = _fingerprint(target)
        return VaultSession(target, salt, key, snapshot, fingerprint)
    finally:
        os.close(descriptor)
