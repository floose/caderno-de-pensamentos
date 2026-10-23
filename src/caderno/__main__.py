import tkinter as tk

if __package__:
    from .ui import build_app
else:
    from ui import build_app


def main() -> None:
    root = tk.Tk()
    build_app(root)
    root.mainloop()


if __name__ == "__main__":
    main()
