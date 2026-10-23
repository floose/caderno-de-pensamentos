import tkinter as tk
from tkinter import font


PAPER = "#f5f3ee"
SIDEBAR = "#f0eee8"
PANEL = "#fffefa"
INK = "#202622"
MUTED = "#858981"
LINE = "#e8e6df"
GREEN = "#355c47"


def build_app(root: tk.Tk) -> None:
    root.title("Caderno de Pensamentos")
    root.geometry("1180x760")
    root.minsize(900, 620)
    root.configure(bg=PAPER)
    configure_fonts()

    shell = tk.Frame(root, bg=PAPER)
    shell.pack(fill="both", expand=True)
    build_sidebar(shell)
    build_main_panel(shell)


def configure_fonts() -> None:
    font.nametofont("TkDefaultFont").configure(family="Arial", size=10)
    font.nametofont("TkTextFont").configure(family="Georgia", size=12)
    font.nametofont("TkFixedFont").configure(family="Menlo", size=10)


def build_sidebar(parent: tk.Widget) -> None:
    sidebar = tk.Frame(parent, bg=SIDEBAR, width=250, padx=18, pady=24)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    build_brand(sidebar)
    make_button(
        sidebar, "+  Novo texto", GREEN, "white", pady=11
    ).pack(fill="x", pady=(0, 20))
    build_navigation(sidebar)
    build_collections(sidebar)
    build_sidebar_status(sidebar)


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
        fg = "#273b30" if index == 0 else "#686e68"
        tk.Label(
            parent, text=label, bg=bg, fg=fg, anchor="w", padx=10, pady=10
        ).pack(fill="x", pady=1)


def build_collections(parent: tk.Widget) -> None:
    heading = tk.Frame(parent, bg=SIDEBAR)
    heading.pack(fill="x", pady=(27, 8))
    tk.Label(
        heading, text="COLEÇÕES", bg=SIDEBAR, fg="#999b92", font=("Menlo", 8)
    ).pack(side="left", padx=10)
    tk.Label(
        heading, text="+", bg=SIDEBAR, fg=MUTED, font=("Arial", 15)
    ).pack(side="right", padx=8)
    tk.Label(
        parent,
        text="Suas coleções aparecerão aqui",
        bg=SIDEBAR,
        fg="#a0a198",
        anchor="w",
        padx=10,
        pady=8,
        font=("Arial", 9),
    ).pack(fill="x")


def build_sidebar_status(parent: tk.Widget) -> None:
    status = tk.Frame(parent, bg=SIDEBAR)
    status.pack(side="bottom", fill="x")
    tk.Frame(status, bg=LINE, height=1).pack(fill="x", pady=(0, 12))
    tk.Label(
        status,
        text="●  Nenhuma base aberta",
        bg=SIDEBAR,
        fg="#5b655c",
        anchor="w",
        font=("Arial", 9, "bold"),
    ).pack(fill="x", padx=9)
    tk.Label(
        status,
        text="Escolha ou crie uma base para começar",
        bg=SIDEBAR,
        fg="#999b93",
        anchor="w",
        font=("Arial", 8),
        wraplength=200,
    ).pack(fill="x", padx=9, pady=(5, 10))


def build_main_panel(parent: tk.Widget) -> None:
    main = tk.Frame(parent, bg=PAPER)
    main.pack(side="left", fill="both", expand=True)
    build_topbar(main)
    build_library(main)


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
        fg="#686e68",
        font=("Arial", 9),
    ).pack(side="left")
    tk.Label(
        topbar,
        text="PROTÓTIPO VISUAL     ◷  Calendário",
        bg=PAPER,
        fg="#657566",
        font=("Arial", 9),
    ).pack(side="right")


def build_library(parent: tk.Widget) -> None:
    content = tk.Frame(parent, bg=PAPER, padx=48, pady=45)
    content.pack(fill="both", expand=True)
    build_welcome(content)
    build_summary(content)
    build_search(content)
    build_empty_state(content)


def build_welcome(parent: tk.Widget) -> None:
    tk.Label(
        parent, text="SEU ARQUIVO PESSOAL", bg=PAPER, fg="#a2a295", font=("Menlo", 8)
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


def build_summary(parent: tk.Widget) -> None:
    summary = tk.Frame(parent, bg=PAPER)
    summary.pack(fill="x", pady=(27, 23))
    for value, label in (("0", "textos no caderno"), ("0", "coleções"), ("0", "adicionados esta semana")):
        block = tk.Frame(summary, bg=PAPER)
        block.pack(side="left", padx=(0, 38))
        tk.Label(
            block, text=value, bg=PAPER, fg=INK, font=("Georgia", 16)
        ).pack(anchor="w")
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
        fg="#777e74",
        insertbackground=GREEN,
        font=("Arial", 10),
    )
    search.insert(0, "⌕   Buscar por título, tema ou conteúdo…")
    search.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 12))
    make_button(
        row, "Ordenar: última edição  ▾", PANEL, "#5d645d", pady=9
    ).pack(side="right")


def build_empty_state(parent: tk.Widget) -> None:
    box = tk.Frame(
        parent,
        bg="#f7f6f1",
        highlightbackground="#dcdcd3",
        highlightthickness=1,
        padx=20,
        pady=34,
    )
    box.pack(fill="both", expand=True)
    tk.Label(
        box,
        text="✳",
        bg="#f1f2ec",
        fg="#6d826f",
        font=("Georgia", 20),
        width=3,
        height=1,
    ).pack(pady=(0, 10))
    tk.Label(
        box,
        text="Seu caderno começa com uma ideia.",
        bg="#f7f6f1",
        fg="#38453b",
        font=("Georgia", 18),
    ).pack()
    tk.Label(
        box,
        text="Abra ou crie uma base de dados para começar a escrever.",
        bg="#f7f6f1",
        fg="#969a91",
        font=("Arial", 9),
    ).pack(pady=(7, 15))
    make_button(box, "Escolher ou criar base", GREEN, "white", pady=9).pack()


def make_button(parent: tk.Widget, label: str, background: str, foreground: str, pady: int) -> tk.Button:
    return tk.Button(
        parent,
        text=label,
        bg=background,
        fg=foreground,
        activebackground=GREEN,
        activeforeground="white",
        relief="flat",
        borderwidth=0,
        padx=12,
        pady=pady,
        font=("Arial", 9, "bold"),
        cursor="hand2",
    )
