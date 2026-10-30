import os
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import font
from typing import Literal
from uuid import uuid4

if __package__:
    from .preferences import load_last_vault, save_last_vault
    from .vault import DurabilityUncertainError, VaultSession, VaultSnapshot, create_vault, open_vault
else:
    from preferences import load_last_vault, save_last_vault
    from vault import DurabilityUncertainError, VaultSession, VaultSnapshot, create_vault, open_vault

ButtonVariant = Literal["primary", "secondary"]


@dataclass(frozen=True)
class ButtonStyle:
    """Cores semânticas de um botão em repouso, ativo e com foco."""

    background: str
    foreground: str
    active_background: str
    active_foreground: str
    focus: str


@dataclass(frozen=True)
class UILayout:
    """Dimensões e espaçamentos usados para compor a janela."""

    window_size: tuple
    minimum_window_size: tuple
    sidebar_width: int
    sidebar_padding_x: int
    sidebar_padding_y: int
    main_horizontal_padding: int
    main_vertical_padding: int
    topbar_vertical_padding: int
    state_horizontal_padding: int
    state_vertical_padding: int
    button_horizontal_padding: int
    highlight_thickness: int
    button_vertical_padding: int
    search_gap: int
    search_vertical_padding: int
    search_bottom_padding: int
    state_description_wrap: int
    state_icon_bottom_padding: int
    state_description_padding: tuple
    state_action_padding: int
    welcome_title_padding: tuple
    summary_vertical_padding: tuple
    password_dialog_size: tuple
    password_dialog_padding: int
    password_prompt_wrap: int
    alert_dialog_size: tuple
    alert_dialog_padding: int
    text_dialog_size: tuple
    text_dialog_padding: int
    path_dialog_size: tuple
    path_dialog_padding: int
    choice_dialog_size: tuple
    choice_dialog_padding: int
    filter_dialog_size: tuple
    filter_dialog_padding: int
    unsaved_dialog_size: tuple
    unsaved_dialog_padding: int
    notes_list_width: int
    notes_list_gap: int


@dataclass(frozen=True)
class UITheme:
    """Tokens visuais compartilhados pela interface Tkinter."""

    paper: str
    sidebar: str
    panel: str
    ink: str
    muted: str
    line: str
    green: str
    sage: str
    state_panel: str
    field_border: str
    state_icon_background: str
    state_icon_foreground: str
    state_title: str
    selected_navigation_background: str
    selected_navigation_foreground: str
    locked_status: str
    welcome_title: str
    empty_state_border: str
    brand_mark_foreground: str
    on_primary_button: str
    primary_button_background: str
    primary_button_active_background: str
    secondary_button_background: str
    secondary_button_active_background: str
    disabled_button_background: str
    font_body: tuple
    font_text: tuple
    font_fixed: tuple
    font_button: tuple
    font_label: tuple
    font_tiny: tuple
    font_brand: tuple
    font_brand_name: tuple
    font_brand_subtitle: tuple
    font_icon: tuple
    font_title: tuple
    font_heading: tuple
    font_summary: tuple
    font_mono_small: tuple
    layout: UILayout

    @property
    def primary_button(self) -> ButtonStyle:
        return ButtonStyle(
            self.primary_button_background, self.on_primary_button,
            self.primary_button_active_background, self.on_primary_button,
            self.green,
        )

    @property
    def secondary_button(self) -> ButtonStyle:
        return ButtonStyle(
            self.secondary_button_background, self.ink,
            self.secondary_button_active_background, self.ink, self.green,
        )

    @property
    def disabled_button(self) -> ButtonStyle:
        return ButtonStyle(
            self.disabled_button_background, self.muted,
            self.disabled_button_background, self.muted, self.green,
        )


THEME = UITheme(
    paper="#f5f3ee", sidebar="#f0eee8", panel="#fffefa", ink="#202622",
    muted="#5f665e", line="#e8e6df", green="#355c47", sage="#536b56",
    state_panel="#f7f6f1", field_border="#7c8278",
    state_icon_background="#f1f2ec", state_icon_foreground="#6d826f",
    state_title="#38453b", selected_navigation_background="#e4e5dd",
    selected_navigation_foreground="#273b30", locked_status="#5b655c",
    welcome_title="#252c27", empty_state_border="#dcdcd3",
    brand_mark_foreground="#f6f3e9",
    on_primary_button="#202622", primary_button_background="#c8d5c7",
    primary_button_active_background="#c0cfbe",
    secondary_button_background="#dfe4dc", secondary_button_active_background="#cfd8cc",
    disabled_button_background="#e3e5de",
    font_body=("Arial", 12), font_text=("Georgia", 14),
    font_fixed=("Courier New", 12), font_button=("Arial", 12, "bold"),
    font_label=("Arial", 11), font_tiny=("Arial", 10),
    font_brand=("Georgia", 20, "bold"), font_brand_name=("Arial", 12, "bold"),
    font_brand_subtitle=("Georgia", 11, "italic"), font_icon=("Georgia", 22),
    font_title=("Georgia", 34), font_heading=("Georgia", 22),
    font_summary=("Georgia", 18), font_mono_small=("Courier New", 10),
    layout=UILayout(
        window_size=(1180, 760), minimum_window_size=(900, 620),
        sidebar_width=250, sidebar_padding_x=18, sidebar_padding_y=24,
        main_horizontal_padding=48, main_vertical_padding=45,
        topbar_vertical_padding=20, state_horizontal_padding=20,
        state_vertical_padding=34, button_horizontal_padding=12,
        highlight_thickness=1, button_vertical_padding=9,
        search_gap=12, search_vertical_padding=10, search_bottom_padding=18,
        state_description_wrap=480, state_icon_bottom_padding=10,
        state_description_padding=(7, 15), state_action_padding=3,
        welcome_title_padding=(9, 4), summary_vertical_padding=(27, 23),
        password_dialog_size=(480, 300), password_dialog_padding=24,
        password_prompt_wrap=380,
        alert_dialog_size=(460, 220), alert_dialog_padding=24,
        text_dialog_size=(480, 260), text_dialog_padding=24,
        path_dialog_size=(720, 520), path_dialog_padding=20,
        choice_dialog_size=(440, 380), choice_dialog_padding=22,
        filter_dialog_size=(560, 560), filter_dialog_padding=22,
        unsaved_dialog_size=(520, 220), unsaved_dialog_padding=24,
        notes_list_width=190, notes_list_gap=18,
    ),
)


