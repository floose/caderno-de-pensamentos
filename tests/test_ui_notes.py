from pathlib import Path
from types import SimpleNamespace
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


class FakeNoteList:
    def __init__(self):
        self.items = []
        self.selection = ()

    def delete(self, *_args):
        self.items.clear()
        self.selection = ()

    def insert(self, _index, value):
        self.items.append(value)

    def selection_set(self, index):
        self.selection = (index,)

    def see(self, *_args):
        pass

    def curselection(self):
        return self.selection


def search_app():
    app = ui.CadernoApp.__new__(ui.CadernoApp)
    app.session = SimpleNamespace(snapshot=SimpleNamespace(document={
        "collections": [{"id": "collection-ideas", "name": "Ideias"}],
        "entries": [
            {
                "id": "entry-art", "title": "Aquarela", "body_markdown": "Planejar canal",
                "collection_id": "collection-ideas", "tags": ["desenho", "tela"],
                "created_at": "2026-10-28T10:00:00Z",
                "updated_at": "2026-10-30T10:00:00Z",
            },
            {
                "id": "entry-archive", "title": "Arquivo antigo", "body_markdown": "Lembranças",
                "collection_id": "collection-ideas", "tags": ["memória"],
                "created_at": "2026-10-29T10:00:00Z",
                "updated_at": "2026-10-29T10:00:00Z",
            },
        ],
    }))
    app.search_query = ""
    app.collection_filter_id = None
    app.tag_filter = None
    app.sort_mode = ui.DEFAULT_SORT_MODE
    app.active_entry_id = "entry-art"
    app.note_entry_ids = []
    app.note_list = FakeNoteList()
    app.title_entry = FakeEntry("rascunho não salvo")
    app.body_editor = FakeBody("corpo em edição")
    return app


def app_with_editor(session):
    app = ui.CadernoApp.__new__(ui.CadernoApp)
    app.root = object()
    app.session = session
    app.active_entry_id = None
    app.saved_title = ""
    app.saved_body = ""
    initial_collection = session.snapshot.document["collections"][0]["id"]
    app.collection_choice = FakeEntry(initial_collection)
    app.collection_id_by_label = {initial_collection: initial_collection}
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
    monkeypatch.setattr(ui, "show_alert", Mock())
    monkeypatch.setattr(ui, "show_alert", Mock())

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
    monkeypatch.setattr(ui, "show_alert", errors)
    monkeypatch.setattr(ui, "ask_password", lambda *_args: "wrong-synthetic-password")
    app.unlock(path)
    assert app.session is None
    assert "wrong-synthetic-password" not in errors.call_args.args[2]

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
    monkeypatch.setattr(ui, "show_alert", Mock())

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


