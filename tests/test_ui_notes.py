from pathlib import Path
from unittest.mock import Mock

from caderno import ui
from caderno.vault import (
    DurabilityUncertainError, VaultAttachment, VaultSnapshot, create_vault, open_vault,
)
from caderno.vault import api as vault_api


class FakeEntry:
    def __init__(self, value=""):
        self.value = value

    def get(self, *_args):
        return self.value

    def focus_set(self):
        pass


class FakeBody(FakeEntry):
    pass


def app_with_editor(session):
    app = ui.CadernoApp.__new__(ui.CadernoApp)
    app.root = object()
    app.session = session
    app.active_entry_id = None
    app.saved_title = ""
    app.saved_body = ""
    initial_collection = session.snapshot.document["collections"][0]["id"]
    app.collection_choice = FakeEntry(initial_collection)
    app.collection_ids_by_label = {initial_collection: initial_collection}
    app.tags_entry = FakeEntry()
    app.saved_collection_id = initial_collection
    app.saved_tags = []
    app.editor_metadata_ready = True
    app.title_entry = FakeEntry()
    app.body_editor = FakeBody()
    app.update_summary = Mock()
    app.refresh_notes = Mock()
    app.show_locked = Mock()
    app._activate = ui.CadernoApp._activate.__get__(app)

    def display_unlocked(_session):
        entry = app._active_entry()
        app.title_entry.value = entry["title"] if entry else ""
        app.body_editor.value = entry["body_markdown"] if entry else ""
        app.saved_title, app.saved_body = app.title_entry.value, app.body_editor.value

    app.show_unlocked = Mock(side_effect=display_unlocked)
    app._remember_path = Mock()
    return app


def test_note_create_edit_close_and_reopen_persist_in_real_vault(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-notes.cpv"
    image_bytes = (Path(__file__).parent / "fixtures" / "pixel.png").read_bytes()
    initial = VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-synthetic", "name": "Geral"}],
        "attachments": [{
            "id": "attachment-synthetic", "entry_id": "entry-synthetic",
            "filename": "pixel.png", "media_type": "image/png",
        }],
        "entries": [{
            "id": "entry-synthetic", "title": "Nota com anexo", "body_markdown": "Exemplo.",
            "collection_id": "collection-synthetic", "tags": [],
            "created_at": "2026-10-24T09:00:00Z", "updated_at": "2026-10-24T09:00:00Z",
            "published_at": None, "favorite": False, "attachments": ["attachment-synthetic"],
        }],
    }, (VaultAttachment(
        id="attachment-synthetic", name="pixel.png", media_type="image/png", data=image_bytes,
    ),))
    session = create_vault(path, "synthetic-password", initial)
    app = app_with_editor(session)
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())
    monkeypatch.setattr(ui.messagebox, "showwarning", Mock())

    app.title_entry.value = "Nota sintética"
    app.body_editor.value = "Primeira versão"
    app.tags_entry.value = "#ensaio, #macOS"
    assert app.save_entry()
    entry_id = app.active_entry_id

    app.title_entry.value = "Nota editada"
    app.body_editor.value = "Conteúdo atualizado"
    assert app.active_entry_id == entry_id
    unsaved_prompt = Mock(return_value="save")
    monkeypatch.setattr(ui, "ask_unsaved_changes", unsaved_prompt)
    assert app.close_vault()
    unsaved_prompt.assert_called_once_with(app.root)

    reopened = open_vault(path, "synthetic-password")
    persisted = reopened.snapshot
    entries = {entry["id"]: entry for entry in persisted.document["entries"]}
    entry = entries[entry_id]
    assert entry["id"] == entry_id
    assert entry["title"] == "Nota editada"
    assert entry["body_markdown"] == "Conteúdo atualizado"
    assert entry["tags"] == ["ensaio", "macOS"]
    assert entries["entry-synthetic"]["attachments"] == ["attachment-synthetic"]
    assert persisted.attachments[0].data == image_bytes
    reopened.close()

    monkeypatch.setenv("CADERNO_UI_TEST_PROFILE", str(tmp_path))
    errors = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", errors)
    monkeypatch.setattr(ui, "ask_password", lambda *_args: "wrong-synthetic-password")
    app.unlock(path)
    assert app.session is None
    assert "wrong-synthetic-password" not in errors.call_args.args[1]

    monkeypatch.setattr(ui, "ask_password", lambda *_args: "synthetic-password")
    app.unlock(path)
    assert app.session.snapshot.document["entries"]
    app._remember_path.assert_called_once_with(path)
    assert app.close_vault()


