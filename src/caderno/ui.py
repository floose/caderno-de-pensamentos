import os
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import filedialog, font, messagebox, simpledialog
from typing import Literal

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
    font_collection_add: tuple
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
    font_fixed=("Menlo", 12), font_button=("Arial", 12, "bold"),
    font_label=("Arial", 11), font_tiny=("Arial", 10),
    font_brand=("Georgia", 20, "bold"), font_brand_name=("Arial", 12, "bold"),
    font_brand_subtitle=("Georgia", 11, "italic"), font_icon=("Georgia", 22),
    font_collection_add=("Arial", 18),
    font_title=("Georgia", 34), font_heading=("Georgia", 22),
    font_summary=("Georgia", 18), font_mono_small=("Menlo", 10),
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
    ),
)


class CadernoApp:
    """Coordena o ciclo de abertura e fechamento do cofre pela interface."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.session: VaultSession | None = None
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
        self.restore_last_vault()

    def create(self):
        """Pede destino e senha, cria cofre vazio e só então lembra o caminho."""
        options = dict(
            parent=self.root, title="Criar base", defaultextension=".cpv",
            filetypes=[("Base criptografada", "*.cpv")],
        )
        if os.environ.get("CADERNO_UI_TEST_PROFILE"):
            options["initialdir"] = os.environ["CADERNO_UI_TEST_PROFILE"]
        target = filedialog.asksaveasfilename(**options)
        if not target:
            return
        if not self._path_allowed_in_test_profile(Path(target)):
            messagebox.showerror(
                "Arquivo fora da pasta de teste",
                "No perfil de teste, crie a base dentro da pasta de teste indicada no Terminal.",
                parent=self.root,
            )
            return
        password = simpledialog.askstring("Criar base", "Escolha uma senha:", show="•", parent=self.root)
        if password is None:
            return
        confirmation = simpledialog.askstring(
            "Confirmar senha", "Digite a senha novamente:", show="•", parent=self.root
        )
        if confirmation is None:
            return
        if not password or password != confirmation:
            messagebox.showerror("Não foi possível criar", "A senha está vazia ou as confirmações não coincidem.", parent=self.root)
            return
        document = {
            "schema_version": 1,
            "collections": [{"id": "default", "name": "Geral"}],
            "attachments": [],
            "entries": [],
        }
        try:
            session = create_vault(Path(target), password, VaultSnapshot(document))
        except FileExistsError:
            messagebox.showerror("Não foi possível criar", "Já existe um arquivo nesse local.", parent=self.root)
            return
        except DurabilityUncertainError:
            messagebox.showwarning(
                "Gravação incerta",
                "O arquivo pode ter sido criado, mas não foi possível confirmar sua gravação. "
                "Não tente sobrescrevê-lo; escolha-o e tente abri-lo para validar.",
                parent=self.root,
            )
            return
        except Exception:
            messagebox.showerror("Não foi possível criar", "Verifique o local escolhido e tente novamente.", parent=self.root)
            return
        self._activate(session)
        self._remember_path(Path(target))

    def choose(self):
        """Seleciona um arquivo de cofre e solicita a senha sem persistí-la."""
        options = dict(
            parent=self.root, title="Abrir base",
            filetypes=[("Base criptografada", "*.cpv"), ("Todos os arquivos", "*")],
        )
        if os.environ.get("CADERNO_UI_TEST_PROFILE"):
            options["initialdir"] = os.environ["CADERNO_UI_TEST_PROFILE"]
        target = filedialog.askopenfilename(**options)
        if target:
            self.unlock(Path(target))

    def unlock(self, path: Path):
        """Abre um cofre; mensagens de falha não revelam detalhes internos do arquivo."""
        if not self._path_allowed_in_test_profile(path):
            messagebox.showerror(
                "Arquivo fora da pasta de teste",
                "No perfil de teste, escolha um arquivo dentro da pasta de teste indicada no Terminal.",
                parent=self.root,
            )
            return
        password = simpledialog.askstring("Abrir base", "Digite a senha da base:", show="•", parent=self.root)
        if password is None:
            return
        try:
            session = open_vault(path, password)
        except Exception:
            messagebox.showerror(
                "Não foi possível abrir a base",
                "A senha pode estar incorreta ou o arquivo pode estar inválido ou indisponível.",
                parent=self.root,
            )
            return
        self._activate(session)
        self._remember_path(path)

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
            messagebox.showwarning(
                "Base aberta", "A base está aberta, mas não foi possível lembrar este caminho.", parent=self.root
            )

    def _activate(self, session: VaultSession):
        if self.session is not None:
            self.session.close()
        self.session = session
        self.show_unlocked(session)

    def show_locked(self):
        self.status.configure(text="●  Nenhuma base aberta", fg=THEME.locked_status)
        self.status_detail.configure(text="Escolha ou crie uma base para começar")
        self.close_button.pack_forget()
        self.update_summary(None)
        self.render_state(
            "Seu caderno começa com uma ideia.",
            "Abra ou crie uma base criptografada para começar.",
            ("Escolher base", self.choose, "primary"),
            ("Criar base", self.create, "primary"),
        )

    def show_unlocked(self, session: VaultSession):
        self.status.configure(text="●  Base aberta", fg=THEME.green)
        self.status_detail.configure(text=session.path.name)
        self.close_button.pack(fill="x", padx=8, pady=(8, 0))
        self.update_summary(session.snapshot.document)
        self.render_state(
            "Base desbloqueada.",
            "O cofre está aberto. A edição de textos será conectada na próxima etapa.",
            ("Escolher outra base", self.choose, "secondary"),
            ("Fechar base", self.close_vault, "secondary"),
        )

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
        if self.session is not None:
            self.session.close()
            self.session = None
        self.show_locked()

    def close_app(self):
        self.close_vault()
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
            messagebox.showinfo(
                "Base não localizada", "A última base usada não foi encontrada. Escolha uma base ou crie outra.",
                parent=self.root,
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
    make_button(sidebar, "+  Novo texto", "primary", pady=11, state="disabled").pack(fill="x", pady=(0, 20))
    build_navigation(sidebar)
    build_collections(sidebar)
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


def build_collections(parent: tk.Widget) -> None:
    heading = tk.Frame(parent, bg=THEME.sidebar)
    heading.pack(fill="x", pady=(27, 8))
    tk.Label(
        heading, text="COLEÇÕES", bg=THEME.sidebar, fg=THEME.muted, font=THEME.font_mono_small
    ).pack(side="left", padx=10)
    tk.Label(
        heading, text="+", bg=THEME.sidebar, fg=THEME.muted, font=THEME.font_collection_add
    ).pack(side="right", padx=8)
    tk.Label(
        parent,
        text="Suas coleções aparecerão aqui",
        bg=THEME.sidebar,
        fg=THEME.muted,
        anchor="w",
        padx=10,
        pady=8,
        font=THEME.font_label,
    ).pack(fill="x")


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
    build_welcome(content)
    build_summary(content, app)
    build_search(content)
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


def build_search(parent: tk.Widget) -> None:
    row = tk.Frame(parent, bg=THEME.paper)
    row.pack(fill="x", pady=(0, THEME.layout.search_bottom_padding))
    search = tk.Entry(
        row,
        relief="flat",
        bg=THEME.panel,
        fg=THEME.muted,
        disabledbackground=THEME.panel,
        disabledforeground=THEME.muted,
        insertbackground=THEME.green,
        highlightbackground=THEME.field_border,
        highlightcolor=THEME.green,
        highlightthickness=THEME.layout.highlight_thickness,
        font=THEME.font_body,
    )
    search.insert(0, "⌕   Buscar por título, tema ou conteúdo…")
    search.configure(state="disabled")
    search.pack(
        side="left", fill="x", expand=True, ipady=THEME.layout.search_vertical_padding,
        padx=(0, THEME.layout.search_gap),
    )
    make_button(
        row, "Ordenar: última edição  ▾", "secondary", pady=9, state="disabled"
    ).pack(side="right")


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
