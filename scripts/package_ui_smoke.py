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
    assert root.minsize()[0] >= 1000
    try:
        _create_empty_vault(app, vault_path)
        _save_synthetic_note(app)
        _exercise_note_focus(app)
        _exercise_search_and_filters(app)
        _reject_duplicate_collection(app)
        _exercise_focus_close(app)
        _close_and_reopen_vault(app, vault_path)
    finally:
        if app.session is not None:
            app.session.close()
        root.destroy()


def _create_empty_vault(app, vault_path: Path) -> None:
    app.create()
    assert app.session is not None and app.session.path == vault_path
    assert app.session.snapshot.document["collections"] == [{"id": "default", "name": "Geral"}]


def _save_synthetic_note(app) -> None:
    app.new_entry()
    assert app.title_dates is None
    app.title_entry.insert(0, "Nota do teste empacotado")
    app.body_editor.insert("1.0", "Conteúdo sintético do smoke test.")
    app.tags_entry.insert(0, "#teste, #empacotamento")
    app.toggle_favorite()
    assert app.save_entry()
    entry = app.session.snapshot.document["entries"][0]
    assert entry["title"] == "Nota do teste empacotado"
    assert entry["body_markdown"] == "Conteúdo sintético do smoke test."
    assert entry["tags"] == ["teste", "empacotamento"]
    assert entry["favorite"] is True
    assert "Criada em " in app.title_dates.cget("text")
    assert "Modificada em " in app.title_dates.cget("text")
    assert app.title_dates.cget("text").count(" às ") == 2


def _exercise_note_focus(app) -> None:
    assert app.focus_button.cget("text") == "Expandir escrita  ⌃⌘E"
    ask_text = ui.ask_text
    try:
        ui.ask_text = lambda *_args: "Projetos"
        assert app.add_collection()
    finally:
        ui.ask_text = ask_text
    app.collection_choice.set("Projetos")
    app.tags_entry.delete(0, "end")
    app.tags_entry.insert(0, "#modo-foco")
    app.toggle_favorite()
    assert app._has_pending_changes()

    app.body_editor.insert("end", " Texto escrito no modo expandido.")
    assert app._toggle_note_focus_shortcut() == "break"
    assert app.focus_mode and app.sidebar.winfo_manager() == ""
    assert app.focus_button.cget("text") == "Voltar ao caderno  ⌃⌘E"
    assert app.note_list_panel.winfo_manager() == ""
    assert app.body_editor.get("1.0", "end-1c").endswith("modo expandido.")
    assert app._exit_focus_shortcut() == "break"
    assert not app.focus_mode and app.sidebar.winfo_manager() == "pack"
    assert app.focus_button.cget("text") == "Expandir escrita  ⌃⌘E"
    assert app.body_editor.get("1.0", "end-1c").endswith("modo expandido.")
    assert app.collection_choice.get() == "Projetos"
    assert app.tags_entry.get() == "#modo-foco"
    assert not app.favorite_choice and app._has_pending_changes()

    assert app._toggle_note_focus_shortcut() == "break"
    assert app.save_entry()
    assert app.focus_mode and app.sidebar.winfo_manager() == ""
    entry = app._active_entry()
    assert entry["collection_id"] != "default"
    assert app._new_entry_shortcut() == "break"
    assert app.collection_choice.get() == "Projetos"
    assert app.active_entry_id is None
    app.select_entry(entry["id"])
    assert entry["tags"] == ["modo-foco"] and not entry["favorite"]
    app.exit_note_focus()


def _exercise_focus_close(app) -> None:
    app.body_editor.insert("end", " Rascunho para testar fechamento.")
    app.enter_note_focus()
    ask_unsaved = ui.ask_unsaved_changes
    try:
        ui.ask_unsaved_changes = lambda *_args: "cancel"
        assert not app.close_vault()
        assert app.focus_mode and app.body_editor.get("1.0", "end-1c").endswith(
            "fechamento."
        )
        ui.ask_unsaved_changes = lambda *_args: "discard"
        assert app.close_vault()
        assert not app.focus_mode and app.session is None
    finally:
        ui.ask_unsaved_changes = ask_unsaved


def _reject_duplicate_collection(app) -> None:
    alerts = []
    ui.ask_text = lambda *_args: "geral"
    ui.show_alert = lambda *args: alerts.append(args)
    assert not app.add_collection()
    assert [item["name"] for item in app.session.snapshot.document["collections"]] == [
        "Geral", "Projetos",
    ]
    assert alerts == [(app.root, "Coleção existente", "Já existe uma coleção chamada “geral”.")]


def _exercise_search_and_filters(app) -> None:
    app.set_search_query("modo-foco")
    assert app.note_entry_ids == [app.active_entry_id]
    ask_filters = ui.ask_filters
    try:
        collection_id = app._active_entry()["collection_id"]
        ui.ask_filters = lambda *_args: (collection_id, "modo-foco", False)
        app.choose_filters()
        assert app.collection_filter_id == collection_id
        assert app.tag_filter == "modo-foco"
        app.set_search_query("sem resultado")
        assert app.note_list.get(0) == "Nenhuma nota encontrada"
        app.set_search_query("")
        assert app.note_entry_ids == [app.active_entry_id]
        ui.ask_filters = lambda *_args: (None, None, True)
        app.choose_filters()
        assert app.favorites_only and app.note_entry_ids == []
        ui.ask_filters = lambda *_args: (None, None, False)
        app.choose_filters()
        assert not app.favorites_only and app.note_entry_ids == [app.active_entry_id]
    finally:
        ui.ask_filters = ask_filters
    ask_choice = ui.ask_choice
    try:
        ui.ask_choice = lambda *_args: "title_asc"
        app.choose_sort()
        assert app.sort_mode == "title_asc"
        assert app.sort_button.cget("text") == "Ordenar: título A–Z ▾"
    finally:
        ui.ask_choice = ask_choice


def _close_and_reopen_vault(app, vault_path: Path) -> None:
    assert app.close_vault()
    app.unlock(vault_path)
    entry = app._active_entry()
    assert entry is not None
    assert entry["title"] == "Nota do teste empacotado"
    assert entry["tags"] == ["modo-foco"]
    assert entry["favorite"] is False
    assert entry["collection_id"] != "default"
    assert app.close_vault()
    persisted = open_vault(vault_path, "synthetic-package-ui-password")
    assert persisted.snapshot.document["entries"][0]["body_markdown"] == (
        "Conteúdo sintético do smoke test. Texto escrito no modo expandido."
    )
    assert persisted.snapshot.document["entries"][0]["tags"] == ["modo-foco"]
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
