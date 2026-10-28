from pathlib import Path
from unittest.mock import Mock

from caderno import ui
from caderno.vault import VaultSnapshot


class FakeTextField:
    def __init__(self):
        self.value = ""
        self.bindings = {}

    def get(self, *_args):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, _index, value):
        self.value = value

    def bind(self, event, callback):
        self.bindings[event] = callback

    def focus_set(self):
        pass


def bare_app():
    app = ui.CadernoApp.__new__(ui.CadernoApp)
    app.root = object()
    app.session = None
    app.active_entry_id = None
    app.title_entry = FakeTextField()
    app.body_editor = FakeTextField()
    app.saved_title = ""
    app.saved_body = ""
    app._activate = Mock()
    app._remember_path = Mock()
    app.refresh_notes = Mock()
    app.update_summary = Mock()
    app.new_entry_button = Mock()
    app.welcome_area = Mock()
    app.summary_area = Mock()
    app.search_area = Mock()
    app.state_area = Mock()
    return app


class FakeDialogWidget:
    def __init__(self, *_args, **options):
        self.options = options
        self.bindings = {}

    def pack(self, **_kwargs):
        pass

    def grid(self, **_kwargs):
        pass

    def columnconfigure(self, *_args, **_kwargs):
        pass

    def bind(self, event, callback):
        self.bindings[event] = callback

    def focus_set(self):
        pass

    def get(self):
        return "synthetic password"


class FakePasswordWindow(FakeDialogWidget):
    def __init__(self, *_args, **options):
        super().__init__(**options)
        self._title = ""
        self.bindings = {}
        self.protocols = {}
        self.lifecycle = []

    def title(self, value=None):
        if value is not None:
            self._title = value
        return self._title

    def configure(self, **_kwargs):
        pass

    def resizable(self, *_args):
        pass

    def transient(self, *_args):
        pass

    def protocol(self, event, callback):
        self.protocols[event] = callback

    def update_idletasks(self):
        pass

    def geometry(self, value):
        self.geometry_value = value

    def deiconify(self):
        self.lifecycle.append("show")

    def wait_visibility(self):
        self.lifecycle.append("visible")

    def after_idle(self, callback):
        self.lifecycle.append("focus_scheduled")
        self.focus_callback = callback

    def grab_set(self):
        self.lifecycle.append("grab")

    def withdraw(self):
        pass

    def destroy(self):
        self.destroyed = True


class FakePasswordEntry(FakeDialogWidget):
    pass


class FakePasswordParent:
    def winfo_rootx(self):
        return 100

    def winfo_rooty(self):
        return 200

    def winfo_width(self):
        return 1180

    def winfo_height(self):
        return 760

    def wait_window(self, window):
        self.waited_window = window


def install_dialog_widgets(monkeypatch):
    monkeypatch.setattr(ui.tk, "Toplevel", FakePasswordWindow)
    monkeypatch.setattr(ui.tk, "Frame", FakeDialogWidget)
    monkeypatch.setattr(ui.tk, "Label", FakeDialogWidget)
    monkeypatch.setattr(ui.tk, "Entry", FakePasswordEntry)


def test_password_dialog_uses_masked_theme_field_and_styled_actions(monkeypatch):
    install_dialog_widgets(monkeypatch)
    buttons = []
    make_button = Mock(side_effect=lambda *args, **kwargs: buttons.append(FakeDialogWidget()) or buttons[-1])
    monkeypatch.setattr(ui, "make_button", make_button)

    dialog = ui.PasswordDialog(FakePasswordParent(), "Abrir base", "Digite a senha.", "Abrir")

    assert dialog.password_entry.options["show"] == "•"
    assert dialog.password_entry.options["bg"] == ui.THEME.panel
    assert dialog.password_entry.options["font"] == ui.THEME.font_body
    assert [call.args[1:3] for call in make_button.call_args_list] == [
        ("Cancelar", "secondary"), ("Abrir", "primary")
    ]
    assert dialog.window.geometry_value == "480x300+450+430"
    assert dialog.window.lifecycle == ["show", "grab", "focus_scheduled"]
    buttons[0].bindings["<Return>"](None)
    assert dialog.result == "synthetic password"
    assert dialog.window.destroyed