class PasswordDialog:
    """Diálogo modal de senha com os mesmos tokens visuais da janela principal."""

    def __init__(self, parent, title: str, prompt: str, submit_label: str):
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title(title)
        self.window.configure(bg=THEME.paper)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self._build_content(prompt, submit_label)
        self.window.bind("<Return>", self._submit_event)
        self.window.bind("<Escape>", self._cancel_event)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._center_on_parent(parent)
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.password_entry.focus_set)

    def _build_content(self, prompt: str, submit_label: str):
        layout = THEME.layout
        self.window.geometry(f"{layout.password_dialog_size[0]}x{layout.password_dialog_size[1]}")
        panel = tk.Frame(self.window, bg=THEME.state_panel, padx=layout.password_dialog_padding)
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(
            panel, text=self.window.title(), bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            panel, text=prompt, bg=THEME.state_panel, fg=THEME.muted,
            font=THEME.font_body, wraplength=layout.password_prompt_wrap, justify="left",
        ).pack(anchor="w", pady=(0, 18))
        tk.Label(
            panel, text="Senha", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(anchor="w", pady=(0, 5))
        self.password_entry = tk.Entry(
            panel, show="•", bg=THEME.panel, fg=THEME.ink,
            insertbackground=THEME.green, highlightbackground=THEME.field_border,
            highlightcolor=THEME.green, highlightthickness=THEME.layout.highlight_thickness,
            relief="flat", font=THEME.font_body,
        )
        self.password_entry.pack(fill="x", ipady=7)
        self._build_actions(panel, submit_label)

    def _build_actions(self, parent, submit_label: str):
        actions = tk.Frame(parent, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(22, 0))
        actions.columnconfigure(0, weight=1)
        cancel_button = make_button(
            actions, "Cancelar", "secondary", pady=8, command=self.cancel,
        )
        submit_button = make_button(
            actions, submit_label, "primary", pady=8, command=self.submit,
        )
        cancel_button.grid(row=0, column=0, sticky="e", padx=(0, 8))
        submit_button.grid(row=0, column=1, sticky="e")
        cancel_button.bind("<Return>", self._submit_event)
        submit_button.bind("<Return>", self._submit_event)

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.password_dialog_size
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _submit_event(self, _event=None):
        self.submit()
        return "break"

    def _cancel_event(self, _event=None):
        self.cancel()
        return "break"

    def submit(self):
        self.result = self.password_entry.get()
        self.window.destroy()

    def cancel(self):
        self.window.destroy()


def ask_password(parent, title: str, prompt: str, submit_label: str) -> str | None:
    """Mostra o diálogo modal de senha e devolve o valor ou None ao cancelar."""
    dialog = PasswordDialog(parent, title, prompt, submit_label)
    parent.wait_window(dialog.window)
    return dialog.result


class AlertDialog:
    """Exibe um alerta modal com as cores, fontes e botões do tema do app."""

    def __init__(self, parent, title: str, message: str):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title(title)
        self.window.configure(bg=THEME.paper)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self._build_content(title, message)
        self.window.bind("<Return>", self._dismiss_event)
        self.window.bind("<Escape>", self._dismiss_event)
        self.window.protocol("WM_DELETE_WINDOW", self.dismiss)
        self._center_on_parent(parent)
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.dismiss_button.focus_set)

    def _build_content(self, title: str, message: str):
        width, height = THEME.layout.alert_dialog_size
        self.window.geometry(f"{width}x{height}")
        panel = tk.Frame(
            self.window, bg=THEME.state_panel, padx=THEME.layout.alert_dialog_padding, pady=20,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        content = tk.Frame(panel, bg=THEME.state_panel)
        content.pack(fill="both", expand=True)
        tk.Label(
            content, text="!", bg=THEME.state_icon_background,
            fg=THEME.state_icon_foreground, font=THEME.font_icon, width=2,
        ).pack(side="left", anchor="n", padx=(0, 12))
        details = tk.Frame(content, bg=THEME.state_panel)
        details.pack(side="left", fill="both", expand=True)
        tk.Label(
            details, text=title, bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            details, text=message, bg=THEME.state_panel, fg=THEME.muted,
            font=THEME.font_body, wraplength=width - 2 * (18 + THEME.layout.alert_dialog_padding) - 60,
            justify="left",
        ).pack(anchor="w")
        actions = tk.Frame(panel, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(16, 0))
        self.dismiss_button = make_button(
            actions, "Entendi", "primary", pady=8, command=self.dismiss,
        )
        self.dismiss_button.pack(side="right")

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.alert_dialog_size
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _dismiss_event(self, _event=None):
        self.dismiss()
        return "break"

    def dismiss(self):
        """Fecha o alerta pelo botão, Escape, Enter ou controle da janela."""
        self.window.destroy()


def show_alert(parent, title: str, message: str) -> None:
    """Mostra um alerta modal seguindo o tema da interface."""
    dialog = AlertDialog(parent, title, message)
    parent.wait_window(dialog.window)


class TextInputDialog:
    """Pede um texto em modal próprio e devolve None quando cancelado."""

    def __init__(self, parent, title: str, prompt: str):
        self.result = None
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title(title)
        self.window.configure(bg=THEME.paper)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self._build_content(prompt)
        self.window.bind("<Return>", self._submit_event)
        self.window.bind("<Escape>", self._cancel_event)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._center_on_parent(parent)
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.text_entry.focus_set)

    def _build_content(self, prompt: str):
        width, height = THEME.layout.text_dialog_size
        panel = tk.Frame(
            self.window, bg=THEME.state_panel, padx=THEME.layout.text_dialog_padding,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(
            panel, text=self.window.title(), bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            panel, text=prompt, bg=THEME.state_panel, fg=THEME.muted,
            font=THEME.font_body, wraplength=width - 2 * THEME.layout.text_dialog_padding,
            justify="left",
        ).pack(anchor="w", pady=(0, 16))
        self.text_entry = tk.Entry(
            panel, bg=THEME.panel, fg=THEME.ink, insertbackground=THEME.green,
            highlightbackground=THEME.field_border, highlightcolor=THEME.green,
            highlightthickness=THEME.layout.highlight_thickness, relief="flat",
            font=THEME.font_body,
        )
        self.text_entry.pack(fill="x", ipady=7)
        self._build_actions(panel)

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(22, 0))
        actions.columnconfigure(0, weight=1)
        make_button(actions, "Cancelar", "secondary", pady=8, command=self.cancel).grid(
            row=0, column=0, sticky="e", padx=(0, 8),
        )
        make_button(actions, "Criar", "primary", pady=8, command=self.submit).grid(
            row=0, column=1, sticky="e",
        )

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.text_dialog_size
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def _submit_event(self, _event=None):
        self.submit()
        return "break"

    def _cancel_event(self, _event=None):
        self.cancel()
        return "break"

    def submit(self):
        self.result = self.text_entry.get()
        self.window.destroy()

    def cancel(self):
        self.window.destroy()


def ask_text(parent, title: str, prompt: str) -> str | None:
    """Mostra entrada de texto modal; retorna None se for cancelada."""
    dialog = TextInputDialog(parent, title, prompt)
    parent.wait_window(dialog.window)
    return dialog.result


