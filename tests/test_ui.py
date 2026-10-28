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


def test_create_activates_and_remembers_only_after_password_confirmation(tmp_path, monkeypatch):
    app = bare_app()
    monkeypatch.delenv("CADERNO_CONFIG_DIR", raising=False)
    target = tmp_path / "new.cpv"
    session = object()
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **kwargs: str(target))
    answers = iter(("passphrase", "passphrase"))
    monkeypatch.setattr(ui.simpledialog, "askstring", lambda *args, **kwargs: next(answers))
    create = Mock(return_value=session)
    monkeypatch.setattr(ui, "create_vault", create)
    monkeypatch.setattr(ui.messagebox, "showerror", Mock())

    app.create()

    create.assert_called_once()
    app._activate.assert_called_once_with(session)
    app._remember_path.assert_called_once_with(Path(target))


def test_create_with_mismatched_password_does_not_create_or_remember(monkeypatch):
    app = bare_app()
    monkeypatch.setattr(ui.filedialog, "asksaveasfilename", lambda **kwargs: "/tmp/new.cpv")
    answers = iter(("first", "second"))
    monkeypatch.setattr(ui.simpledialog, "askstring", lambda *args, **kwargs: next(answers))
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
    monkeypatch.setattr(ui.simpledialog, "askstring", lambda *args, **kwargs: "passphrase")
    open_file = Mock(return_value=session)
    monkeypatch.setattr(ui, "open_vault", open_file)

    app.unlock(path)

    open_file.assert_called_once_with(path, "passphrase")
    app._activate.assert_called_once_with(session)
    app._remember_path.assert_called_once_with(path)


def test_unlock_failure_keeps_current_session_and_does_not_remember(monkeypatch):
    app = bare_app()
    monkeypatch.delenv("CADERNO_CONFIG_DIR", raising=False)
    original_session = object()
    app.session = original_session
    monkeypatch.setattr(ui.simpledialog, "askstring", lambda *args, **kwargs: "wrong")
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
    monkeypatch.setattr(ui.simpledialog, "askstring", password_prompt)
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
    monkeypatch.setattr(ui.simpledialog, "askstring", lambda *args, **kwargs: "passphrase")
    open_file = Mock(return_value=session)
    monkeypatch.setattr(ui, "open_vault", open_file)

    vault_path = tmp_path / "outside-profile.cpv"
    app.unlock(vault_path)

    open_file.assert_called_once_with(vault_path, "passphrase")
    app._activate.assert_called_once_with(session)
