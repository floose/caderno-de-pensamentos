"""Measure the exact CPV1 Argon2id KDF without printing synthetic secrets."""

from __future__ import annotations

import argparse
import json
import platform
import resource
import statistics
import sys
import time

import nacl
from nacl import pwhash

OPSLIMIT = 3
MEMLIMIT = 268435456
OUTLEN = 32
SYNTHETIC_PASSWORD = b"caderno-argon2id-benchmark-only"
SYNTHETIC_SALT = b"0123456789abcdef"


def _peak_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def _run_one() -> float:
    started = time.perf_counter()
    key = pwhash.argon2id.kdf(
        OUTLEN,
        SYNTHETIC_PASSWORD,
        SYNTHETIC_SALT,
        opslimit=OPSLIMIT,
        memlimit=MEMLIMIT,
    )
    elapsed = time.perf_counter() - started
    if len(key) != OUTLEN:
        raise RuntimeError("PyNaCl retornou tamanho de chave inesperado")
    return elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=5, help="número de derivações (mínimo 3)")
    args = parser.parse_args()
    if args.samples < 3:
        parser.error("--samples precisa ser pelo menos 3")
    baseline_rss = _peak_rss_bytes()
    times = [_run_one() for _ in range(args.samples)]
    result = {
        "python": platform.python_version(),
        "pynacl": nacl.__version__,
        "architecture": platform.machine(),
        "platform": platform.platform(),
        "kdf": "Argon2id13",
        "opslimit": OPSLIMIT,
        "memlimit_bytes": MEMLIMIT,
        "output_bytes": OUTLEN,
        "samples_seconds": [round(value, 4) for value in times],
        "median_seconds": round(statistics.median(times), 4),
        "minimum_seconds": round(min(times), 4),
        "maximum_seconds": round(max(times), 4),
        "baseline_peak_rss_bytes": baseline_rss,
        "process_peak_rss_bytes": _peak_rss_bytes(),
        "rss_note": "ru_maxrss is process high-water RSS; it is not isolated KDF allocation.",
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