class PathDialog:
    """Navega diretórios e seleciona um caminho sem abrir painéis do sistema."""

    def __init__(self, parent, mode: Literal["open", "save"], initialdir: Path,
                 allowed_root: Path | None = None):
        self.mode = mode
        self.result = None
        self.allowed_root = self._resolved_directory(allowed_root) if allowed_root else None
        self.directory = self._initial_directory(initialdir)
        self.path_items = []
        self.show_all_files = False
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Abrir base" if mode == "open" else "Criar base")
        self.window.configure(bg=THEME.paper)
        self.window.resizable(True, True)
        self.window.transient(parent)
        self._build_content()
        self.window.bind("<Return>", self._submit_event)
        self.window.bind("<Escape>", self._cancel_event)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._center_on_parent(parent)
        self._refresh_items()
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.name_entry.focus_set)

    def _build_content(self):
        width, height = THEME.layout.path_dialog_size
        panel = tk.Frame(
            self.window, bg=THEME.state_panel, padx=THEME.layout.path_dialog_padding,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(
            panel, text=self.window.title(), bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 10))
        self._build_location_row(panel)
        self._build_file_list(panel)
        self._build_filename_row(panel)
        self._build_actions(panel)
        self.window.minsize(width, height)

    def _build_location_row(self, parent):
        row = tk.Frame(parent, bg=THEME.state_panel)
        row.pack(fill="x", pady=(0, 10))
        tk.Label(
            row, text="Pasta", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(side="left", padx=(0, 8))
        self.location_entry = tk.Entry(
            row, bg=THEME.panel, fg=THEME.ink, insertbackground=THEME.green,
            font=THEME.font_body, relief="flat",
        )
        self.location_entry.pack(side="left", fill="x", expand=True, ipady=5)
        self.location_entry.bind("<Return>", self._go_to_location_event)
        make_button(row, "Ir", "secondary", pady=5, command=self._go_to_location).pack(
            side="left", padx=(8, 0),
        )
        if self.mode == "open":
            self.filter_button = make_button(
                row, "Bases .cpv", "secondary", pady=5, command=self._toggle_file_filter,
            )
            self.filter_button.pack(side="left", padx=(8, 0))

    def _build_file_list(self, parent):
        area = tk.Frame(parent, bg=THEME.state_panel)
        area.pack(fill="both", expand=True)
        self.file_list = tk.Listbox(
            area, bg=THEME.panel, fg=THEME.ink,
            selectbackground=THEME.selected_navigation_background,
            selectforeground=THEME.selected_navigation_foreground,
            font=THEME.font_body, relief="flat",
            highlightbackground=THEME.field_border,
            highlightcolor=THEME.green, highlightthickness=THEME.layout.highlight_thickness,
        )
        scrollbar = tk.Scrollbar(area, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        self.file_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.file_list.bind("<<ListboxSelect>>", self._select_item)
        self.file_list.bind("<Double-Button-1>", self._activate_item)

    def _build_filename_row(self, parent):
        row = tk.Frame(parent, bg=THEME.state_panel)
        row.pack(fill="x", pady=(10, 0))
        tk.Label(
            row, text="Nome", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(side="left", padx=(0, 8))
        self.name_entry = tk.Entry(
            row, bg=THEME.panel, fg=THEME.ink, insertbackground=THEME.green,
            font=THEME.font_body, relief="flat",
        )
        self.name_entry.pack(side="left", fill="x", expand=True, ipady=5)

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(12, 0))
        make_button(actions, "Cancelar", "secondary", pady=7, command=self.cancel).pack(side="right", padx=(8, 0))
        label = "Abrir" if self.mode == "open" else "Criar"
        make_button(actions, label, "primary", pady=7, command=self.submit).pack(side="right")

    def _refresh_items(self):
        self.location_entry.delete(0, "end")
        self.location_entry.insert(0, str(self.directory))
        self.file_list.delete(0, "end")
        try:
            entries = list(self.directory.iterdir())
        except OSError:
            show_alert(self.window, "Pasta indisponível", "Não foi possível listar esta pasta.")
            self.path_items = []
            return
        directories = sorted((item for item in entries if item.is_dir()), key=lambda item: item.name.casefold())
        files = sorted((item for item in entries if item.is_file()), key=lambda item: item.name.casefold())
        if self.mode == "open" and not self.show_all_files:
            files = [item for item in files if item.suffix.casefold() == ".cpv"]
        self.path_items = directories + files
        for item in self.path_items:
            label = f"[Pasta] {item.name}" if item.is_dir() else item.name
            self.file_list.insert("end", label)

    def _selected_path(self):
        selection = self.file_list.curselection()
        if not selection:
            return None
        index = selection[0]
        return self.path_items[index] if index < len(self.path_items) else None

    def _select_item(self, _event=None):
        selected = self._selected_path()
        if selected is not None and selected.is_file():
            self._set_name(selected.name)

    def _activate_item(self, _event=None):
        selected = self._selected_path()
        if selected is None:
            return "break"
        if selected.is_dir():
            self._navigate(selected)
        elif self.mode == "open":
            self._set_name(selected.name)
            self.submit()
        return "break"

    def _set_name(self, name: str):
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, name)

    def _navigate(self, path: Path):
        try:
            target = path.expanduser().resolve(strict=True)
            if not target.is_dir() or not self._is_allowed(target):
                raise ValueError
        except (OSError, RuntimeError, ValueError):
            show_alert(self.window, "Pasta indisponível", "Escolha uma pasta acessível dentro do perfil atual.")
            return False
        self.directory = target
        self._refresh_items()
        return True

    def _go_to_location(self):
        return self._navigate(Path(self.location_entry.get().strip()))

    def _go_to_location_event(self, _event=None):
        self._go_to_location()
        return "break"

    def _toggle_file_filter(self):
        self.show_all_files = not self.show_all_files
        label = "Todos os arquivos" if self.show_all_files else "Bases .cpv"
        self.filter_button.configure(text=label)
        self._refresh_items()

    def _candidate_path(self):
        name = self.name_entry.get().strip()
        if not name:
            show_alert(self.window, "Nome necessário", "Selecione um arquivo ou informe um nome.")
            return None
        candidate = Path(name).expanduser()
        if self.mode == "save" and candidate.name != name:
            show_alert(self.window, "Nome inválido", "Informe apenas o nome do arquivo nesta pasta.")
            return None
        if not candidate.is_absolute():
            candidate = self.directory / candidate
        try:
            resolved = candidate.resolve(strict=self.mode == "open")
            if not self._is_allowed(resolved):
                raise ValueError
            if self.mode == "open":
                if not resolved.is_file():
                    raise ValueError
                if not self.show_all_files and resolved.suffix.casefold() != ".cpv":
                    raise ValueError
            else:
                if resolved.parent != self.directory or not resolved.parent.is_dir():
                    raise ValueError
                if not resolved.suffix:
                    resolved = resolved.with_suffix(".cpv")
        except (OSError, RuntimeError, ValueError):
            show_alert(self.window, "Caminho inválido", "Escolha um arquivo permitido nesta pasta.")
            return None
        return resolved

    def _is_allowed(self, path: Path) -> bool:
        if self.allowed_root is None:
            return True
        return path == self.allowed_root or self.allowed_root in path.parents

    def submit(self):
        self.result = self._candidate_path()
        if self.result is not None:
            self.window.destroy()

    def _submit_event(self, _event=None):
        self.submit()
        return "break"

    def _cancel_event(self, _event=None):
        self.cancel()
        return "break"

    def cancel(self):
        self.window.destroy()

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.path_dialog_size
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    @staticmethod
    def _initial_directory(initialdir: Path) -> Path:
        try:
            candidate = Path(initialdir).expanduser().resolve(strict=True)
            return candidate if candidate.is_dir() else Path.home().resolve()
        except (OSError, RuntimeError):
            return Path.home().resolve()

    @staticmethod
    def _resolved_directory(directory: Path) -> Path:
        return Path(directory).expanduser().resolve(strict=True)


def ask_path(parent, mode: Literal["open", "save"], initialdir: Path,
             allowed_root: Path | None = None) -> Path | None:
    """Mostra navegador de caminhos do app e retorna Path ou None ao cancelar."""
    dialog = PathDialog(parent, mode, initialdir, allowed_root)
    parent.wait_window(dialog.window)
    return dialog.result


class ChoiceDialog:
    """Oferece opções em uma lista modal que segue o tema do aplicativo."""

    def __init__(self, parent, title: str, prompt: str, options: list[tuple[str, str]], selected_id):
        self.result = None
        self.options = list(options)
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title(title)
        self.window.configure(bg=THEME.paper)
        self.window.resizable(True, True)
        self.window.transient(parent)
        self._build_content(prompt, selected_id)
        self.window.bind("<Return>", self._choose_event)
        self.window.bind("<Escape>", self._cancel_event)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._center_on_parent(parent)
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.option_list.focus_set)

    def _build_content(self, prompt: str, selected_id):
        panel = tk.Frame(
            self.window, bg=THEME.state_panel, padx=THEME.layout.choice_dialog_padding,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(
            panel, text=self.window.title(), bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            panel, text=prompt, bg=THEME.state_panel, fg=THEME.muted,
            font=THEME.font_body, wraplength=360, justify="left",
        ).pack(anchor="w", pady=(0, 12))
        self._build_option_list(panel, selected_id)
        self._build_actions(panel)

    def _build_option_list(self, parent, selected_id):
        area = tk.Frame(parent, bg=THEME.state_panel)
        area.pack(fill="both", expand=True)
        self.option_list = tk.Listbox(
            area, bg=THEME.panel, fg=THEME.ink,
            selectbackground=THEME.selected_navigation_background,
            selectforeground=THEME.selected_navigation_foreground,
            font=THEME.font_body, relief="flat",
            highlightbackground=THEME.field_border,
            highlightcolor=THEME.green, highlightthickness=THEME.layout.highlight_thickness,
        )
        scrollbar = tk.Scrollbar(area, orient="vertical", command=self.option_list.yview)
        self.option_list.configure(yscrollcommand=scrollbar.set)
        self.option_list.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.selected_index = 0
        for index, (identifier, label) in enumerate(self.options):
            self.option_list.insert("end", label)
            if identifier == selected_id:
                self.selected_index = index
        if self.options:
            self.option_list.selection_set(self.selected_index)
            self.option_list.see(self.selected_index)
        self.option_list.bind("<Double-Button-1>", self._choose_event)

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(12, 0))
        make_button(actions, "Cancelar", "secondary", pady=7, command=self.cancel).pack(
            side="right", padx=(8, 0),
        )
        make_button(actions, "Escolher", "primary", pady=7, command=self.choose).pack(side="right")

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.choice_dialog_size
        self.window.geometry(f"{width}x{height}")
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def choose(self):
        selection = self.option_list.curselection()
        if selection and selection[0] < len(self.options):
            self.result = self.options[selection[0]][0]
            self.window.destroy()

    def _choose_event(self, _event=None):
        self.choose()
        return "break"

    def _cancel_event(self, _event=None):
        self.cancel()
        return "break"

    def cancel(self):
        self.window.destroy()


def ask_choice(parent, title: str, prompt: str, options: list[tuple[str, str]], selected_id):
    """Mostra seletor modal próprio e retorna o identificador ou None ao cancelar."""
    dialog = ChoiceDialog(parent, title, prompt, options, selected_id)
    parent.wait_window(dialog.window)
    return dialog.result


class FilterDialog:
    """Seleciona coleção e hashtag em um modal estilizado do aplicativo."""

    def __init__(self, parent, collections, tags, selected_collection, selected_tag):
        self.result = None
        self.collection_options = [(None, "Todas as coleções"), *collections]
        self.tag_options = [(None, "Todas as hashtags"), *((tag, tag) for tag in tags)]
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Filtrar notas")
        self.window.configure(bg=THEME.paper)
        self.window.resizable(False, False)
        self.window.transient(parent)
        self._build_content(selected_collection, selected_tag)
        self.window.bind("<Return>", self._apply_event)
        self.window.bind("<Escape>", self._cancel_event)
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self._center_on_parent(parent)
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.collection_list.focus_set)

    def _build_content(self, selected_collection, selected_tag):
        width, height = THEME.layout.filter_dialog_size
        panel = tk.Frame(
            self.window, bg=THEME.state_panel, padx=THEME.layout.filter_dialog_padding,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(
            panel, text="Filtrar notas", bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 12))
        self.collection_list = self._build_picker(
            panel, "Coleção", self.collection_options, selected_collection,
        )
        self.tag_list = self._build_picker(panel, "Hashtag", self.tag_options, selected_tag)
        self._build_actions(panel)
        self.window.geometry(f"{width}x{height}")
        self.window.minsize(width, height)

    def _build_picker(self, parent, title, options, selected_value):
        group = tk.Frame(parent, bg=THEME.state_panel)
        group.pack(fill="both", expand=True, pady=(0, 10))
        tk.Label(
            group, text=title, bg=THEME.state_panel, fg=THEME.ink, font=THEME.font_label,
        ).pack(anchor="w", pady=(0, 4))
        area = tk.Frame(group, bg=THEME.state_panel)
        area.pack(fill="both", expand=True)
        items = tk.Listbox(
            area, bg=THEME.panel, fg=THEME.ink,
            selectbackground=THEME.selected_navigation_background,
            selectforeground=THEME.selected_navigation_foreground,
            font=THEME.font_body, relief="flat",
            highlightbackground=THEME.field_border, highlightcolor=THEME.green,
            highlightthickness=THEME.layout.highlight_thickness,
        )
        scrollbar = tk.Scrollbar(area, orient="vertical", command=items.yview)
        items.configure(yscrollcommand=scrollbar.set)
        items.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        selected_index = 0
        for index, (value, label) in enumerate(options):
            items.insert("end", label)
            if value == selected_value:
                selected_index = index
        items.selection_set(selected_index)
        items.see(selected_index)
        return items

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(4, 0))
        make_button(actions, "Cancelar", "secondary", pady=8, command=self.cancel).pack(
            side="right", padx=(8, 0),
        )
        make_button(actions, "Aplicar", "primary", pady=8, command=self.apply).pack(side="right")

    def apply(self):
        collection = self._selected_value(self.collection_list, self.collection_options)
        tag = self._selected_value(self.tag_list, self.tag_options)
        self.result = collection, tag
        self.window.destroy()

    @staticmethod
    def _selected_value(listbox, options):
        selection = listbox.curselection()
        index = selection[0] if selection and selection[0] < len(options) else 0
        return options[index][0]

    def _apply_event(self, _event=None):
        self.apply()
        return "break"

    def _cancel_event(self, _event=None):
        self.cancel()
        return "break"

    def cancel(self):
        self.window.destroy()

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.filter_dialog_size
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")


