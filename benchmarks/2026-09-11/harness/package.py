"""Zip the benchmark kit: prompts, hidden checks, fixtures, scripts, raw results,
charts and the report, so the whole thing travels as one file.

    python benchmarks/2026-09-11/harness/package.py --out <path to zip>
"""
from __future__ import annotations

import argparse
import pathlib
import zipfile

BENCH = pathlib.Path(__file__).resolve().parents[1]
SKIP = {".goal-store", "__pycache__"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(BENCH.rglob("*")):
            if not path.is_file() or any(part in SKIP for part in path.parts):
                continue
            zf.write(path, pathlib.Path("benchmarks-2026-09-11") / path.relative_to(BENCH))
            count += 1
    print(f"{out} ({out.stat().st_size:,} bytes, {count} files)")


if __name__ == "__main__":
    main()
