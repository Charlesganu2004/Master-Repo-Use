#!/usr/bin/env python3
"""Install a catalogued third-party skill pack into every client's skill root.

Catalog entries are reference-only by design: a repository URL is not a vetted
install, and `docs/REPO-CATALOG.md` deliberately gives no way to run one. That is
the right default and this script does not change it. What it adds is the missing
middle step, so adopting a skill pack is a reviewed action rather than either an
unreviewed `git clone` into a config directory or nothing at all.

What it will not do, each for a reason:

  It will not install a slug that is not in repo-lists/. A typosquat is the exact
  attack a skills marketplace invites, and "did you already vet this" is a
  question the catalog can answer for free. An uncatalogued slug is refused, not
  scanned-then-installed.

  It will not execute anything from the cloned repository. No npm install, no
  postinstall, no setup script, no build. It copies directories that contain a
  SKILL.md and nothing else. A skill pack that needs to run code to install is
  not a skill pack.

  It will not overwrite a skill folder it did not install. The no-prune rule says
  a capability is never removed or disabled without Charles saying so, and
  silently replacing one with a same-named folder from a different repository is
  a removal wearing a hat. Collisions are reported and refused.

  It will not install over scanner findings without being told to. Findings are
  printed in full first, so --accept-findings is a decision made after reading
  them rather than a flag copied off a wiki.

Usage:
    python scripts/install_catalog_skill.py mattpocock/skills --dry-run
    python scripts/install_catalog_skill.py mattpocock/skills
    python scripts/install_catalog_skill.py --list
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import catalog_security as security  # noqa: E402

SLUG_RE = re.compile(r"[\w.-]+/[\w.-]+")

# Both clients read one directory per skill, each holding a SKILL.md. Same shape,
# so one copy serves both. Antigravity's path was read from
# antigravity.google/docs/skills on 2026-09-04; it is under ~/.gemini/config/ and
# there is no ~/.antigravity/ tree.
SKILL_ROOTS = {
    "Claude Code": pathlib.Path(".claude") / "skills",
    "Antigravity": pathlib.Path(".gemini") / "config" / "skills",
}

# Files that are never worth scanning or copying, and that dominate the byte count
# of any repository with a lockfile in it.
SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv"}
MAX_SCAN_BYTES = 2_000_000


def catalogued_slugs() -> dict[str, str]:
    """Every slug in repo-lists/, mapped to the lane file that carries it.

    Read from the lists rather than from the built atlas data, so this works in a
    fresh clone before anything has been generated.
    """
    found: dict[str, str] = {}
    for path in sorted((ROOT / "repo-lists").glob("*.txt")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            candidate = line.split("#")[0].strip()
            if SLUG_RE.fullmatch(candidate):
                found.setdefault(candidate, path.name)
    return found


def clone(slug: str, into: pathlib.Path) -> None:
    """Shallow clone, no submodules, no hooks, no credential prompt.

    --recurse-submodules is deliberately absent: a submodule is a second
    repository nobody catalogued, arriving under the name of one that was.
    """
    # Inherit the environment and add one variable, rather than replacing it. The
    # first version passed only PATH, which on Windows leaves git without
    # SystemRoot and getaddrinfo fails before any network call is made: a DNS
    # error that looks exactly like the repository not existing.
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"       # fail on a private repo, never prompt
    subprocess.run(
        ["git", "clone", "--depth", "1", "--no-tags", "--config", "core.hooksPath=",
         f"https://github.com/{slug}.git", str(into)],
        check=True, capture_output=True, text=True, env=env,
    )


def scan_tree(clone_dir: pathlib.Path) -> list[str]:
    """Run the repository's own heuristic scanner over every readable file."""
    findings: list[str] = []
    for path in sorted(clone_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                findings.append(f"INFO skipped {path.relative_to(clone_dir)}, larger than "
                                f"{MAX_SCAN_BYTES} bytes")
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue          # binary or unreadable; the heuristics do not apply
        findings.extend(security.scan_text(path.relative_to(clone_dir), text))
    return findings


def skill_dirs(clone_dir: pathlib.Path) -> list[pathlib.Path]:
    """Directories holding a SKILL.md. That file is what makes a folder a skill."""
    return sorted({definition.parent for definition in clone_dir.rglob("SKILL.md")
                   if not any(part in SKIP_DIRS for part in definition.parts)})


def install_name(slug: str, folder: pathlib.Path, clone_dir: pathlib.Path) -> str:
    """Namespace by owner so two repositories cannot claim one skill name.

    Skill folders are named for what they do, so 'review', 'design' and 'test'
    collide across packs constantly. Without the owner prefix the second install
    would quietly replace the first.
    """
    relative = folder.relative_to(clone_dir)
    tail = relative.name if str(relative) != "." else slug.split("/")[1]
    owner = slug.split("/")[0]
    return re.sub(r"[^a-z0-9]+", "-", f"{owner}-{tail}".lower()).strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", nargs="?", help="owner/repo, as catalogued in repo-lists/")
    parser.add_argument("--home", default=str(pathlib.Path.home()))
    parser.add_argument("--dry-run", action="store_true",
                        help="scan and report, write nothing")
    parser.add_argument("--accept-findings", action="store_true",
                        help="install despite scanner findings, after reading them")
    parser.add_argument("--list", action="store_true",
                        help="list catalogued repositories that ship a skill pack")
    args = parser.parse_args()

    catalog = catalogued_slugs()

    if args.list:
        print(f"{len(catalog)} catalogued repositories. Any of them may be passed as a slug;")
        print("the scan decides, not the name. Likely skill packs by lane:\n")
        for slug, lane in sorted(catalog.items()):
            if "skill" in lane or "skill" in slug.lower():
                print(f"  {slug:<52} {lane}")
        return 0

    if not args.slug:
        parser.error("a slug is required unless --list is given")

    slug = args.slug.strip().rstrip("/")
    if slug not in catalog:
        print(f"REFUSED: {slug} is not in repo-lists/.\n", file=sys.stderr)
        print("This is the typosquat gate, not a formality. A skills marketplace is exactly\n"
              "where a near-name repository gets installed by mistake, and the catalog\n"
              "already knows which one was vetted. Add it to a lane first, with its licence\n"
              "and dates recorded, then run this again.", file=sys.stderr)
        near = [s for s in catalog if s.split("/")[-1].lower() == slug.split("/")[-1].lower()]
        if near:
            print(f"\nCatalogued repositories with that name: {', '.join(near)}", file=sys.stderr)
        return 2

    print(f"Slug     : {slug}")
    print(f"Catalog  : repo-lists/{catalog[slug]}")

    with tempfile.TemporaryDirectory(prefix="catalog-skill-") as temporary:
        clone_dir = pathlib.Path(temporary) / "repo"
        try:
            clone(slug, clone_dir)
        except subprocess.CalledProcessError as error:
            print(f"\nClone failed: {(error.stderr or '').strip()}", file=sys.stderr)
            return 1
        print(f"Cloned   : shallow, no submodules, hooks disabled")

        findings = scan_tree(clone_dir)
        serious = [f for f in findings if f.startswith(("CRITICAL", "HIGH"))]
        print(f"Scanned  : {len(findings)} finding(s), {len(serious)} at HIGH or above")
        for finding in findings:
            print(f"  {finding}")
        if security.has_scanner_error(findings):
            print("\nA scanner did not run. Treat the result as incomplete.", file=sys.stderr)

        packs = skill_dirs(clone_dir)
        if not packs:
            print("\nNothing to install: no SKILL.md anywhere in this repository.\n"
                  "It is catalogued for reference, which is a different thing from being a "
                  "skill pack.", file=sys.stderr)
            return 1
        print(f"Skills   : {len(packs)} folder(s) with a SKILL.md")

        if serious and not args.accept_findings:
            print(f"\nREFUSED: {len(serious)} finding(s) at HIGH or above, listed above.\n"
                  "Read them. Most heuristic hits on a skill pack are documentation about an\n"
                  "attack rather than an attack, which is why this refuses rather than deletes.\n"
                  "Re-run with --accept-findings once you have decided they are benign.",
                  file=sys.stderr)
            return 2

        home = pathlib.Path(args.home).expanduser()
        planned = []
        for folder in packs:
            name = install_name(slug, folder, clone_dir)
            for client, root in SKILL_ROOTS.items():
                target = home / root / name
                marker = target / ".installed-from"
                if target.exists() and not marker.is_file():
                    print(f"\nREFUSED: {target} already exists and was not installed by this "
                          f"script.\nNothing here removes or replaces a capability somebody else "
                          f"put there.", file=sys.stderr)
                    return 2
                planned.append((client, folder, target, name))

        for client, folder, target, name in planned:
            if args.dry_run:
                print(f"  would install {name:<40} -> {target}")
                continue
            if target.exists():
                shutil.rmtree(target)          # only ever a previous install of ours
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(folder, target,
                            ignore=shutil.ignore_patterns(*SKIP_DIRS))
            (target / ".installed-from").write_text(
                f"{slug}\nlane: repo-lists/{catalog[slug]}\n", encoding="utf-8")
            print(f"  installed {name:<40} -> {target}")

    print("\nDry run, nothing written." if args.dry_run else
          "\nInstalled. Nothing from the repository was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