def ask_filters(parent, collections, tags, selected_collection, selected_tag):
    """Abre o modal de filtros e retorna as escolhas ou None ao cancelar."""
    dialog = FilterDialog(parent, collections, tags, selected_collection, selected_tag)
    parent.wait_window(dialog.window)
    return dialog.result


class UnsavedChangesDialog:
    """Pede uma decisão explícita antes de descartar um rascunho alterado."""

    def __init__(self, parent):
        self.result = "cancel"
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.title("Alterações não salvas")
        self.window.configure(bg=THEME.paper)
        self.window.resizable(False, False)
        self.window.transient(parent)
        width, height = THEME.layout.unsaved_dialog_size
        self.window.geometry(f"{width}x{height}")
        panel = tk.Frame(
            self.window, bg=THEME.state_panel, padx=THEME.layout.unsaved_dialog_padding, pady=20,
        )
        panel.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(
            panel, text="Este rascunho tem alterações.", bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            panel, text="Salve antes de continuar ou descarte o que ainda não foi salvo.",
            bg=THEME.state_panel, fg=THEME.muted, font=THEME.font_body,
            wraplength=width - 2 * (18 + THEME.layout.unsaved_dialog_padding), justify="left",
        ).pack(anchor="w")
        self._build_actions(panel)
        self.window.bind("<Return>", lambda _event: self.choose("save"))
        self.window.bind("<Command-s>", lambda _event: self.choose("save"))
        self.window.bind("<Escape>", lambda _event: self.choose("cancel"))
        self.window.bind("<Command-BackSpace>", lambda _event: self.choose("discard"))
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.choose("cancel"))
        self._center_on_parent(parent)
        self.window.deiconify()
        self.window.grab_set()
        self.window.after_idle(self.save_button.focus_set)

    def _build_actions(self, parent):
        actions = tk.Frame(parent, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(24, 0))
        actions.columnconfigure(0, weight=1)
        self.save_button = make_button(
            actions, "Salvar  ⌘S", "primary", pady=8, command=lambda: self.choose("save"),
        )
        discard_button = make_button(
            actions, "Descartar  ⌘⌫", "secondary", pady=8, command=lambda: self.choose("discard"),
        )
        cancel_button = make_button(
            actions, "Cancelar  Esc", "secondary", pady=8, command=lambda: self.choose("cancel"),
        )
        self.save_button.grid(row=0, column=0, sticky="e", padx=(0, 8))
        discard_button.grid(row=0, column=1, sticky="e", padx=(0, 8))
        cancel_button.grid(row=0, column=2, sticky="e")

    def _center_on_parent(self, parent):
        self.window.update_idletasks()
        width, height = THEME.layout.unsaved_dialog_size
        x = parent.winfo_rootx() + max((parent.winfo_width() - width) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - height) // 2, 0)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

    def choose(self, result: str):
        self.result = result
        self.window.destroy()


def ask_unsaved_changes(parent) -> str:
    """Devolve save, discard ou cancel depois de uma escolha explícita."""
    dialog = UnsavedChangesDialog(parent)
    parent.wait_window(dialog.window)
    return dialog.result


