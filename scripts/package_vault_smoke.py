"""Smoke test do backend CPV1 carregado por um executável PyInstaller."""

from pathlib import Path
from tempfile import TemporaryDirectory

from caderno.vault import VaultSnapshot, create_vault, open_vault


def _snapshot(title: str) -> VaultSnapshot:
    """Cria snapshot determinístico, sem conteúdo de usuário, para o smoke test."""
    return VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-synthetic", "name": "Geral"}],
        "attachments": [],
        "entries": [{
            "id": "entry-synthetic", "title": title, "body_markdown": "Texto sintético.",
            "collection_id": "collection-synthetic", "tags": [],
            "created_at": "2026-10-28T00:00:00Z", "updated_at": "2026-10-28T00:00:00Z",
            "published_at": None, "favorite": False, "attachments": [],
        }],
    })


def main() -> None:
    """Cria, abre, edita, salva e reabre um cofre temporário com o backend empacotado."""
    with TemporaryDirectory(prefix="caderno-package-smoke-", dir="/private/tmp") as directory:
        path = Path(directory) / "synthetic.cpv"
        session = create_vault(path, "synthetic-package-smoke-password", _snapshot("Criada"))
        session.close()
        session = open_vault(path, "synthetic-package-smoke-password")
        assert session.snapshot.document["entries"][0]["title"] == "Criada"
        session.save(_snapshot("Editada"))
        session.close()
        session = open_vault(path, "synthetic-package-smoke-password")
        assert session.snapshot.document["entries"][0]["title"] == "Editada"
        session.close()
    print("Roundtrip CPV1 no runtime empacotado passou.")


if __name__ == "__main__":
    main()