def test_password_dialog_escape_and_window_close_cancel_without_value(monkeypatch):
    install_dialog_widgets(monkeypatch)
    monkeypatch.setattr(ui, "make_button", lambda *_args, **_kwargs: FakeDialogWidget())
    escaped = ui.PasswordDialog(FakePasswordParent(), "Abrir", "Senha", "Abrir")
    escaped.window.bindings["<Escape>"](None)
    assert escaped.result is None and escaped.window.destroyed

    closed = ui.PasswordDialog(FakePasswordParent(), "Abrir", "Senha", "Abrir")
    closed.window.protocols["WM_DELETE_WINDOW"]()
    assert closed.result is None and closed.window.destroyed


def test_unsaved_dialog_binds_save_discard_and_cancel_shortcuts(monkeypatch):
    install_dialog_widgets(monkeypatch)
    monkeypatch.setattr(ui, "make_button", lambda *_args, **_kwargs: FakeDialogWidget())

    saved = ui.UnsavedChangesDialog(FakePasswordParent())
    assert "<Command-s>" in saved.window.bindings
    saved.window.bindings["<Command-s>"](None)
    assert saved.result == "save" and saved.window.destroyed

    discarded = ui.UnsavedChangesDialog(FakePasswordParent())
    discarded.window.bindings["<Command-BackSpace>"](None)
    assert discarded.result == "discard" and discarded.window.destroyed

    cancelled = ui.UnsavedChangesDialog(FakePasswordParent())
    cancelled.window.bindings["<Escape>"](None)
    assert cancelled.result == "cancel" and cancelled.window.destroyed


def test_ask_password_waits_for_dialog_and_returns_cancel_value(monkeypatch):
    dialog = Mock(window=object(), result=None)
    monkeypatch.setattr(ui, "PasswordDialog", Mock(return_value=dialog))
    parent = FakePasswordParent()

    result = ui.ask_password(parent, "Abrir", "Digite a senha", "Abrir")

    assert result is None
    assert parent.waited_window is dialog.window


def test_last_vault_restore_waits_until_main_window_is_mapped():
    root = Mock()
    app = type("App", (), {"root": root, "_restore_binding": "binding-1", "restore_last_vault": Mock()})()

    ui.CadernoApp._restore_after_map(app, type("Event", (), {"widget": object()})())
    root.unbind.assert_not_called()

    ui.CadernoApp._restore_after_map(app, type("Event", (), {"widget": root})())

    root.unbind.assert_called_once_with("<Map>", "binding-1")
    root.after_idle.assert_called_once_with(app.restore_last_vault)


def test_create_activates_and_remembers_only_after_password_confirmation(tmp_path, monkeypatch):
    app = bare_app()
    monkeypatch.delenv("CADERNO_CONFIG_DIR", raising=False)
    target = tmp_path / "new.cpv"
    session = object()
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **kwargs: str(target))
    answers = iter(("passphrase", "passphrase"))
    ask_password = Mock(side_effect=lambda *_args: next(answers))
    monkeypatch.setattr(ui, "ask_password", ask_password)
    create = Mock(return_value=session)
    monkeypatch.setattr(ui, "create_vault", create)
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    app.create()

    assert [call.args[1:] for call in ask_password.call_args_list] == [
        ("Criar base", "Escolha uma senha para esta base.", "Continuar"),
        ("Confirmar senha", "Digite a senha novamente para confirmar.", "Confirmar"),
    ]
    create.assert_called_once()
    app._activate.assert_called_once_with(session)
    app._remember_path.assert_called_once_with(Path(target))


def test_create_with_mismatched_password_does_not_create_or_remember(monkeypatch):
    app = bare_app()
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **kwargs: "/tmp/new.cpv")
    answers = iter(("first", "second"))
    monkeypatch.setattr(ui, "ask_password", lambda *_args: next(answers))
    create = Mock()
    monkeypatch.setattr(ui, "create_vault", create)
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    app.create()

    create.assert_not_called()
    app._activate.assert_not_called()
    app._remember_path.assert_not_called()


def test_cancelled_create_picker_does_not_prompt_or_discard_editor_draft(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.title_entry.value = "Rascunho que deve ficar"
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **_kwargs: "")
    unsaved_prompt = Mock()
    monkeypatch.setattr(ui, "ask_unsaved_changes", unsaved_prompt)

    app.create()

    unsaved_prompt.assert_not_called()
    assert app.title_entry.value == "Rascunho que deve ficar"


