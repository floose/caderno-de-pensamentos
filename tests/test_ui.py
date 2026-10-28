from pathlib import Path
from unittest.mock import Mock

from caderno import ui


def bare_app():
    app = ui.CadernoApp.__new__(ui.CadernoApp)
    app.root = object()
    app.session = None
    app._activate = Mock()
    app._remember_path = Mock()
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
    monkeypatch.setattr(ui, "ask_password", lambda *_args: "wrong")
    monkeypatch.setattr(ui, "open_vault", Mock(side_effect=ValueError("secret detail")))
    showerror = Mock()
    monkeypatch.setattr(ui.messagebox, "showerror", showerror)

    app.unlock(Path("invalid.cpv"))

    app._activate.assert_not_called()
    app._remember_path.assert_not_called()
    assert app.session is original_session
    assert "secret detail" not in showerror.call_args.args[1]


def test_close_vault_closes_session_and_returns_to_locked_state():
    app = bare_app()
    session = Mock()
    app.session = session
    app.show_locked = Mock()

    app.close_vault()

    session.close.assert_called_once_with()
    assert app.session is None
    app.show_locked.assert_called_once_with()


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

    app.render_state.reset_mock()
    session = Mock(path=Path("synthetic.cpv"), snapshot=Mock(document={"entries": [], "collections": []}))
    app.show_unlocked(session)
    unlocked_actions = app.render_state.call_args.args[2:]
    assert [action[2] for action in unlocked_actions] == ["secondary", "secondary"]


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
