"""Mede a listagem do PathDialog em pastas sintéticas de tamanhos definidos."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import tempfile
import time
import tkinter as tk
from pathlib import Path

from caderno.ui import PathDialog


def _measure_directory(root: tk.Tk, empty_directory: Path, directory: Path,
                       entries: int, samples: int) -> dict:
    """Mede a primeira listagem e as amostras repetidas da mesma pasta."""
    dialog = PathDialog(root, "open", empty_directory, directory.parent)
    try:
        dialog.directory = directory
        first = _refresh_seconds(dialog)
        timings = [_refresh_seconds(dialog) for _ in range(samples)]
        if len(dialog.path_items) != entries:
            raise RuntimeError("O seletor não listou todos os arquivos sintéticos")
        return {
            "entries": entries,
            "first_refresh_seconds": round(first, 6),
            "repeat_seconds": [round(value, 6) for value in timings],
            "median_repeat_seconds": round(statistics.median(timings), 6),
            "min_repeat_seconds": round(min(timings), 6),
            "max_repeat_seconds": round(max(timings), 6),
        }
    finally:
        dialog.cancel()


def _refresh_seconds(dialog: PathDialog) -> float:
    started = time.perf_counter()
    dialog._refresh_items()
    dialog.window.update_idletasks()
    return time.perf_counter() - started


def _create_synthetic_files(directory: Path, count: int) -> None:
    """Prepara arquivos vazios fora da região cronometrada."""
    for index in range(count):
        (directory / f"synthetic-{index:06}.cpv").touch()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entries", nargs="+", type=int, default=[100, 1000, 5000],
        help="quantidade sintética de arquivos por pasta (padrão: 100 1000 5000)",
    )
    parser.add_argument("--samples", type=int, default=5, help="repetições por tamanho (mínimo 3)")
    args = parser.parse_args()
    if (
        args.samples < 3
        or any(count < 1 for count in args.entries)
        or len(set(args.entries)) != len(args.entries)
    ):
        parser.error("informe tamanhos positivos e distintos, e pelo menos 3 amostras")

    with tempfile.TemporaryDirectory(prefix="caderno-path-benchmark-") as temporary:
        base = Path(temporary)
        empty = base / "empty"
        empty.mkdir()
        root = tk.Tk()
        root.withdraw()
        try:
            measurements = []
            for count in args.entries:
                directory = base / f"files-{count}"
                directory.mkdir()
                _create_synthetic_files(directory, count)
                measurements.append(_measure_directory(root, empty, directory, count, args.samples))
        finally:
            root.destroy()

    print(json.dumps({
        "python": platform.python_version(),
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "tk_version": tk.TkVersion,
        "samples_per_size": args.samples,
        "measurement": "PathDialog._refresh_items + update_idletasks; synthetic empty .cpv files",
        "results": measurements,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