def test_create_existing_file_does_not_prompt_or_discard_editor_draft(tmp_path, monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.title_entry.value = "Rascunho que deve ficar"
    target = tmp_path / "already-exists.cpv"
    target.touch()
    monkeypatch.delenv("CADERNO_UI_TEST_PROFILE", raising=False)
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **_kwargs: str(target))
    unsaved_prompt = Mock()
    ask_password = Mock()
    monkeypatch.setattr(ui, "ask_unsaved_changes", unsaved_prompt)
    monkeypatch.setattr(ui, "ask_password", ask_password)
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    app.create()

    unsaved_prompt.assert_not_called()
    ask_password.assert_not_called()
    app._activate.assert_not_called()
    assert app.title_entry.value == "Rascunho que deve ficar"


def test_rejected_test_profile_path_does_not_touch_pending_draft(tmp_path, monkeypatch):
    app = bare_app()
    profile = tmp_path / "synthetic-profile"
    profile.mkdir()
    app.session = Mock()
    app.title_entry.value = "Rascunho"
    monkeypatch.setenv("CADERNO_UI_TEST_PROFILE", str(profile))
    ask_unsaved = Mock()
    monkeypatch.setattr(ui, "ask_unsaved_changes", ask_unsaved)
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    app.unlock(tmp_path / "outside.cpv")

    ask_unsaved.assert_not_called()
    assert app.title_entry.value == "Rascunho"


def test_unlock_success_activates_and_remembers_path(tmp_path, monkeypatch):
    app = bare_app()
    monkeypatch.delenv("CADERNO_CONFIG_DIR", raising=False)
    path = tmp_path / "existing.cpv"
    session = object()
    ask_password = Mock(return_value="passphrase")
    monkeypatch.setattr(ui, "ask_password", ask_password)
    open_file = Mock(return_value=session)
    monkeypatch.setattr(ui, "open_vault", open_file)

    app.unlock(path)

    ask_password.assert_called_once_with(
        app.root, "Abrir base", "Digite a senha desta base para desbloqueá-la.", "Abrir base"
    )
    open_file.assert_called_once_with(path, "passphrase")
    app._activate.assert_called_once_with(session)
    app._remember_path.assert_called_once_with(path)


def test_unlock_failure_keeps_current_session_and_does_not_remember(monkeypatch):
    app = bare_app()
    monkeypatch.delenv("CADERNO_CONFIG_DIR", raising=False)
    original_session = object()
    app.session = original_session
    app.title_entry.value = "Rascunho a preservar"
    app.body_editor.value = "Conteúdo a preservar"
    monkeypatch.setattr(ui, "ask_password", lambda *_args: "wrong")
    monkeypatch.setattr(ui, "open_vault", Mock(side_effect=ValueError("secret detail")))
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    app.unlock(Path("invalid.cpv"))

    app._activate.assert_not_called()
    app._remember_path.assert_not_called()
    assert app.session is original_session
    assert app.title_entry.value == "Rascunho a preservar"
    assert app.body_editor.value == "Conteúdo a preservar"
    assert "secret detail" not in showerror.call_args.args[1]


def test_cancelled_unlock_keeps_old_session_and_closes_candidate(monkeypatch):
    app = bare_app()
    current = Mock(path=Path("current.cpv"))
    candidate = Mock()
    app.session = current
    app.title_entry.value = "Rascunho a preservar"
    app.body_editor.value = "Conteúdo a preservar"
    monkeypatch.setattr(ui, "ask_password", lambda *_args: "synthetic-password")
    monkeypatch.setattr(ui, "open_vault", Mock(return_value=candidate))
    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: "cancel")

    app.unlock(Path("other.cpv"))

    candidate.close.assert_called_once_with()
    app._activate.assert_not_called()
    app._remember_path.assert_not_called()
    assert app.session is current
    assert app.title_entry.value == "Rascunho a preservar"
    assert app.body_editor.value == "Conteúdo a preservar"


def test_unlocking_current_vault_is_noop_and_preserves_dirty_editor(monkeypatch, tmp_path):
    app = bare_app()
    path = tmp_path / "current.cpv"
    app.session = Mock(path=path)
    app.title_entry.value = "Rascunho a preservar"
    ask_password = Mock()
    monkeypatch.setattr(ui, "ask_password", ask_password)
    monkeypatch.setattr(ui, "open_vault", Mock())

    app.unlock(path)

    ask_password.assert_not_called()
    ui.open_vault.assert_not_called()
    assert app.title_entry.value == "Rascunho a preservar"


