"""Exercita o fluxo da UI Tk real no runtime PyInstaller."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
import traceback

from caderno import ui
from caderno.vault import open_vault


def _run_ui_flow(profile: Path) -> None:
    """Cria, salva, fecha e reabre um cofre sintético pelos callbacks da UI."""
    os.environ["CADERNO_CONFIG_DIR"] = str(profile / "config")
    os.environ["CADERNO_UI_TEST_PROFILE"] = str(profile)
    vault_path = profile / "synthetic-ui.cpv"
    ui.ask_path = lambda *_args: vault_path
    ui.ask_password = lambda *_args: "synthetic-package-ui-password"
    root = tk.Tk()
    root.withdraw()
    app = ui.CadernoApp(root)
    try:
        _create_empty_vault(app, vault_path)
        _save_synthetic_note(app)
        _exercise_search_and_filters(app)
        _reject_duplicate_collection(app)
        _close_and_reopen_vault(app, vault_path)
    finally:
        if app.session is not None:
            app.close_vault()
        root.destroy()


def _create_empty_vault(app, vault_path: Path) -> None:
    app.create()
    assert app.session is not None and app.session.path == vault_path
    assert app.session.snapshot.document["collections"] == [{"id": "default", "name": "Geral"}]


def _save_synthetic_note(app) -> None:
    app.new_entry()
    app.title_entry.insert(0, "Nota do teste empacotado")
    app.body_editor.insert("1.0", "Conteúdo sintético do smoke test.")
    app.tags_entry.insert(0, "#teste, #empacotamento")
    assert app.save_entry()
    entry = app.session.snapshot.document["entries"][0]
    assert entry["title"] == "Nota do teste empacotado"
    assert entry["body_markdown"] == "Conteúdo sintético do smoke test."
    assert entry["tags"] == ["teste", "empacotamento"]


def _reject_duplicate_collection(app) -> None:
    alerts = []
    ui.ask_text = lambda *_args: "geral"
    ui.show_alert = lambda *args: alerts.append(args)
    assert not app.add_collection()
    assert [item["name"] for item in app.session.snapshot.document["collections"]] == ["Geral"]
    assert alerts == [(app.root, "Coleção existente", "Já existe uma coleção chamada “geral”.")]


def _exercise_search_and_filters(app) -> None:
    app.set_search_query("empacotamento")
    assert app.note_entry_ids == [app.active_entry_id]
    ask_filters = ui.ask_filters
    try:
        ui.ask_filters = lambda *_args: ("default", "empacotamento")
        app.choose_filters()
        assert app.collection_filter_id == "default"
        assert app.tag_filter == "empacotamento"
        app.set_search_query("sem resultado")
        assert app.note_list.get(0) == "Nenhuma nota encontrada"
        app.set_search_query("")
        assert app.note_entry_ids == [app.active_entry_id]
        ui.ask_filters = lambda *_args: (None, None)
        app.choose_filters()
        assert app.collection_filter_id is None and app.tag_filter is None
    finally:
        ui.ask_filters = ask_filters


def _close_and_reopen_vault(app, vault_path: Path) -> None:
    assert app.close_vault()
    app.unlock(vault_path)
    entry = app._active_entry()
    assert entry is not None
    assert entry["title"] == "Nota do teste empacotado"
    assert entry["tags"] == ["teste", "empacotamento"]
    assert app.close_vault()
    persisted = open_vault(vault_path, "synthetic-package-ui-password")
    assert persisted.snapshot.document["entries"][0]["body_markdown"] == "Conteúdo sintético do smoke test."
    persisted.close()


def main() -> None:
    """Executa o fluxo sintético e grava o resultado para o build windowed."""
    result_path = Path(os.environ["CADERNO_PACKAGE_UI_SMOKE_RESULT"])
    try:
        with TemporaryDirectory(prefix="caderno-package-ui-smoke-", dir="/private/tmp") as directory:
            _run_ui_flow(Path(directory))
    except Exception:
        result_path.write_text(f"FAIL\n{traceback.format_exc()}", encoding="utf-8")
        raise
    result_path.write_text("PASS: fluxo UI Tk + CPV1 empacotado.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
