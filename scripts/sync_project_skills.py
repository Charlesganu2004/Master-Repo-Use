#!/usr/bin/env python3
"""Mirror canonical repository skills into the shared project discovery path.

``skills/`` remains the source of truth. Codex, GitHub Copilot and Cursor can
discover project-scoped skills from ``.agents/skills/`` when the repository is
running locally or in a cloud coding agent. The mirror is an additive refresh:
source files replace older copies with the same path, while destination-only
files and directories remain untouched.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil


def canonical_skills(repo: pathlib.Path) -> tuple[pathlib.Path, ...]:
    """Return immediate canonical skill directories in stable name order."""
    source = repo / "skills"
    if not source.is_dir():
        raise FileNotFoundError(f"Canonical skill directory not found: {source}")
    return tuple(sorted(
        (path for path in source.iterdir()
         if path.is_dir() and (path / "SKILL.md").is_file()),
        key=lambda path: path.name.casefold(),
    ))


def sync_project_skills(
    repo: pathlib.Path | str,
    dry_run: bool = False,
) -> tuple[pathlib.Path, ...]:
    """Merge canonical skills into ``.agents/skills`` and return destinations.

    This function never removes a destination path. It is safe for build scripts
    to call repeatedly, including when a user or another client placed extra
    resources inside an existing mirrored skill directory.
    """
    root = pathlib.Path(repo).expanduser().resolve()
    skills = canonical_skills(root)
    destination_root = root / ".agents" / "skills"
    destinations = tuple(destination_root / skill.name for skill in skills)

    if dry_run:
        return destinations

    destination_root.mkdir(parents=True, exist_ok=True)
    for skill, destination in zip(skills, destinations):
        shutil.copytree(skill, destination, dirs_exist_ok=True)
    return destinations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge canonical skills into .agents/skills without pruning extras."
    )
    parser.add_argument(
        "--repo",
        default=str(pathlib.Path(__file__).resolve().parents[1]),
        help="repository root containing skills/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list destinations without writing files",
    )
    args = parser.parse_args()

    try:
        destinations = sync_project_skills(args.repo, dry_run=args.dry_run)
    except (FileNotFoundError, OSError) as exc:
        parser.exit(1, f"sync_project_skills: {exc}\n")

    action = "Would merge" if args.dry_run else "Merged"
    print(
        f"{action} {len(destinations)} project skills into .agents/skills "
        "without deleting destination-only files."
    )
    for destination in destinations:
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