def test_close_vault_closes_session_and_returns_to_locked_state():
    app = bare_app()
    session = Mock()
    app.session = session
    app.show_locked = Mock()

    app.close_vault()

    session.close.assert_called_once_with()
    assert app.session is None
    app.show_locked.assert_called_once_with()


def test_save_new_note_creates_entry_with_schema_fields(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.session.snapshot = VaultSnapshot({
        "schema_version": 1,
        "collections": [{"id": "collection-1", "name": "Geral"}],
        "attachments": [],
        "entries": [],
    })
    app.title_entry.value = "  Ideia nova  "
    app.body_editor.value = "Corpo sintético"
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    assert app.save_entry()

    saved = app.session.save.call_args.args[0]
    entry = saved.document["entries"][0]
    assert entry["title"] == "Ideia nova"
    assert entry["body_markdown"] == "Corpo sintético"
    assert entry["collection_id"] == "collection-1"
    assert entry["tags"] == [] and entry["attachments"] == []
    assert entry["created_at"].endswith("Z")
    assert entry["updated_at"] == entry["created_at"]
    assert entry["published_at"] is None and entry["favorite"] is False
    assert app.active_entry_id == entry["id"]
    assert app.saved_title == "Ideia nova"


def test_save_edit_preserves_created_time_tags_favorite_and_attachments(monkeypatch):
    app = bare_app()
    document = {
        "schema_version": 1,
        "collections": [{"id": "collection-1", "name": "Geral"}],
        "attachments": [{
            "id": "attachment-1", "entry_id": "entry-1", "filename": "pixel.png",
            "media_type": "image/png",
        }],
        "entries": [{
            "id": "entry-1", "title": "Antes", "body_markdown": "Texto antigo",
            "collection_id": "collection-1", "tags": ["sintética"],
            "created_at": "2026-10-24T09:00:00Z", "updated_at": "2026-10-24T09:00:00Z",
            "published_at": None, "favorite": True, "attachments": ["attachment-1"],
        }],
    }
    app.session = Mock()
    app.session.snapshot = VaultSnapshot(document)
    app.active_entry_id = "entry-1"
    app.title_entry.value = "Depois"
    app.body_editor.value = "Texto editado"
    app.saved_title = "Antes"
    app.saved_body = "Texto antigo"
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    assert app.save_entry()

    saved = app.session.save.call_args.args[0]
    entry = saved.document["entries"][0]
    assert entry["title"] == "Depois" and entry["body_markdown"] == "Texto editado"
    assert entry["created_at"] == document["entries"][0]["created_at"]
    assert entry["tags"] == ["sintética"] and entry["favorite"] is True
    assert entry["attachments"] == ["attachment-1"]
    assert saved.document["attachments"] == document["attachments"]


def test_save_without_title_keeps_editor_open(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.title_entry.value = "   "
    app.body_editor.value = "Corpo que não deve sumir"
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    assert not app.save_entry()

    app.session.save.assert_not_called()
    assert app.body_editor.value == "Corpo que não deve sumir"
    showerror.assert_called_once()


def test_saving_unchanged_existing_note_does_not_rewrite_the_vault():
    app = bare_app()
    app.session = Mock()
    app.active_entry_id = "entry-1"
    app.title_entry.value = "Already saved"
    app.body_editor.value = "Unchanged body"
    app.saved_title = "Already saved"
    app.saved_body = "Unchanged body"

    assert app.save_entry()

    app.session.save.assert_not_called()


def test_failed_save_keeps_draft_and_saved_baseline(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.session.snapshot = VaultSnapshot({
        "schema_version": 1, "collections": [{"id": "c", "name": "Geral"}],
        "attachments": [], "entries": [],
    })
    app.session.save.side_effect = OSError("synthetic failure")
    app.title_entry.value = "Rascunho"
    app.body_editor.value = "Não perder"
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    assert not app.save_entry()

    assert app.title_entry.value == "Rascunho"
    assert app.body_editor.value == "Não perder"
    assert app.saved_title == "" and app.active_entry_id is None
    showerror.assert_called_once()


def test_uncertain_durability_treats_visible_snapshot_as_saved(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.session.snapshot = VaultSnapshot({
        "schema_version": 1, "collections": [{"id": "c", "name": "Geral"}],
        "attachments": [], "entries": [],
    })

    def save_with_uncertain_durability(updated):
        app.session.snapshot = updated
        raise ui.DurabilityUncertainError("synthetic")

    app.session.save.side_effect = save_with_uncertain_durability
    app.title_entry.value = "Alteração visível"
    app.body_editor.value = "Conteúdo"
    warning = Mock()
    monkeypatch.setattr(ui.messagebox, "showwarning", warning)

    assert not app.save_entry()

    assert app.saved_title == "Alteração visível"
    assert app.session.snapshot.document["entries"][0]["title"] == app.saved_title
    warning.assert_called_once()


def test_uncertain_durability_does_not_close_vault_from_same_action(monkeypatch):
    app = bare_app()
    session = Mock()
    session.snapshot = VaultSnapshot({
        "schema_version": 1, "collections": [{"id": "c", "name": "Geral"}],
        "attachments": [], "entries": [],
    })
    app.session = session
    app.title_entry.value = "Gravado com durabilidade incerta"
    app.body_editor.value = "Conteúdo"
    app.show_locked = Mock()

    def uncertain_save(updated):
        session.snapshot = updated
        raise ui.DurabilityUncertainError("synthetic")

    session.save.side_effect = uncertain_save
    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: "save")
    monkeypatch.setattr(ui.messagebox, "showwarning", Mock())

    assert not app.close_vault()

    session.close.assert_not_called()
    assert app.session is session
    assert app.session.snapshot.document["entries"][0]["title"] == app.saved_title
    assert not app._has_pending_changes()


def test_pending_changes_can_be_saved_discarded_or_cancelled(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.title_entry.value = "Alteração"
    app.save_entry = Mock(return_value=True)
    ask = Mock(side_effect=("cancel", "discard", "save"))
    monkeypatch.setattr(ui, "ask_unsaved_changes", ask)

    assert not app._confirm_pending_changes()
    assert app._confirm_pending_changes()
    assert app._confirm_pending_changes()
    app.save_entry.assert_called_once_with()


def test_cancelled_note_switch_restores_previous_selection(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.active_entry_id = "entry-old"
    app.note_entry_ids = ["entry-old", "entry-new"]
    app.note_list = Mock()
    app.title_entry.value = "Rascunho"
    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: "cancel")

    app.select_entry("entry-new")

    assert app.active_entry_id == "entry-old"
    app.note_list.selection_clear.assert_called_once_with(0, "end")
    app.note_list.selection_set.assert_called_once_with(0)
    app.refresh_notes.assert_not_called()


def test_close_vault_cancel_preserves_session_and_pending_text(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.title_entry.value = "Rascunho"
    app.body_editor.value = "Texto"
    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: "cancel")

    assert not app.close_vault()

    app.session.close.assert_not_called()
    assert app.session is not None
    assert app.body_editor.value == "Texto"


def test_closing_app_after_closing_vault_does_not_read_destroyed_editor():
    app = bare_app()
    app.root = Mock()
    session = Mock()
    app.session = session
    app.show_locked = Mock()

    assert app.close_vault()
    app.title_entry.get = Mock(side_effect=AssertionError("widget should not be read"))
    app.body_editor.get = Mock(side_effect=AssertionError("widget should not be read"))
    app.close_app()

    app.root.destroy.assert_called_once_with()
    session.close.assert_called_once_with()


def test_shortcut_handlers_keep_cancel_and_discard_distinct(monkeypatch):
    app = bare_app()
    app.session = Mock()
    app.title_entry.value = "Rascunho"
    app.save_entry = Mock()
    decisions = iter(("cancel", "discard", "save"))
    monkeypatch.setattr(ui, "ask_unsaved_changes", lambda _parent: next(decisions))

    assert app._cancel_edit_shortcut() == "break"
    assert app.title_entry.value == "Rascunho"
    assert app._cancel_edit_shortcut() == "break"
    assert app._cancel_edit_shortcut() == "break"
    app.save_entry.assert_called_once_with()


def test_command_s_handler_saves_and_consumes_key_event():
    app = bare_app()
    app.save_entry = Mock()

    assert app._save_shortcut() == "break"
    app.save_entry.assert_called_once_with()


def test_locked_and_unlocked_views_choose_the_shared_button_variants():
    app = bare_app()
    app.status = Mock()
    app.status_detail = Mock()
    app.close_button = Mock()
    app.summary_values = []
    app.update_summary = Mock()
    app.render_state = Mock()

    app.show_locked()
    locked_actions = app.render_state.call_args.args[2:]
    assert [action[2] for action in locked_actions] == ["primary", "primary"]
    app.new_entry_button.configure.assert_called_once_with(state="disabled")

    app.render_state.reset_mock()
    session = Mock(path=Path("synthetic.cpv"), snapshot=Mock(document={"entries": [], "collections": []}))
    app.show_unlocked(session)
    app.render_state.assert_not_called()
    app.refresh_notes.assert_called_once_with()
    assert app.new_entry_button.configure.call_args_list[-1].kwargs == {"state": "normal"}


def test_sidebar_close_button_uses_the_same_secondary_variant(monkeypatch):
    class FakeWidget:
        def pack(self, **_kwargs):
            pass

    monkeypatch.setattr(ui.tk, "Frame", lambda *_args, **_kwargs: FakeWidget())
    monkeypatch.setattr(ui.tk, "Label", lambda *_args, **_kwargs: FakeWidget())
    make_button = Mock(return_value=FakeWidget())
    monkeypatch.setattr(ui, "make_button", make_button)
    app = Mock()

    ui.build_sidebar_status(None, app)

    assert make_button.call_args.args[1:3] == ("Fechar base", "secondary")
    assert make_button.call_args.kwargs["command"] == app.close_vault


def test_restore_missing_last_vault_warns_without_trying_to_unlock(tmp_path, monkeypatch):
    app = bare_app()
    missing_path = tmp_path / "missing.cpv"
    monkeypatch.setattr(ui, "load_last_vault", lambda: missing_path)
    app.unlock = Mock()
    showinfo = Mock()
    monkeypatch.setattr(ui.messagebox, "showinfo", showinfo)

    app.restore_last_vault()

    app.unlock.assert_not_called()
    showinfo.assert_called_once()


def test_file_dialogs_start_in_isolated_profile_when_configured(tmp_path, monkeypatch):
    app = bare_app()
    monkeypatch.setenv("CADERNO_UI_TEST_PROFILE", str(tmp_path))
    save_dialog = Mock(return_value="")
    open_dialog = Mock(return_value="")
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", save_dialog)
    monkeypatch.setattr(ui.filedialog, "askopenfilename", open_dialog)

    app.create()
    app.choose()

    assert save_dialog.call_args.kwargs["initialdir"] == str(tmp_path)
    assert open_dialog.call_args.kwargs["initialdir"] == str(tmp_path)


def test_unlock_rejects_file_outside_isolated_test_profile(tmp_path, monkeypatch):
    app = bare_app()
    profile = tmp_path / "test-profile"
    profile.mkdir()
    monkeypatch.setenv("CADERNO_CONFIG_DIR", str(profile))
    monkeypatch.setenv("CADERNO_UI_TEST_PROFILE", str(profile))
    monkeypatch.setattr(ui, "open_vault", Mock())
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    app.unlock(tmp_path / "real-vault.cpv")

    ui.open_vault.assert_not_called()
    app._remember_path.assert_not_called()
    showerror.assert_called_once()
    assert "real-vault.cpv" not in showerror.call_args.args[1]


def test_create_rejects_destination_outside_isolated_test_profile(tmp_path, monkeypatch):
    app = bare_app()
    profile = tmp_path / "test-profile"
    profile.mkdir()
    monkeypatch.setenv("CADERNO_CONFIG_DIR", str(profile))
    monkeypatch.setenv("CADERNO_UI_TEST_PROFILE", str(profile))
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **kwargs: str(tmp_path / "real-vault.cpv"))
    password_prompt = Mock()
    monkeypatch.setattr(ui, "ask_password", password_prompt)
    create = Mock()
    monkeypatch.setattr(ui, "create_vault", create)
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    app.create()

    password_prompt.assert_not_called()
    create.assert_not_called()
    app._remember_path.assert_not_called()
    showerror.assert_called_once()


def test_preferences_override_alone_does_not_restrict_vault_opening(tmp_path, monkeypatch):
    app = bare_app()
    monkeypatch.setenv("CADERNO_CONFIG_DIR", str(tmp_path / "preferences"))
    monkeypatch.delenv("CADERNO_UI_TEST_PROFILE", raising=False)
    session = object()
    monkeypatch.setattr(ui, "ask_password", lambda *_args: "passphrase")
    open_file = Mock(return_value=session)
    monkeypatch.setattr(ui, "open_vault", open_file)

    vault_path = tmp_path / "outside-profile.cpv"
    app.unlock(vault_path)

    open_file.assert_called_once_with(vault_path, "passphrase")
    app._activate.assert_called_once_with(session)
