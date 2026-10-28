import json
import stat

from caderno import preferences


def test_last_vault_preferences_store_only_path_with_private_permissions(tmp_path, monkeypatch):
    target = tmp_path / "Application Support" / "Caderno" / "preferences.json"
    monkeypatch.setattr(preferences, "_preferences_file", lambda: target)
    vault_path = tmp_path / "example.cpv"

    preferences.save_last_vault(vault_path)

    assert preferences.load_last_vault() == vault_path
    assert json.loads(target.read_text(encoding="utf-8")) == {"last_vault": str(vault_path)}
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    assert stat.S_IMODE(target.parent.stat().st_mode) == 0o700
    assert list(target.parent.glob(".preferences-*")) == []


def test_last_vault_preferences_ignore_missing_invalid_and_insecure_files(tmp_path, monkeypatch):
    target = tmp_path / "preferences.json"
    monkeypatch.setattr(preferences, "_preferences_file", lambda: target)

    assert preferences.load_last_vault() is None
    target.write_text("not json", encoding="utf-8")
    assert preferences.load_last_vault() is None
    target.write_text('{"last_vault":"/tmp/example.cpv"}', encoding="utf-8")
    target.chmod(0o644)
    assert preferences.load_last_vault() is None


def test_last_vault_preferences_ignore_symlink(tmp_path, monkeypatch):
    target = tmp_path / "preferences.json"
    external = tmp_path / "external.json"
    external.write_text('{"last_vault":"/tmp/example.cpv"}', encoding="utf-8")
    target.symlink_to(external)
    monkeypatch.setattr(preferences, "_preferences_file", lambda: target)

    assert preferences.load_last_vault() is None


def test_config_directory_can_be_isolated_for_manual_ui_testing(tmp_path, monkeypatch):
    monkeypatch.setenv("CADERNO_CONFIG_DIR", str(tmp_path))

    assert preferences._preferences_file() == tmp_path / "Caderno de Pensamentos" / "preferences.json"


def test_override_never_changes_permissions_on_the_supplied_profile_root(tmp_path, monkeypatch):
    profile = tmp_path / "profile"
    profile.mkdir(mode=0o755)
    profile.chmod(0o755)
    monkeypatch.setenv("CADERNO_CONFIG_DIR", str(profile))

    preferences.save_last_vault(profile / "test.cpv")

    assert stat.S_IMODE(profile.stat().st_mode) == 0o755
    app_preferences = profile / "Caderno de Pensamentos"
    assert stat.S_IMODE(app_preferences.stat().st_mode) == 0o700