def test_collection_and_tags_edits_are_confirmed_and_persisted(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-organization.cpv"
    initial = VaultSnapshot({
        "schema_version": 1,
        "collections": [
            {"id": "collection-general", "name": "Geral"},
            {"id": "collection-project", "name": "Projetos"},
        ],
        "attachments": [], "entries": [],
    })
    session = create_vault(path, "synthetic-password", initial)
    app = app_with_editor(session)
    app.title_entry.value = "Nota organizada"
    app.body_editor.value = "Texto sintético"
    app.collection_choice.value = "collection-project"
    app.tags_entry.value = "#ideia, #pesquisa, #ideia"
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    assert app.save_entry()
    saved_entry = session.snapshot.document["entries"][0]
    assert saved_entry["collection_id"] == "collection-project"
    assert saved_entry["tags"] == ["ideia", "pesquisa"]
    assert not app._has_pending_changes()
    app.collection_choice.value = "collection-general"
    app.tags_entry.value = "#rascunho"
    assert app._has_pending_changes()
    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: "cancel")
    assert not app.close_vault()
    assert app.session is session

    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: "save")
    assert app.close_vault()
    reopened = open_vault(path, "synthetic-password")
    entry = reopened.snapshot.document["entries"][0]
    assert entry["collection_id"] == "collection-general"
    assert entry["tags"] == ["rascunho"]
    reopened.close()


def test_add_collection_persists_real_vault_and_rejects_duplicate_name(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-collection-test.cpv"
    session = create_vault(path, "synthetic-password", VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-general", "name": "Geral"}],
        "attachments": [], "entries": [],
    }))
    app = app_with_editor(session)
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())
    ask_name = Mock(side_effect=("Projetos", " geral "))
    monkeypatch.setattr(ui.simpledialog, "askstring", ask_name)

    assert app.add_collection()
    assert not app.add_collection()
    assert [item["name"] for item in session.snapshot.document["collections"]] == ["Geral", "Projetos"]
    app.refresh_notes.assert_called_once_with()
    session.close()


def test_tag_over_schema_limit_keeps_draft_and_skips_persistence(monkeypatch):
    snapshot = VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-synthetic", "name": "Geral"}],
        "attachments": [], "entries": [],
    })
    session = Mock(snapshot=snapshot)
    app = app_with_editor(session)
    app.title_entry.value = "Nota válida"
    app.tags_entry.value = "#" + "x" * 257
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    assert not app.save_entry()

    session.save.assert_not_called()
    assert app.tags_entry.value == "#" + "x" * 257
    showerror.assert_called_once_with(
        "Hashtag inválida", "Cada hashtag pode ter até 256 caracteres.", parent=app.root,
    )


def test_stale_ui_session_keeps_draft_without_overwriting_external_save(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-conflict.cpv"
    initial = VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-synthetic", "name": "Geral"}],
        "attachments": [],
        "entries": [],
    })
    session = create_vault(path, "synthetic-password", initial)
    external_session = open_vault(path, "synthetic-password")
    app = app_with_editor(session)
    app.title_entry.value = "Rascunho local"
    app.body_editor.value = "Não deve sobrescrever o cofre"
    external_document = external_session.snapshot.document
    external_document["entries"].append({
        "id": "entry-external", "title": "Alteração externa", "body_markdown": "Preservar",
        "collection_id": "collection-synthetic", "tags": [],
        "created_at": "2026-10-24T09:00:00Z", "updated_at": "2026-10-24T09:00:00Z",
        "published_at": None, "favorite": False, "attachments": [],
    })
    external_session.save(VaultSnapshot(external_document))
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    assert not app.save_entry()

    assert app.title_entry.value == "Rascunho local"
    assert app.body_editor.value == "Não deve sobrescrever o cofre"
    assert app.saved_title == "" and app.active_entry_id is None
    reader = open_vault(path, "synthetic-password")
    assert [entry["title"] for entry in reader.snapshot.document["entries"]] == ["Alteração externa"]
    assert "Rascunho local" not in showerror.call_args.args[1]
    reader.close()
    external_session.close()
    session.close()


def test_ui_treats_post_replace_durability_error_as_visible_save(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-durability.cpv"
    initial = VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-synthetic", "name": "Geral"}],
        "attachments": [],
        "entries": [],
    })
    session = create_vault(path, "synthetic-password", initial)
    app = app_with_editor(session)
    app.title_entry.value = "Nota visível"
    app.body_editor.value = "O novo conteúdo deve permanecer"
    monkeypatch.setattr(
        vault_api, "_sync_parent", Mock(side_effect=DurabilityUncertainError("synthetic")),
    )
    warning = Mock()
    monkeypatch.setattr(ui.messagebox, "showwarning", warning)

    assert not app.save_entry()

    assert app.saved_title == "Nota visível"
    assert not app._has_pending_changes()
    warning.assert_called_once()
    session.close()
    reader = open_vault(path, "synthetic-password")
    assert reader.snapshot.document["entries"][0]["title"] == "Nota visível"
    reader.close()
