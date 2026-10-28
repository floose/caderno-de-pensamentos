import os
import tkinter as tk
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tkinter import filedialog, font, messagebox, simpledialog

if __package__:
    from .preferences import load_last_vault, save_last_vault
    from .vault import DurabilityUncertainError, VaultSession, VaultSnapshot, create_vault, open_vault
else:
    from preferences import load_last_vault, save_last_vault
    from vault import DurabilityUncertainError, VaultSession, VaultSnapshot, create_vault, open_vault


PAPER = "#f5f3ee"
SIDEBAR = "#f0eee8"
PANEL = "#fffefa"
INK = "#202622"
MUTED = "#5f665e"
LINE = "#e8e6df"
GREEN = "#355c47"
PRIMARY_BUTTON = "#294b38"
SECONDARY_BUTTON = "#dfe4dc"
SECONDARY_ACTIVE = "#cfd8cc"
SAGE = "#536b56"
DISABLED_BUTTON = "#e3e5de"
STATE_PANEL = "#f7f6f1"
FIELD_BORDER = "#7c8278"
FOCUS_ON_PRIMARY = "#f6f3e9"


class CadernoApp:
    """Coordena o ciclo de abertura e fechamento do cofre pela interface."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.session: VaultSession | None = None
        root.title("Caderno de Pensamentos")
        root.geometry("1180x760")
        root.minsize(900, 620)
        root.configure(bg=PAPER)
        root.protocol("WM_DELETE_WINDOW", self.close_app)
        configure_fonts()
        shell = tk.Frame(root, bg=PAPER)
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
        self.status.configure(text="●  Nenhuma base aberta", fg="#5b655c")
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
        self.status.configure(text="●  Base aberta", fg=GREEN)
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
        tk.Label(self.state_area, text="✳", bg="#f1f2ec", fg="#6d826f", font=("Georgia", 20), width=3).pack(pady=(0, 10))
        tk.Label(self.state_area, text=title, bg=STATE_PANEL, fg="#38453b", font=("Georgia", 18)).pack()
        tk.Label(
            self.state_area, text=description, bg=STATE_PANEL, fg=MUTED, font=("Arial", 9),
            wraplength=600,
        ).pack(pady=(7, 15))
        for label, callback, variant in actions:
            make_button(
                self.state_area, label, GREEN, "white", pady=9,
                command=callback, variant=variant,
            ).pack(pady=3)

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
    font.nametofont("TkDefaultFont").configure(family="Arial", size=10)
    font.nametofont("TkTextFont").configure(family="Georgia", size=12)
    font.nametofont("TkFixedFont").configure(family="Menlo", size=10)


def build_sidebar(parent: tk.Widget, app: CadernoApp) -> None:
    sidebar = tk.Frame(parent, bg=SIDEBAR, width=250, padx=18, pady=24)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    build_brand(sidebar)
    make_button(sidebar, "+  Novo texto", GREEN, "white", pady=11, state="disabled").pack(fill="x", pady=(0, 20))
    build_navigation(sidebar)
    build_collections(sidebar)
    build_sidebar_status(sidebar, app)


def build_brand(parent: tk.Widget) -> None:
    brand = tk.Frame(parent, bg=SIDEBAR)
    brand.pack(fill="x", pady=(0, 26))
    tk.Label(
        brand,
        text="c.",
        bg=GREEN,
        fg="#f6f3e9",
        font=("Georgia", 19, "bold"),
        width=3,
        height=1,
    ).pack(side="left")
    text = tk.Frame(brand, bg=SIDEBAR)
    text.pack(side="left", padx=10)
    tk.Label(
        text, text="Caderno", bg=SIDEBAR, fg=INK, font=("Arial", 11, "bold")
    ).pack(anchor="w")
    tk.Label(
        text,
        text="de conhecimento",
        bg=SIDEBAR,
        fg=MUTED,
        font=("Georgia", 10, "italic"),
    ).pack(anchor="w")


def build_navigation(parent: tk.Widget) -> None:
    items = ("▤   Todos os textos", "◷   Recentes", "☆   Favoritos", "⚙   Configurações")
    for index, label in enumerate(items):
        bg = "#e4e5dd" if index == 0 else SIDEBAR
        fg = "#273b30" if index == 0 else MUTED
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", pady=1)
        tk.Frame(row, bg=GREEN if index == 0 else bg, width=3).pack(side="left", fill="y")
        tk.Label(
            row, text=label, bg=bg, fg=fg, anchor="w", padx=10, pady=10
        ).pack(side="left", fill="x", expand=True)


def build_collections(parent: tk.Widget) -> None:
    heading = tk.Frame(parent, bg=SIDEBAR)
    heading.pack(fill="x", pady=(27, 8))
    tk.Label(
        heading, text="COLEÇÕES", bg=SIDEBAR, fg=MUTED, font=("Menlo", 8)
    ).pack(side="left", padx=10)
    tk.Label(
        heading, text="+", bg=SIDEBAR, fg=MUTED, font=("Arial", 15)
    ).pack(side="right", padx=8)
    tk.Label(
        parent,
        text="Suas coleções aparecerão aqui",
        bg=SIDEBAR,
        fg=MUTED,
        anchor="w",
        padx=10,
        pady=8,
        font=("Arial", 9),
    ).pack(fill="x")


def build_sidebar_status(parent: tk.Widget, app: CadernoApp) -> None:
    status = tk.Frame(parent, bg=SIDEBAR)
    status.pack(side="bottom", fill="x")
    tk.Frame(status, bg=LINE, height=1).pack(fill="x", pady=(0, 12))
    app.status = tk.Label(
        status,
        text="●  Nenhuma base aberta",
        bg=SIDEBAR,
        anchor="w",
        font=("Arial", 9, "bold"),
    )
    app.status.pack(fill="x", padx=9)
    app.status_detail = tk.Label(
        status,
        text="Escolha ou crie uma base para começar",
        bg=SIDEBAR,
        fg=MUTED,
        anchor="w",
        font=("Arial", 8),
        wraplength=200,
    )
    app.status_detail.pack(fill="x", padx=9, pady=(5, 10))
    app.close_button = make_button(
        status, "Fechar base", PANEL, INK, pady=7,
        command=app.close_vault, variant="secondary",
    )


def build_main_panel(parent: tk.Widget, app: CadernoApp) -> None:
    main = tk.Frame(parent, bg=PAPER)
    main.pack(side="left", fill="both", expand=True)
    build_topbar(main)
    build_library(main, app)


def build_topbar(parent: tk.Widget) -> None:
    topbar = tk.Frame(
        parent,
        bg=PAPER,
        padx=48,
        pady=20,
        highlightbackground=LINE,
        highlightthickness=1,
    )
    topbar.pack(fill="x")
    tk.Label(
        topbar,
        text="Seu espaço   /   Todos os textos",
        bg=PAPER,
        fg=MUTED,
        font=("Arial", 9),
    ).pack(side="left")
    tk.Label(
        topbar,
        text="PROTÓTIPO VISUAL     ◷  Calendário",
        bg=PAPER,
        fg=SAGE,
        font=("Arial", 9),
    ).pack(side="right")


def build_library(parent: tk.Widget, app: CadernoApp) -> None:
    content = tk.Frame(parent, bg=PAPER, padx=48, pady=45)
    content.pack(fill="both", expand=True)
    build_welcome(content)
    build_summary(content, app)
    build_search(content)
    build_empty_state(content, app)


def build_welcome(parent: tk.Widget) -> None:
    tk.Label(
        parent, text="SEU ARQUIVO PESSOAL", bg=PAPER, fg=MUTED, font=("Menlo", 8)
    ).pack(anchor="w")
    tk.Label(
        parent,
        text="Um lugar para suas ideias.",
        bg=PAPER,
        fg="#252c27",
        font=("Georgia", 30),
    ).pack(anchor="w", pady=(9, 4))
    tk.Label(
        parent,
        text="Registre o que você aprende. Encontre conexões com o tempo.",
        bg=PAPER,
        fg=MUTED,
        font=("Arial", 10),
    ).pack(anchor="w")


def build_summary(parent: tk.Widget, app: CadernoApp) -> None:
    summary = tk.Frame(parent, bg=PAPER)
    summary.pack(fill="x", pady=(27, 23))
    app.summary_values = []
    for value, label in (("0", "textos no caderno"), ("0", "coleções"), ("0", "adicionados esta semana")):
        block = tk.Frame(summary, bg=PAPER)
        block.pack(side="left", padx=(0, 38))
        value_label = tk.Label(
            block, text=value, bg=PAPER, fg=INK, font=("Georgia", 16)
        )
        value_label.pack(anchor="w")
        app.summary_values.append(value_label)
        tk.Label(
            block, text=label, bg=PAPER, fg=MUTED, font=("Arial", 8)
        ).pack(anchor="w")


def build_search(parent: tk.Widget) -> None:
    row = tk.Frame(parent, bg=PAPER)
    row.pack(fill="x", pady=(0, 18))
    search = tk.Entry(
        row,
        relief="flat",
        bg=PANEL,
        fg=MUTED,
        disabledbackground=PANEL,
        disabledforeground=MUTED,
        insertbackground=GREEN,
        highlightbackground=FIELD_BORDER,
        highlightcolor=GREEN,
        highlightthickness=1,
        font=("Arial", 10),
    )
    search.insert(0, "⌕   Buscar por título, tema ou conteúdo…")
    search.configure(state="disabled")
    search.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 12))
    make_button(
        row, "Ordenar: última edição  ▾", PANEL, MUTED, pady=9, state="disabled"
    ).pack(side="right")


def build_empty_state(parent: tk.Widget, app: CadernoApp) -> None:
    box = tk.Frame(
        parent,
        bg=STATE_PANEL,
        highlightbackground="#dcdcd3",
        highlightthickness=1,
        padx=20,
        pady=34,
    )
    box.pack(fill="both", expand=True)
    app.state_area = box


def make_button(
    parent: tk.Widget, label: str, background: str, foreground: str, pady: int,
    command=None, state="normal", variant="default",
) -> tk.Button:
    active_background = GREEN
    active_foreground = "white"
    focus_color = GREEN
    if variant == "primary":
        background, foreground = PRIMARY_BUTTON, "white"
        focus_color = FOCUS_ON_PRIMARY
    elif variant == "secondary":
        background, foreground = SECONDARY_BUTTON, INK
        active_background, active_foreground = SECONDARY_ACTIVE, INK
    if state == "disabled":
        background = DISABLED_BUTTON
        foreground = MUTED
        active_background, active_foreground = background, foreground
    return tk.Button(
        parent,
        text=label,
        bg=background,
        fg=foreground,
        activebackground=active_background,
        activeforeground=active_foreground,
        disabledforeground=foreground,
        highlightbackground=background,
        highlightcolor=focus_color,
        highlightthickness=1,
        relief="flat",
        borderwidth=0,
        padx=12,
        pady=pady,
        font=("Arial", 9, "bold"),
        cursor="arrow" if state == "disabled" else "hand2",
        command=command,
        state=state,
    )
