#!/usr/bin/env python3
"""Update installed skill copies that are only out of date, and never touch an edited one.

    python scripts/refresh_installed_skills.py            # report what would change
    python scripts/refresh_installed_skills.py --apply    # update the stale copies

The installer refuses to overwrite an installed skill it did not write, because it
cannot tell an old copy from one somebody customised. That is the right default and
it left seven clients carrying a skill eighteen lines behind the repository, with no
way to fix it but a hand copy.

Git settles the question. A copy whose bytes match some committed version of that
skill is a stale install: every byte of it came from this repository. A copy matching
no committed version has been edited locally, and is reported and left alone.

Each replaced file is kept, under <home>/.master-repo-skill-backups/, never beside the
original: a skill directory is scanned by the clients that load skills, and a second
copy of a SKILL.md sitting next to it is a file they may read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills"
# Where each client keeps its global skills. Mirrors scripts/install_auto_mode.py.
CLIENT_DIRS = (
    ".claude/skills", ".agents/skills", ".codex/skills", ".cursor/skills",
    ".copilot/skills", ".gemini/skills", ".gemini/config/skills", ".antigravity/skills",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def committed_versions(relative: str) -> dict[str, str]:
    """Every version of one file that this repository has ever committed, by digest."""
    log = subprocess.run(["git", "log", "--format=%H", "--", relative],
                         cwd=ROOT, capture_output=True, text=True)
    versions: dict[str, str] = {}
    for sha in log.stdout.split():
        blob = subprocess.run(["git", "show", f"{sha}:{relative}"], cwd=ROOT, capture_output=True)
        if blob.returncode == 0:
            versions.setdefault(digest(blob.stdout), sha[:7])
    return versions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="write the updates; otherwise report only")
    parser.add_argument("--home", default=str(pathlib.Path.home()))
    args = parser.parse_args()
    home = pathlib.Path(args.home)
    today = dt.date.today().isoformat()

    stale: list[str] = []
    edited: list[str] = []
    missing = 0
    for skill_dir in sorted(p for p in SOURCE.iterdir() if (p / "SKILL.md").is_file()):
        relative = f"skills/{skill_dir.name}/SKILL.md"
        current = (skill_dir / "SKILL.md").read_bytes()
        history: dict[str, str] | None = None
        for client in CLIENT_DIRS:
            installed = home / client / skill_dir.name / "SKILL.md"
            if not installed.is_file():
                missing += 1
                continue
            data = installed.read_bytes()
            if data == current:
                continue
            if history is None:
                history = committed_versions(relative)
            origin = history.get(digest(data))
            if origin is None:
                edited.append(f"{installed}: does not match any committed version, left alone")
                continue
            stale.append(f"{installed}: {len(data)} -> {len(current)} bytes, was the version from {origin}")
            if args.apply:
                backup = home / ".master-repo-skill-backups" / today / client / skill_dir.name / "SKILL.md"
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(data)
                shutil.copyfile(skill_dir / "SKILL.md", installed)

    for line in stale:
        print(("updated " if args.apply else "stale   ") + line)
    for line in edited:
        print("EDITED  " + line)
    print(f"\n{len(stale)} stale, {len(edited)} locally edited, {missing} not installed."
          + ("" if args.apply else "  Re-run with --apply to update the stale copies."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