def test_collection_choice_updates_draft_label_without_saving(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-choice-test.cpv"
    session = create_vault(path, "synthetic-password", VaultSnapshot({
        "schema_version": 1,
        "collections": [
            {"id": "collection-general", "name": "Geral"},
            {"id": "collection-projects", "name": "Projetos"},
        ],
        "attachments": [], "entries": [],
    }))
    app = app_with_editor(session)
    app.collection_options = [("Geral", "collection-general"), ("Projetos", "collection-projects")]
    app.collection_id_by_label = dict(app.collection_options)
    app.collection_choice = FakeEntry("Geral")
    app.collection_choice.set = lambda value: setattr(app.collection_choice, "value", value)
    app.collection_selector = Mock()
    choose = Mock(return_value="collection-projects")
    monkeypatch.setattr(ui, "ask_choice", choose)

    ui.CadernoApp.choose_collection(app)

    assert app.collection_choice.value == "Projetos"
    app.collection_selector.configure.assert_called_once_with(text="Projetos")
    choose.assert_called_once_with(
        app.root, "Coleção da nota", "Escolha uma coleção para esta nota.",
        app.collection_options, "collection-general",
    )
    assert session.snapshot.document["entries"] == []
    session.close()


def test_search_matches_all_words_across_content_and_tags_case_insensitively():
    app = search_app()
    app.set_search_query("DESENHO planejar")

    assert [entry["id"] for entry in app._matching_entries()] == ["entry-art"]

    app.set_search_query("IDEIAS")
    assert {entry["id"] for entry in app._matching_entries()} == {"entry-art", "entry-archive"}
    app.set_search_query("AQUARELA")
    assert [entry["id"] for entry in app._matching_entries()] == ["entry-art"]


def test_search_updates_only_note_list_and_keeps_current_draft():
    app = search_app()
    app.set_search_query("desenho")

    assert app.note_entry_ids == ["entry-art"]
    assert app.note_list.items == ["Aquarela"]
    assert app.note_list.selection == (0,)
    assert app.title_entry.value == "rascunho não salvo"
    assert app.body_editor.value == "corpo em edição"


def test_search_empty_result_shows_empty_state_and_ignores_selection():
    app = search_app()
    app.select_entry = Mock()
    app.set_search_query("sem correspondência")

    assert app.note_entry_ids == []
    assert app.note_list.items == ["Nenhuma nota encontrada"]
    app.note_list.selection_set(0)
    ui.CadernoApp._select_list_entry(app)
    app.select_entry.assert_not_called()


def test_collection_and_tag_filters_combine_with_search_without_resetting_draft(monkeypatch):
    app = search_app()
    app.root = object()
    app.filter_button = Mock()
    app.set_search_query("planejar")
    choose = Mock(return_value=("collection-ideas", "desenho"))
    monkeypatch.setattr(ui, "ask_filters", choose)

    ui.CadernoApp.choose_filters(app)

    assert app.collection_filter_id == "collection-ideas"
    assert app.tag_filter == "desenho"
    assert app.note_entry_ids == ["entry-art"]
    assert app.title_entry.value == "rascunho não salvo"
    app.filter_button.configure.assert_called_once_with(text="Filtros (2) ▾")
    choose.assert_called_once_with(
        app.root,
        [("collection-ideas", "Ideias")],
        ["desenho", "memória", "tela"],
        None,
        None,
    )


def test_cancelled_filter_dialog_preserves_existing_filter_state(monkeypatch):
    app = search_app()
    app.root = object()
    app.collection_filter_id = "collection-ideas"
    app.tag_filter = "desenho"
    app.filter_button = Mock()
    choose = Mock(return_value=None)
    monkeypatch.setattr(ui, "ask_filters", choose)

    ui.CadernoApp.choose_filters(app)

    assert app.collection_filter_id == "collection-ideas"
    assert app.tag_filter == "desenho"
    app.filter_button.configure.assert_not_called()


def test_sort_modes_order_notes_by_edit_creation_and_title():
    app = search_app()
    expected_orders = {
        "updated_desc": ["entry-art", "entry-archive"],
        "updated_asc": ["entry-archive", "entry-art"],
        "created_desc": ["entry-archive", "entry-art"],
        "created_asc": ["entry-art", "entry-archive"],
        "title_asc": ["entry-art", "entry-archive"],
        "title_desc": ["entry-archive", "entry-art"],
    }

    for mode, expected in expected_orders.items():
        app.sort_mode = mode
        assert [entry["id"] for entry in app._matching_entries()] == expected


def test_sort_choice_updates_list_and_cancel_preserves_current_mode(monkeypatch):
    app = search_app()
    app.root = object()
    app.sort_button = Mock()
    choose = Mock(side_effect=("title_asc", None))
    monkeypatch.setattr(ui, "ask_choice", choose)

    ui.CadernoApp.choose_sort(app)
    assert app.sort_mode == "title_asc"
    assert app.note_entry_ids == ["entry-art", "entry-archive"]
    app.sort_button.configure.assert_called_once_with(text="Ordenar: título A–Z ▾")

    ui.CadernoApp.choose_sort(app)
    assert app.sort_mode == "title_asc"
    assert choose.call_args.args[-1] == "title_asc"


def test_add_collection_persists_real_vault_and_rejects_duplicate_name(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-collection-test.cpv"
    session = create_vault(path, "synthetic-password", VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-general", "name": "Geral"}],
        "attachments": [], "entries": [],
    }))
    app = app_with_editor(session)
    show_alert = Mock()
    monkeypatch.setattr(ui, "show_alert", show_alert)
    ask_name = Mock(side_effect=("Projetos", " geral "))
    monkeypatch.setattr(ui, "ask_text", ask_name)
    save = Mock(wraps=session.save)
    session.save = save

    assert app.add_collection()
    assert not app.add_collection()
    assert [item["name"] for item in session.snapshot.document["collections"]] == ["Geral", "Projetos"]
    assert save.call_count == 1
    show_alert.assert_called_once_with(
        app.root, "Coleção existente", "Já existe uma coleção chamada “geral”.",
    )
    app.refresh_notes.assert_called_once_with()
    session.close()


def test_add_collection_cancel_and_blank_name_do_not_persist(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-cancel-collection.cpv"
    session = create_vault(path, "synthetic-password", VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-general", "name": "Geral"}],
        "attachments": [], "entries": [],
    }))
    app = app_with_editor(session)
    prompt = Mock(side_effect=(None, "   "))
    alert = Mock()
    monkeypatch.setattr(ui, "ask_text", prompt)
    monkeypatch.setattr(ui, "show_alert", alert)
    save = Mock(wraps=session.save)
    session.save = save

    assert not app.add_collection()
    assert not app.add_collection()

    assert save.call_count == 0
    assert [item["name"] for item in session.snapshot.document["collections"]] == ["Geral"]
    alert.assert_called_once_with(app.root, "Nome inválido", "Informe um nome de até 4096 caracteres.")
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
    monkeypatch.setattr(ui, "show_alert", showerror)

    assert not app.save_entry()

    session.save.assert_not_called()
    assert app.tags_entry.value == "#" + "x" * 257
    showerror.assert_called_once_with(
        app.root, "Hashtag inválida", "Cada hashtag pode ter até 256 caracteres.",
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
    monkeypatch.setattr(ui, "show_alert", showerror)

    assert not app.save_entry()

    assert app.title_entry.value == "Rascunho local"
    assert app.body_editor.value == "Não deve sobrescrever o cofre"
    assert app.saved_title == "" and app.active_entry_id is None
    reader = open_vault(path, "synthetic-password")
    assert [entry["title"] for entry in reader.snapshot.document["entries"]] == ["Alteração externa"]
    assert "Rascunho local" not in showerror.call_args.args[2]
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
    monkeypatch.setattr(ui, "show_alert", warning)

    assert not app.save_entry()

    assert app.saved_title == "Nota visível"
    assert not app._has_pending_changes()
    warning.assert_called_once()
    session.close()
    reader = open_vault(path, "synthetic-password")
    assert reader.snapshot.document["entries"][0]["title"] == "Nota visível"
    reader.close()