class CadernoApp:
    """Coordena o ciclo de abertura e fechamento do cofre pela interface."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.session: VaultSession | None = None
        self.active_entry_id = None
        self.saved_title = ""
        self.saved_body = ""
        self.saved_collection_id = None
        self.saved_tags = []
        self.collection_id_by_label = {}
        self.collection_filter_id = None
        self.tag_filter = None
        self.editor_metadata_ready = False
        root.title("Caderno de Pensamentos")
        root.geometry(f"{THEME.layout.window_size[0]}x{THEME.layout.window_size[1]}")
        root.minsize(*THEME.layout.minimum_window_size)
        root.configure(bg=THEME.paper)
        root.protocol("WM_DELETE_WINDOW", self.close_app)
        configure_fonts()
        shell = tk.Frame(root, bg=THEME.paper)
        shell.pack(fill="both", expand=True)
        build_sidebar(shell, self)
        build_main_panel(shell, self)
        self.show_locked()
        self._restore_binding = root.bind("<Map>", self._restore_after_map, add="+")

    def _restore_after_map(self, event):
        """Só inicia a restauração depois que a janela principal foi mapeada."""
        if event.widget is not self.root:
            return
        self.root.unbind("<Map>", self._restore_binding)
        self.root.after_idle(self.restore_last_vault)

    def create(self):
        """Pede destino e senha, cria cofre vazio e só então lembra o caminho."""
        profile = os.environ.get("CADERNO_UI_TEST_PROFILE")
        initialdir = Path(profile) if profile else Path.home()
        target = ask_path(self.root, "save", initialdir, Path(profile) if profile else None)
        if target is None:
            return
        if not self._path_allowed_in_test_profile(target):
            show_alert(
                self.root,
                "Arquivo fora da pasta de teste",
                "No perfil de teste, crie a base dentro da pasta de teste indicada no Terminal.",
            )
            return
        if target.exists():
            show_alert(self.root, "Não foi possível criar", "Já existe um arquivo nesse local.")
            return
        password = ask_password(self.root, "Criar base", "Escolha uma senha para esta base.", "Continuar")
        if password is None:
            return
        confirmation = ask_password(
            self.root, "Confirmar senha", "Digite a senha novamente para confirmar.", "Confirmar"
        )
        if confirmation is None:
            return
        if not password or password != confirmation:
            show_alert(self.root, "Não foi possível criar", "A senha está vazia ou as confirmações não coincidem.")
            return
        if not self._confirm_pending_changes():
            return
        document = {
            "schema_version": 1,
            "collections": [{"id": "default", "name": "Geral"}],
            "attachments": [],
            "entries": [],
        }
        try:
            session = create_vault(target, password, VaultSnapshot(document))
        except FileExistsError:
            show_alert(self.root, "Não foi possível criar", "Já existe um arquivo nesse local.")
            return
        except DurabilityUncertainError:
            show_alert(
                self.root,
                "Gravação incerta",
                "O arquivo pode ter sido criado, mas não foi possível confirmar sua gravação. "
                "Não tente sobrescrevê-lo; escolha-o e tente abri-lo para validar.",
            )
            return
        except Exception:
            show_alert(self.root, "Não foi possível criar", "Verifique o local escolhido e tente novamente.")
            return
        self._activate(session)
        self._remember_path(target)

    def choose(self):
        """Seleciona um arquivo de cofre e solicita a senha sem persistí-la."""
        profile = os.environ.get("CADERNO_UI_TEST_PROFILE")
        initialdir = Path(profile) if profile else Path.home()
        target = ask_path(self.root, "open", initialdir, Path(profile) if profile else None)
        if target is not None:
            self.unlock(target)

    def unlock(self, path: Path):
        """Abre um cofre; mensagens de falha não revelam detalhes internos do arquivo."""
        if not self._path_allowed_in_test_profile(path):
            show_alert(
                self.root,
                "Arquivo fora da pasta de teste",
                "No perfil de teste, escolha um arquivo dentro da pasta de teste indicada no Terminal.",
            )
            return
        if self._is_current_vault(path):
            return
        password = ask_password(self.root, "Abrir base", "Digite a senha desta base para desbloqueá-la.", "Abrir base")
        if password is None:
            return
        try:
            session = open_vault(path, password)
        except Exception:
            show_alert(
                self.root,
                "Não foi possível abrir a base",
                "A senha pode estar incorreta ou o arquivo pode estar inválido ou indisponível.",
            )
            return
        if not self._confirm_pending_changes():
            session.close()
            return
        self._activate(session)
        self._remember_path(path)

    def _is_current_vault(self, path: Path) -> bool:
        if self.session is None:
            return False
        try:
            return Path(path).expanduser().resolve(strict=False) == self.session.path
        except (AttributeError, OSError, RuntimeError):
            return False

    @staticmethod
    def _path_allowed_in_test_profile(path: Path) -> bool:
        """Restringe cofres ao perfil descartável quando o launcher de UI está ativo."""
        profile = os.environ.get("CADERNO_UI_TEST_PROFILE")
        if not profile:
            return True
        try:
            root = Path(profile).expanduser().resolve()
            target = Path(path).expanduser().resolve()
            return target != root and target.is_relative_to(root)
        except (OSError, RuntimeError):
            return False

    def _remember_path(self, path: Path):
        try:
            save_last_vault(path)
        except OSError:
            show_alert(self.root, "Base aberta", "A base está aberta, mas não foi possível lembrar este caminho.")

    def _activate(self, session: VaultSession):
        if self.session is not None:
            self.session.close()
        self.session = session
        self._reset_search_for_locked_view()
        self.active_entry_id = self._first_entry_id(session.snapshot.document)
        self.show_unlocked(session)

    def show_locked(self):
        self.status.configure(text="●  Nenhuma base aberta", fg=THEME.locked_status)
        self.status_detail.configure(text="Escolha ou crie uma base para começar")
        self.title_entry = None
        self.body_editor = None
        self.editor_metadata_ready = False
        self.new_entry_button.configure(state="disabled")
        self.collection_add_button.configure(state="disabled")
        self.welcome_area.pack(fill="x", before=self.summary_area)
        self.search_area.pack(fill="x", before=self.state_area)
        self._reset_search_for_locked_view()
        self.close_button.pack_forget()
        self.update_summary(None)
        self.render_state(
            "Seu caderno começa com uma ideia.",
            "Abra ou crie uma base criptografada para começar.",
            ("Escolher base", self.choose, "primary"),
            ("Criar base", self.create, "primary"),
        )
        self._render_collection_list()

    def show_unlocked(self, session: VaultSession):
        self.status.configure(text="●  Base aberta", fg=THEME.green)
        self.status_detail.configure(text=session.path.name)
        self.new_entry_button.configure(state="normal")
        self.collection_add_button.configure(state="normal")
        self.welcome_area.pack_forget()
        self.search_area.pack(fill="x", before=self.state_area)
        search_entry = getattr(self, "search_entry", None)
        if search_entry is not None:
            search_entry.configure(state="normal")
        filter_button = getattr(self, "filter_button", None)
        if filter_button is not None:
            filter_button.configure(state="normal")
        self.close_button.pack(fill="x", padx=8, pady=(8, 0))
        self.update_summary(session.snapshot.document)
        self._render_collection_list()
        self.refresh_notes()

    @staticmethod
    def _first_entry_id(document):
        entries = sorted(document["entries"], key=lambda entry: entry["updated_at"], reverse=True)
        return entries[0]["id"] if entries else None

    def refresh_notes(self):
        """Renderiza a lista e o editor para o snapshot da sessão ativa."""
        for child in self.state_area.winfo_children():
            child.destroy()
        layout = tk.Frame(self.state_area, bg=THEME.state_panel)
        layout.pack(fill="both", expand=True)
        list_panel = tk.Frame(layout, bg=THEME.state_panel, width=THEME.layout.notes_list_width)
        list_panel.pack(side="left", fill="y", padx=(0, THEME.layout.notes_list_gap))
        list_panel.pack_propagate(False)
        tk.Label(
            list_panel, text="NOTAS", bg=THEME.state_panel,
            fg=THEME.muted, font=THEME.font_mono_small,
        ).pack(anchor="w", pady=(0, 8))
        self._render_note_list(list_panel)
        self.editor_panel = tk.Frame(layout, bg=THEME.state_panel)
        self.editor_panel.pack(side="left", fill="both", expand=True)
        entry = self._active_entry()
        self._render_note_editor(entry)

    def _reset_search_for_locked_view(self):
        """Limpa a busca ao fechar a base e desativa o campo bloqueado."""
        self.search_query = ""
        self.collection_filter_id = None
        self.tag_filter = None
        filter_button = getattr(self, "filter_button", None)
        if filter_button is not None:
            filter_button.configure(text="Filtrar ▾", state="disabled")
        search_entry = getattr(self, "search_entry", None)
        if search_entry is None:
            return
        search_entry.configure(state="normal")
        search_entry.delete(0, "end")
        search_entry.insert(0, self.search_placeholder)
        search_entry.configure(fg=THEME.muted, state="disabled")
        self.search_placeholder_visible = True

    def _search_focus_in(self, _event=None):
        if not getattr(self, "search_placeholder_visible", False):
            return
        self.search_entry.delete(0, "end")
        self.search_entry.configure(fg=THEME.ink)
        self.search_placeholder_visible = False

    def _search_focus_out(self, _event=None):
        if self.search_entry.get().strip():
            return
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, self.search_placeholder)
        self.search_entry.configure(fg=THEME.muted)
        self.search_placeholder_visible = True
        self.set_search_query("")

    def _search_key_release(self, _event=None):
        if not self.search_placeholder_visible:
            self.set_search_query(self.search_entry.get())

    def _search_escape(self, _event=None):
        self.search_entry.delete(0, "end")
        self.set_search_query("")
        return "break"

    def set_search_query(self, query: str):
        """Atualiza o filtro em memória sem recriar o editor nem seus rascunhos."""
        self.search_query = query.strip().casefold()
        if getattr(self, "session", None) is not None and hasattr(self, "note_list"):
            self._populate_note_list()

    def choose_filters(self):
        """Abre filtros temporários de coleção e hashtag para a lista atual."""
        if self.session is None:
            return
        document = self.session.snapshot.document
        collections = [(item["id"], item["name"]) for item in document["collections"]]
        tags = self._available_tags(document)
        selection = ask_filters(
            self.root, collections, tags, self.collection_filter_id, self.tag_filter,
        )
        if selection is None:
            return
        self.collection_filter_id, self.tag_filter = selection
        self._update_filter_button()
        self._populate_note_list()

    @staticmethod
    def _available_tags(document):
        tags = {tag.casefold(): tag for entry in document["entries"] for tag in entry["tags"]}
        return sorted(tags.values(), key=str.casefold)

    def _update_filter_button(self):
        active = int(self.collection_filter_id is not None) + int(self.tag_filter is not None)
        label = f"Filtros ({active}) ▾" if active else "Filtrar ▾"
        self.filter_button.configure(text=label)

    def _matching_entries(self):
        document = self.session.snapshot.document
        collections = {item["id"]: item["name"] for item in document["collections"]}
        entries = sorted(document["entries"], key=lambda item: item["updated_at"], reverse=True)
        return [
            entry for entry in entries
            if self._entry_matches_query(entry, collections, self.search_query)
            and self._entry_matches_filters(entry)
        ]

    @staticmethod
    def _entry_matches_query(entry, collections, query: str) -> bool:
        if not query:
            return True
        collection = collections.get(entry["collection_id"], "")
        searchable = " ".join((
            entry["title"], entry["body_markdown"], collection, *entry["tags"],
        )).casefold()
        return all(term in searchable for term in query.split())

    def _entry_matches_filters(self, entry) -> bool:
        if self.collection_filter_id and entry["collection_id"] != self.collection_filter_id:
            return False
        tags = {tag.casefold() for tag in entry["tags"]}
        return self.tag_filter is None or self.tag_filter.casefold() in tags

    def _populate_note_list(self):
        entries = self._matching_entries()
        self.note_list.delete(0, "end")
        self.note_entry_ids = [entry["id"] for entry in entries]
        for entry in entries:
            self.note_list.insert("end", entry["title"])
        if not entries and (self.search_query or self.collection_filter_id or self.tag_filter):
            self.note_list.insert("end", "Nenhuma nota encontrada")
        if self.active_entry_id in self.note_entry_ids:
            index = self.note_entry_ids.index(self.active_entry_id)
            self.note_list.selection_set(index)
            self.note_list.see(index)

    def _active_entry(self):
        if self.session is None or self.active_entry_id is None:
            return None
        return next(
            (entry for entry in self.session.snapshot.document["entries"]
             if entry["id"] == self.active_entry_id),
            None,
        )

    def add_collection(self):
        """Pede um nome e persiste uma coleção sem alterar notas existentes."""
        if self.session is None or not self._confirm_pending_changes():
            return False
        name = ask_text(self.root, "Nova coleção", "Nome da coleção:")
        if name is None:
            return False
        name = name.strip()
        if not name or len(name) > 4096:
            show_alert(self.root, "Nome inválido", "Informe um nome de até 4096 caracteres.")
            return False
        current_snapshot = self.session.snapshot
        document = current_snapshot.document
        if any(item["name"].casefold() == name.casefold() for item in document["collections"]):
            show_alert(self.root, "Coleção existente", f"Já existe uma coleção chamada “{name}”.")
            return False
        document["collections"].append({"id": str(uuid4()), "name": name})
        try:
            snapshot = VaultSnapshot(document, current_snapshot.attachments)
            self.session.save(snapshot)
        except DurabilityUncertainError:
            self.update_summary(self.session.snapshot.document)
            self._render_collection_list()
            self.refresh_notes()
            show_alert(self.root, "Gravação incerta", "A coleção está visível na base; confira o arquivo antes de fechar.")
            return False
        except Exception:
            show_alert(self.root, "Não foi possível criar", "A coleção não foi salva. A base pode ter mudado ou estar indisponível.")
            return False
        self.update_summary(self.session.snapshot.document)
        self._render_collection_list()
        self.refresh_notes()
        return True

    def _render_collection_list(self):
        """Mostra as coleções da sessão atual ou o estado vazio da barra lateral."""
        area = getattr(self, "collection_items", None)
        if area is None:
            return
        for child in area.winfo_children():
            child.destroy()
        collections = self.session.snapshot.document["collections"] if self.session else []
        if not collections:
            tk.Label(
                area, text="Suas coleções aparecerão aqui", bg=THEME.sidebar, fg=THEME.muted,
                anchor="w", padx=10, pady=8, font=THEME.font_label,
            ).pack(fill="x")
            return
        for collection in collections:
            tk.Label(
                area, text=collection["name"], bg=THEME.sidebar, fg=THEME.ink,
                anchor="w", padx=10, pady=5, font=THEME.font_label,
            ).pack(fill="x")

    @staticmethod
    def _parse_tags(value: str) -> list[str]:
        """Converte hashtags separadas por vírgula em nomes únicos sem `#`."""
        tags = []
        for part in value.split(","):
            tag = part.strip().lstrip("#").strip()
            if tag and tag not in tags:
                tags.append(tag)
        return tags

    def _editor_metadata(self):
        if not self.editor_metadata_ready:
            entry = self._active_entry()
            if entry:
                return entry["collection_id"], list(entry["tags"])
            collections = self.session.snapshot.document["collections"] if self.session else []
            return (collections[0]["id"] if collections else None), []
        label = self.collection_choice.get()
        collection_id = self.collection_id_by_label.get(label, label)
        tags = self._parse_tags(self.tags_entry.get())
        collections = self.session.snapshot.document["collections"]
        available_ids = {item["id"] for item in collections}
        if collection_id not in available_ids:
            entry = self._active_entry()
            collection_id = entry["collection_id"] if entry else None
            if collection_id is None and collections:
                collection_id = collections[0]["id"]
        return collection_id, tags

    def choose_collection(self):
        """Atualiza a coleção do rascunho sem persistir antes do salvamento da nota."""
        selected_id = self.collection_id_by_label.get(self.collection_choice.get())
        collection_id = ask_choice(
            self.root, "Coleção da nota", "Escolha uma coleção para esta nota.",
            self.collection_options, selected_id,
        )
        if collection_id is None:
            return
        label = next(label for label, identifier in self.collection_options if identifier == collection_id)
        self.collection_choice.set(label)
        self.collection_selector.configure(text=label)

    def _render_note_list(self, parent):
        listbox = tk.Listbox(
            parent, bg=THEME.panel, fg=THEME.ink, selectbackground=THEME.selected_navigation_background,
            selectforeground=THEME.selected_navigation_foreground, font=THEME.font_body,
            relief="flat", highlightbackground=THEME.field_border,
            highlightcolor=THEME.green, highlightthickness=THEME.layout.highlight_thickness,
        )
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        listbox.bind("<<ListboxSelect>>", self._select_list_entry)
        self.note_list = listbox
        self._populate_note_list()

    def _render_note_editor(self, entry):
        title = entry["title"] if entry else ""
        body = entry["body_markdown"] if entry else ""
        self.saved_title, self.saved_body = title, body
        self._initialize_editor_metadata(entry)
        self._render_title_field(title)
        self._render_metadata_fields()
        self._render_body_field(body)
        self._render_editor_actions()

    def _initialize_editor_metadata(self, entry):
        document = self.session.snapshot.document
        self.collection_options = self._collection_options(document)
        self.collection_id_by_label = dict(self.collection_options)
        collection_id = entry["collection_id"] if entry else self.collection_options[0][1]
        selected_label = next(
            (label for label, ident in self.collection_options if ident == collection_id),
            self.collection_options[0][0],
        )
        self.collection_choice = tk.StringVar(self.editor_panel, value=selected_label)
        self.saved_collection_id = collection_id
        self.saved_tags = list(entry["tags"]) if entry else []

    def _render_title_field(self, title):
        tk.Label(
            self.editor_panel, text="Título", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(anchor="w", pady=(0, 5))
        self.title_entry = tk.Entry(
            self.editor_panel, bg=THEME.panel, fg=THEME.ink,
            insertbackground=THEME.green, font=THEME.font_heading,
            relief="flat", highlightthickness=THEME.layout.highlight_thickness,
            highlightbackground=THEME.field_border, highlightcolor=THEME.green,
        )
        self.title_entry.pack(fill="x", pady=(0, 12), ipady=7)
        self.title_entry.insert(0, title)

    def _render_metadata_fields(self):
        options = self.collection_options
        selected_label = self.collection_choice.get()
        metadata = tk.Frame(self.editor_panel, bg=THEME.state_panel)
        metadata.pack(fill="x", pady=(0, 8))
        collection_column = tk.Frame(metadata, bg=THEME.state_panel)
        collection_column.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tags_column = tk.Frame(metadata, bg=THEME.state_panel)
        tags_column.pack(side="left", fill="x", expand=True)
        tk.Label(
            collection_column, text="Coleção", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(anchor="w", pady=(0, 4))
        self.collection_selector = make_button(
            collection_column, selected_label, "secondary", pady=5,
            command=self.choose_collection,
        )
        self.collection_selector.pack(fill="x")
        tk.Label(
            tags_column, text="Hashtags", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(anchor="w", pady=(0, 4))
        self.tags_entry = tk.Entry(
            tags_column, bg=THEME.panel, fg=THEME.ink, insertbackground=THEME.green,
            font=THEME.font_body, relief="flat",
            highlightthickness=THEME.layout.highlight_thickness,
            highlightbackground=THEME.field_border, highlightcolor=THEME.green,
        )
        self.tags_entry.pack(fill="x", ipady=4)
        self.tags_entry.insert(0, ", ".join(f"#{tag}" for tag in self.saved_tags))
        self.editor_metadata_ready = True

    def _render_body_field(self, body):
        tk.Label(
            self.editor_panel, text="Texto", bg=THEME.state_panel,
            fg=THEME.ink, font=THEME.font_label,
        ).pack(anchor="w", pady=(0, 5))
        body_frame = tk.Frame(self.editor_panel, bg=THEME.state_panel)
        body_frame.pack(fill="both", expand=True)
        self.body_editor = tk.Text(
            body_frame, bg=THEME.panel, fg=THEME.ink,
            insertbackground=THEME.green, font=THEME.font_text, height=8,
            wrap="word", undo=True, relief="flat",
            highlightthickness=THEME.layout.highlight_thickness,
            highlightbackground=THEME.field_border, highlightcolor=THEME.green,
        )
        self.body_editor.pack(side="left", fill="both", expand=True)
        body_scrollbar = tk.Scrollbar(body_frame, orient="vertical", command=self.body_editor.yview)
        body_scrollbar.pack(side="right", fill="y")
        self.body_editor.configure(yscrollcommand=body_scrollbar.set)
        self.body_editor.insert("1.0", body)
        for widget in (self.title_entry, self.tags_entry, self.collection_selector, self.body_editor):
            widget.bind("<Command-s>", self._save_shortcut)
            widget.bind("<Escape>", self._cancel_edit_shortcut)

    def _render_editor_actions(self):
        actions = tk.Frame(self.editor_panel, bg=THEME.state_panel)
        actions.pack(fill="x", pady=(12, 0))
        make_button(
            actions, "Salvar  ⌘S", "primary", pady=8, command=self.save_entry,
        ).pack(side="right")
        make_button(
            actions, "Descartar alterações", "secondary", pady=8,
            command=self.discard_editor_changes,
        ).pack(side="right", padx=(0, 8))

    @staticmethod
    def _collection_options(document):
        """Monta opções selecionáveis com rótulos únicos para cada coleção."""
        collections = document["collections"]
        if not collections:
            return [("Geral", None)]
        counts = {}
        for item in collections:
            counts[item["name"]] = counts.get(item["name"], 0) + 1
        options = []
        occurrences = {}
        used_labels = set()
        for item in collections:
            label = item["name"]
            if counts[label] > 1:
                occurrences[label] = occurrences.get(label, 0) + 1
                label = f"{label} · {occurrences[label]}"
            base_label = label
            suffix = 2
            while label in used_labels:
                label = f"{base_label} ({suffix})"
                suffix += 1
            used_labels.add(label)
            options.append((label, item["id"]))
        return options

    def _select_list_entry(self, _event=None):
        selection = self.note_list.curselection()
        if selection and selection[0] < len(self.note_entry_ids):
            self.select_entry(self.note_entry_ids[selection[0]])

    def _save_shortcut(self, _event=None):
        self.save_entry()
        return "break"

    def _cancel_edit_shortcut(self, _event=None):
        if self._has_pending_changes():
            choice = ask_unsaved_changes(self.root)
            if choice == "save":
                self.save_entry()
            elif choice == "discard":
                self.discard_editor_changes()
        return "break"

    def select_entry(self, entry_id):
        current_id = self.active_entry_id
        if not self._confirm_pending_changes():
            self.note_list.selection_clear(0, "end")
            if current_id in self.note_entry_ids:
                self.note_list.selection_set(self.note_entry_ids.index(current_id))
            return
        self.active_entry_id = entry_id
        self.refresh_notes()

    def new_entry(self):
        if self.session is None or not self._confirm_pending_changes():
            return
        self.active_entry_id = None
        self.refresh_notes()

    def _editor_values(self):
        return self.title_entry.get(), self.body_editor.get("1.0", "end-1c")

    def _has_pending_changes(self):
        if self.session is None:
            return False
        if any(getattr(self, name, None) is None for name in ("title_entry", "body_editor")):
            return False
        widgets = [self.title_entry, self.body_editor]
        if self.editor_metadata_ready:
            if getattr(self, "tags_entry", None) is None:
                return False
            widgets.append(self.tags_entry)
        for widget in widgets:
            if hasattr(widget, "winfo_exists"):
                try:
                    if not widget.winfo_exists():
                        return False
                except tk.TclError:
                    return False
        content_changed = self._editor_values() != (self.saved_title, self.saved_body)
        metadata_changed = self.editor_metadata_ready and (
            self._editor_metadata() != (self.saved_collection_id, self.saved_tags)
        )
        return content_changed or metadata_changed

    def _confirm_pending_changes(self):
        if not self._has_pending_changes():
            return True
        choice = ask_unsaved_changes(self.root)
        if choice == "save":
            return self.save_entry()
        if choice == "discard":
            self.discard_editor_changes()
            return True
        return False

    def discard_editor_changes(self):
        """Restaura o último conteúdo persistido ou limpa o rascunho novo."""
        self.refresh_notes()

    def save_entry(self):
        """Valida e persiste o editor como um novo snapshot, mantendo o rascunho em erro."""
        if self.session is None:
            return False
        if self.active_entry_id is not None and not self._has_pending_changes():
            return True
        title, body = self._editor_values()
        title = title.strip()
        if not title:
            show_alert(self.root, "Título necessário", "Dê um título à nota antes de salvar.")
            self.title_entry.focus_set()
            return False
        collection_id, tags = self._editor_metadata()
        if any(len(tag) > 256 for tag in tags):
            show_alert(self.root, "Hashtag inválida", "Cada hashtag pode ter até 256 caracteres.")
            self.tags_entry.focus_set()
            return False
        snapshot = self.session.snapshot
        document = snapshot.document
        entry = self._updated_entry(document, title, body, collection_id, tags)
        try:
            self.session.save(VaultSnapshot(document, snapshot.attachments))
        except DurabilityUncertainError:
            self._mark_entry_saved(entry, title, body)
            show_alert(
                self.root,
                "Gravação incerta",
                "A alteração está visível no arquivo, mas a confirmação de durabilidade falhou. "
                "Não repita a edição; confira a base antes de fechar o aplicativo.",
            )
            return False
        except Exception:
            show_alert(
                self.root,
                "Não foi possível salvar",
                "O rascunho continua no editor. A base pode ter mudado ou estar indisponível.",
            )
            return False
        self._mark_entry_saved(entry, title, body)
        return True

    def _updated_entry(self, document, title: str, body: str, collection_id, tags: list[str]):
        now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        if self.active_entry_id is None:
            collection_id = collection_id or self._default_collection(document)
            entry = {
                "id": str(uuid4()), "title": title, "body_markdown": body,
                "collection_id": collection_id, "tags": tags, "created_at": now,
                "updated_at": now, "published_at": None, "favorite": False, "attachments": [],
            }
            document["entries"].append(entry)
            return entry
        entry = next(item for item in document["entries"] if item["id"] == self.active_entry_id)
        entry["title"] = title
        entry["body_markdown"] = body
        entry["collection_id"] = collection_id or self._default_collection(document)
        entry["tags"] = tags
        entry["updated_at"] = now
        return entry

    @staticmethod
    def _default_collection(document):
        if document["collections"]:
            return document["collections"][0]["id"]
        collection_id = str(uuid4())
        document["collections"].append({"id": collection_id, "name": "Geral"})
        return collection_id

    def _mark_entry_saved(self, entry, title: str, body: str):
        self.active_entry_id = entry["id"]
        self.saved_title, self.saved_body = title, body
        self.saved_collection_id = entry["collection_id"]
        self.saved_tags = list(entry["tags"])
        self.update_summary(self.session.snapshot.document)
        self.refresh_notes()

    def update_summary(self, document):
        """Atualiza os contadores visíveis para corresponderem à base ativa."""
        if document is None:
            counts = (0, 0, 0)
        else:
            entries = document["entries"]
            today = datetime.now(timezone.utc).date()
            week_start = today - timedelta(days=today.weekday())
            recent = sum(
                week_start <= datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")).date() <= today
                for item in entries
            )
            counts = (len(entries), len(document["collections"]), recent)
        for label, value in zip(self.summary_values, counts):
            label.configure(text=str(value))

    def render_state(self, title: str, description: str, *actions):
        for child in self.state_area.winfo_children():
            child.destroy()
        tk.Label(
            self.state_area, text="✳", bg=THEME.state_icon_background,
            fg=THEME.state_icon_foreground, font=THEME.font_icon, width=3,
        ).pack(pady=(0, THEME.layout.state_icon_bottom_padding))
        tk.Label(
            self.state_area, text=title, bg=THEME.state_panel,
            fg=THEME.state_title, font=THEME.font_heading,
        ).pack()
        tk.Label(
            self.state_area, text=description, bg=THEME.state_panel, fg=THEME.muted,
            font=THEME.font_label,
            wraplength=THEME.layout.state_description_wrap,
        ).pack(pady=THEME.layout.state_description_padding)
        for label, callback, variant in actions:
            make_button(
                self.state_area, label, variant,
                pady=THEME.layout.button_vertical_padding, command=callback,
            ).pack(pady=THEME.layout.state_action_padding)

    def close_vault(self):
        """Fecha a sessão e descarta as referências mantidas pela interface."""
        if not self._confirm_pending_changes():
            return False
        if self.session is not None:
            self.session.close()
            self.session = None
        self.active_entry_id = None
        self.saved_title = self.saved_body = ""
        self.saved_collection_id = None
        self.saved_tags = []
        self.editor_metadata_ready = False
        self.show_locked()
        return True

    def close_app(self):
        if not self.close_vault():
            return
        self.root.destroy()

    def restore_last_vault(self):
        path = load_last_vault()
        if path is None:
            return
        try:
            located = path.is_file()
        except OSError:
            located = False
        if not located:
            show_alert(
                self.root,
                "Base não localizada", "A última base usada não foi encontrada. Escolha uma base ou crie outra.",
            )
            return
        self.unlock(path)


def build_app(root: tk.Tk) -> None:
    CadernoApp(root)


def configure_fonts() -> None:
    for name, specification in (
        ("TkDefaultFont", THEME.font_body),
        ("TkTextFont", THEME.font_text),
        ("TkFixedFont", THEME.font_fixed),
    ):
        font.nametofont(name).configure(family=specification[0], size=specification[1])


def build_sidebar(parent: tk.Widget, app: CadernoApp) -> None:
    sidebar = tk.Frame(
        parent, bg=THEME.sidebar, width=THEME.layout.sidebar_width,
        padx=THEME.layout.sidebar_padding_x, pady=THEME.layout.sidebar_padding_y,
    )
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    build_brand(sidebar)
    app.new_entry_button = make_button(
        sidebar, "+  Novo texto", "primary", pady=11, command=app.new_entry, state="disabled",
    )
    app.new_entry_button.pack(fill="x", pady=(0, 20))
    build_navigation(sidebar)
    build_collections(sidebar, app)
    build_sidebar_status(sidebar, app)


def build_brand(parent: tk.Widget) -> None:
    brand = tk.Frame(parent, bg=THEME.sidebar)
    brand.pack(fill="x", pady=(0, 26))
    tk.Label(
        brand,
        text="c.",
        bg=THEME.green,
        fg=THEME.brand_mark_foreground,
        font=THEME.font_brand,
        width=3,
        height=1,
    ).pack(side="left")
    text = tk.Frame(brand, bg=THEME.sidebar)
    text.pack(side="left", padx=10)
    tk.Label(
        text, text="Caderno", bg=THEME.sidebar, fg=THEME.ink, font=THEME.font_brand_name
    ).pack(anchor="w")
    tk.Label(
        text,
        text="de conhecimento",
        bg=THEME.sidebar,
        fg=THEME.muted,
        font=THEME.font_brand_subtitle,
    ).pack(anchor="w")


def build_navigation(parent: tk.Widget) -> None:
    items = ("▤   Todos os textos", "◷   Recentes", "☆   Favoritos", "⚙   Configurações")
    for index, label in enumerate(items):
        bg = THEME.selected_navigation_background if index == 0 else THEME.sidebar
        fg = THEME.selected_navigation_foreground if index == 0 else THEME.muted
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", pady=1)
        tk.Frame(row, bg=THEME.green if index == 0 else bg, width=3).pack(side="left", fill="y")
        tk.Label(
            row, text=label, bg=bg, fg=fg, anchor="w", padx=10, pady=10
        ).pack(side="left", fill="x", expand=True)


def build_collections(parent: tk.Widget, app: CadernoApp) -> None:
    heading = tk.Frame(parent, bg=THEME.sidebar)
    heading.pack(fill="x", pady=(27, 8))
    tk.Label(
        heading, text="COLEÇÕES", bg=THEME.sidebar, fg=THEME.muted, font=THEME.font_mono_small
    ).pack(side="left", padx=10)
    app.collection_add_button = make_button(
        heading, "+", "secondary", pady=1, command=app.add_collection, state="disabled",
    )
    app.collection_add_button.pack(side="right", padx=8)
    app.collection_items = tk.Frame(parent, bg=THEME.sidebar)
    app.collection_items.pack(fill="x")


def build_sidebar_status(parent: tk.Widget, app: CadernoApp) -> None:
    status = tk.Frame(parent, bg=THEME.sidebar)
    status.pack(side="bottom", fill="x")
    tk.Frame(status, bg=THEME.line, height=1).pack(fill="x", pady=(0, 12))
    app.status = tk.Label(
        status,
        text="●  Nenhuma base aberta",
        bg=THEME.sidebar,
        anchor="w",
        font=THEME.font_label + ("bold",),
    )
    app.status.pack(fill="x", padx=9)
    app.status_detail = tk.Label(
        status,
        text="Escolha ou crie uma base para começar",
        bg=THEME.sidebar,
        fg=THEME.muted,
        anchor="w",
        font=THEME.font_tiny,
        wraplength=200,
    )
    app.status_detail.pack(fill="x", padx=9, pady=(5, 10))
    app.close_button = make_button(
        status, "Fechar base", "secondary", pady=7, command=app.close_vault,
    )


def build_main_panel(parent: tk.Widget, app: CadernoApp) -> None:
    main = tk.Frame(parent, bg=THEME.paper)
    main.pack(side="left", fill="both", expand=True)
    build_topbar(main)
    build_library(main, app)


def build_topbar(parent: tk.Widget) -> None:
    topbar = tk.Frame(
        parent,
        bg=THEME.paper,
        padx=THEME.layout.main_horizontal_padding,
        pady=THEME.layout.topbar_vertical_padding,
        highlightbackground=THEME.line,
        highlightthickness=THEME.layout.highlight_thickness,
    )
    topbar.pack(fill="x")
    tk.Label(
        topbar,
        text="Seu espaço   /   Todos os textos",
        bg=THEME.paper,
        fg=THEME.muted,
        font=THEME.font_label,
    ).pack(side="left")
    tk.Label(
        topbar,
        text="PROTÓTIPO VISUAL     ◷  Calendário",
        bg=THEME.paper,
        fg=THEME.sage,
        font=THEME.font_label,
    ).pack(side="right")


def build_library(parent: tk.Widget, app: CadernoApp) -> None:
    content = tk.Frame(
        parent, bg=THEME.paper, padx=THEME.layout.main_horizontal_padding,
        pady=THEME.layout.main_vertical_padding,
    )
    content.pack(fill="both", expand=True)
    app.welcome_area = tk.Frame(content, bg=THEME.paper)
    app.welcome_area.pack(fill="x")
    build_welcome(app.welcome_area)
    app.summary_area = tk.Frame(content, bg=THEME.paper)
    app.summary_area.pack(fill="x")
    build_summary(app.summary_area, app)
    app.search_area = tk.Frame(content, bg=THEME.paper)
    app.search_area.pack(fill="x")
    build_search(app.search_area, app)
    build_empty_state(content, app)


def build_welcome(parent: tk.Widget) -> None:
    tk.Label(
        parent, text="SEU ARQUIVO PESSOAL", bg=THEME.paper, fg=THEME.muted, font=THEME.font_mono_small
    ).pack(anchor="w")
    tk.Label(
        parent,
        text="Um lugar para suas ideias.",
        bg=THEME.paper,
        fg=THEME.welcome_title,
        font=THEME.font_title,
    ).pack(anchor="w", pady=THEME.layout.welcome_title_padding)
    tk.Label(
        parent,
        text="Registre o que você aprende. Encontre conexões com o tempo.",
        bg=THEME.paper,
        fg=THEME.muted,
        font=THEME.font_body,
    ).pack(anchor="w")


def build_summary(parent: tk.Widget, app: CadernoApp) -> None:
    summary = tk.Frame(parent, bg=THEME.paper)
    summary.pack(fill="x", pady=THEME.layout.summary_vertical_padding)
    app.summary_values = []
    for value, label in (("0", "textos no caderno"), ("0", "coleções"), ("0", "adicionados esta semana")):
        block = tk.Frame(summary, bg=THEME.paper)
        block.pack(side="left", padx=(0, 38))
        value_label = tk.Label(
            block, text=value, bg=THEME.paper, fg=THEME.ink, font=THEME.font_summary
        )
        value_label.pack(anchor="w")
        app.summary_values.append(value_label)
        tk.Label(
            block, text=label, bg=THEME.paper, fg=THEME.muted, font=THEME.font_tiny
        ).pack(anchor="w")


def build_search(parent: tk.Widget, app: CadernoApp) -> None:
    row = tk.Frame(parent, bg=THEME.paper)
    row.pack(fill="x", pady=(0, THEME.layout.search_bottom_padding))
    app.search_placeholder = "⌕   Buscar em títulos, coleções, hashtags e conteúdo…"
    app.search_placeholder_visible = True
    app.search_query = ""
    app.search_entry = tk.Entry(
        row,
        relief="flat",
        bg=THEME.panel,
        fg=THEME.muted,
        insertbackground=THEME.green,
        highlightbackground=THEME.field_border,
        highlightcolor=THEME.green,
        highlightthickness=THEME.layout.highlight_thickness,
        font=THEME.font_body,
    )
    app.search_entry.insert(0, app.search_placeholder)
    app.search_entry.bind("<FocusIn>", app._search_focus_in)
    app.search_entry.bind("<FocusOut>", app._search_focus_out)
    app.search_entry.bind("<KeyRelease>", app._search_key_release)
    app.search_entry.bind("<Escape>", app._search_escape)
    app.search_entry.pack(
        side="left", fill="x", expand=True, ipady=THEME.layout.search_vertical_padding,
        padx=(0, THEME.layout.search_gap),
    )
    app.filter_button = make_button(
        row, "Filtrar ▾", "secondary", pady=9,
        command=app.choose_filters, state="disabled",
    )
    app.filter_button.pack(side="right")


def build_empty_state(parent: tk.Widget, app: CadernoApp) -> None:
    box = tk.Frame(
        parent,
        bg=THEME.state_panel,
        highlightbackground=THEME.empty_state_border,
        highlightthickness=THEME.layout.highlight_thickness,
        padx=THEME.layout.state_horizontal_padding,
        pady=THEME.layout.state_vertical_padding,
    )
    box.pack(fill="both", expand=True)
    app.state_area = box


def make_button(
    parent: tk.Widget, label: str, variant: ButtonVariant, pady: int,
    command=None, state="normal",
) -> tk.Button:
    styles = {
        "primary": THEME.primary_button,
        "secondary": THEME.secondary_button,
    }
    try:
        style = styles[variant]
    except KeyError as error:
        raise ValueError(f"Variante de botão desconhecida: {variant}") from error
    if state == "disabled":
        style = THEME.disabled_button
    return tk.Button(
        parent,
        text=label,
        bg=style.background,
        fg=style.foreground,
        activebackground=style.active_background,
        activeforeground=style.active_foreground,
        disabledforeground=style.foreground,
        highlightbackground=style.background,
        highlightcolor=style.focus,
        highlightthickness=THEME.layout.highlight_thickness,
        relief="flat",
        borderwidth=0,
        padx=THEME.layout.button_horizontal_padding,
        pady=pady,
        font=THEME.font_button,
        cursor="arrow" if state == "disabled" else "hand2",
        command=command,
        state=state,
    )
