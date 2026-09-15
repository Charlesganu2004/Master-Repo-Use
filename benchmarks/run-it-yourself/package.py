"""Zip the run-it-yourself kit so it travels as one file.

The kit itself, plus the full benchmark report, because the first question anyone
who receives the kit asks is what the numbers looked like when we ran it.

    python benchmarks/run-it-yourself/package.py

writes benchmarks/share/harness-metrics-<date>.zip, named for the kit's own date
so two builds of different vintages do not collide.
"""
from __future__ import annotations

import argparse
import pathlib
import zipfile

KIT = pathlib.Path(__file__).resolve().parent
BENCHMARKS = KIT.parent
REPO = BENCHMARKS.parent
SKIP = {"__pycache__", ".goal-store"}
STAMP = "2026-09-15"
# Files from outside the kit, published at the path the archive should carry.
EXTRAS = {
    BENCHMARKS / "2026-09-11" / "report" / "report.pdf": "report/full-benchmark-report.pdf",
    BENCHMARKS / "2026-09-15" / "charts" / "graphify_experiment.png": "charts/graphify_experiment.png",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(BENCHMARKS / "share" / f"harness-metrics-{STAMP}.zip"))
    args = parser.parse_args()
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    root = pathlib.Path(out.stem)

    written: dict[str, pathlib.Path] = {}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(KIT.rglob("*")):
            if not path.is_file() or any(part in SKIP for part in path.parts) or path == pathlib.Path(__file__):
                continue
            name = (root / path.relative_to(KIT)).as_posix()
            written[name] = path
            zf.write(path, name)
        for source, target in EXTRAS.items():
            if not source.exists():
                raise SystemExit(f"missing {source.relative_to(REPO)}; build it before packaging")
            name = (root / target).as_posix()
            if name in written:
                raise SystemExit(f"{name} would be written twice")
            written[name] = source
            zf.write(source, name)

    print(f"{out} ({out.stat().st_size:,} bytes, {len(written)} files)")


if __name__ == "__main__":
    main()
