"""Smoke test do backend CPV1 carregado por um executável PyInstaller."""

from pathlib import Path
from tempfile import TemporaryDirectory

from caderno.vault import VaultSnapshot, create_vault, open_vault
from caderno.vault.model import AuthenticationError

OLD_PASSWORD = "synthetic-package-smoke-password"
NEW_PASSWORD = "synthetic-package-smoke-new-password"


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
        session = create_vault(path, OLD_PASSWORD, _snapshot("Criada"))
        session.close()
        session = open_vault(path, OLD_PASSWORD)
        assert session.snapshot.document["entries"][0]["title"] == "Criada"
        session.save(_snapshot("Editada"))
        session.change_password(NEW_PASSWORD)
        session.close()
        try:
            open_vault(path, OLD_PASSWORD)
        except AuthenticationError:
            pass
        else:
            raise AssertionError("A senha anterior ainda abriu o cofre")
        try:
            open_vault(path, "synthetic-package-wrong-password")
        except AuthenticationError:
            pass
        else:
            raise AssertionError("Uma senha incorreta abriu o cofre")
        session = open_vault(path, NEW_PASSWORD)
        assert session.snapshot.document["entries"][0]["title"] == "Editada"
        session.close()
    print("Roundtrip CPV1, senha incorreta e troca de senha no runtime empacotado passaram.")


if __name__ == "__main__":
    main()
