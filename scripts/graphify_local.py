#!/usr/bin/env python3
"""Local graphify across many folders: index each project, connect them in one graph.

Graphify is catalogued (Graphify-Labs/graphify, installed from PyPI as graphifyy)
and wrapped by skills/master-graphify, which every harness ships. That covers the
instruction half: a model is told the graph is the cheaper tool. This covers the
machine half, which a skill cannot do. The graphs have to exist, for every project
you actually work in, and they have to be connected so a question can cross repos.

    python scripts/graphify_local.py --discover        find projects on this machine
    python scripts/graphify_local.py --index all       index each, code only, then merge
    python scripts/graphify_local.py --status          what is indexed, how fresh, how big
    python scripts/graphify_local.py --query "..."     ask the merged graph, capped output

Indexing is `graphify extract --code-only`: local tree-sitter AST parsing, no API
key, nothing leaves the machine. The model-backed pass over docs, PDFs and images
is never run from here. That pass is the one part of graphify that can leave the
machine, and rule 1 of the standing pipeline says to index locally.

The registry lives at ~/.graphify/projects.json, NOT in this repository: it holds
this machine's folder layout, which is machine-specific config.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import time

HOME = pathlib.Path.home()
GRAPHIFY_HOME = pathlib.Path(os.environ.get("GRAPHIFY_HOME", HOME / ".graphify"))
REGISTRY = GRAPHIFY_HOME / "projects.json"
GLOBAL_GRAPH = GRAPHIFY_HOME / "global-graph.json"
# Where a project is recognised: a repository, or a dependency manifest.
MARKERS = (".git", "package.json", "pyproject.toml", "Cargo.toml", "requirements.txt", "go.mod")
DEFAULT_ROOTS = ("Downloads", "Documents", "Desktop", "dev", "source", "repos", "projects")
SKIP_PARTS = {"node_modules", "venv", ".venv", "site-packages", "graphify-out", "_site",
              "build", "dist", ".git", "__pycache__", "AppData"}
# Folders that look like projects and are not: package caches, backups of things
# already removed, and git worktrees, which are a second copy of a repo already
# registered. Matched case-insensitively against any path part.
SKIP_PATTERNS = ("backup", "removed-", ".worktrees", "-cache", "cache@", "@@@")
CODE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".h",
                 ".cpp", ".cs", ".rb", ".php", ".swift", ".kt", ".m", ".scala", ".sh", ".ino"}
# The clients this repository's harness installs into, each with graphify's own
# name for it. `graphify install --platform P` copies the skill; it does not edit
# CLAUDE.md or register a hook, which the per-client `graphify <client> install`
# commands do. Those are left alone: they write into protected files.
CLIENT_PLATFORMS = {"claude-code": "claude", "codex": "codex", "cursor": "cursor",
                    "gemini-cli": "gemini", "antigravity": "antigravity"}


def cli() -> str:
    found = shutil.which("graphify")
    if found:
        return found
    fallback = HOME / ".graphify" / "venv" / "Scripts" / "graphify.exe"
    if fallback.exists():
        return str(fallback)
    raise SystemExit("graphify is not installed. Install it with:\n"
                     "  uv tool install graphifyy   (or pipx install graphifyy)")


def run(*args: str, timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run([cli(), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def load() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {"projects": {}}


def save(registry: dict) -> None:
    GRAPHIFY_HOME.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def tag_for(path: pathlib.Path, taken: set) -> str:
    tag = path.name.lower().replace(" ", "-")
    while tag in taken:
        tag = f"{path.parent.name.lower()}-{tag}"
    return tag


def discover(roots: list, depth: int) -> list:
    """Walk, prune and keep going past unreadable paths.

    glob was the obvious way and it dies on the first broken junction: a venv's
    lib64 link raises WinError 1920 mid-iteration and takes the whole scan with
    it. os.walk prunes as it goes and reports errors instead of raising.
    """
    found = []
    for root in roots:
        base = pathlib.Path(root)
        if not base.is_absolute():
            base = HOME / base
        if not base.is_dir():
            continue
        for current, directories, files in os.walk(base, onerror=lambda error: None):
            here = pathlib.Path(current)
            level = len(here.relative_to(base).parts)
            directories[:] = [d for d in directories if d not in SKIP_PARTS] if level < depth else []
            if any(pattern in part.lower() for part in here.parts for pattern in SKIP_PATTERNS):
                directories[:] = []
                continue
            if any(marker in files or marker in set(directories) or (here / marker).exists()
                   for marker in MARKERS):
                if here != base and here not in found:
                    found.append(here)
                    directories[:] = []          # a project's subfolders are its own business
    return sorted(found)


def has_code(project: pathlib.Path) -> bool:
    """A cheap look, so a folder with no source is never handed to the indexer."""
    seen = 0
    for path in project.rglob("*"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in CODE_SUFFIXES:
            seen += 1
            if seen >= 3:
                return True
    return False


def index(tag: str, entry: dict) -> dict:
    project = pathlib.Path(entry["path"])
    if not project.is_dir():
        entry["error"] = "folder is gone"
        return entry
    started = time.time()
    result = run("extract", str(project), "--code-only", "--no-cluster")
    entry["seconds"] = round(time.time() - started, 1)
    graph = project / "graphify-out" / "graph.json"
    if result.returncode != 0 or not graph.exists():
        tail = (result.stderr or result.stdout or "extract failed").strip().splitlines()
        entry["error"] = tail[-1][:200] if tail else "extract failed"
        entry.pop("nodes", None)
        return entry
    data = json.loads(graph.read_text(encoding="utf-8"))
    entry.update({"graph": str(graph), "nodes": len(data.get("nodes", [])),
                  "edges": len(data.get("edges", [])),
                  "indexedAt": time.strftime("%Y-%m-%dT%H:%M:%S"), "error": None})
    merged = run("global", "add", str(graph), "--as", tag)
    entry["inGlobal"] = merged.returncode == 0
    if merged.returncode != 0:
        entry["globalError"] = (merged.stderr or merged.stdout).strip()[:200]
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--discover", action="store_true", help="find projects and register them")
    parser.add_argument("--roots", nargs="*", default=list(DEFAULT_ROOTS))
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--add", metavar="PATH", help="register one folder")
    parser.add_argument("--as", dest="tag", help="tag for --add")
    parser.add_argument("--index", metavar="TAG", help="index one project, or all")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--query", metavar="QUESTION")
    parser.add_argument("--budget", type=int, default=400, help="token cap on query output")
    parser.add_argument("--query-tag", help="query one project instead of the merged graph")
    parser.add_argument("--install-clients", action="store_true",
                        help="copy graphify's own skill into each client this repo supports")
    args = parser.parse_args()
    registry = load()

    if args.discover:
        taken = set(registry["projects"])
        known = {pathlib.Path(e["path"]) for e in registry["projects"].values()}
        added = 0
        for project in discover(args.roots, args.depth):
            if project in known or not has_code(project):
                continue
            tag = tag_for(project, taken)
            taken.add(tag)
            registry["projects"][tag] = {"path": str(project)}
            added += 1
            print(f"registered {tag:34} {project}")
        save(registry)
        print(f"{added} added, {len(registry['projects'])} registered in {REGISTRY}")

    if args.add:
        project = pathlib.Path(args.add).resolve()
        tag = args.tag or tag_for(project, set(registry["projects"]))
        registry["projects"][tag] = {"path": str(project)}
        save(registry)
        print(f"registered {tag} {project}")

    if args.index:
        targets = list(registry["projects"]) if args.index == "all" else [args.index]
        for tag in targets:
            entry = registry["projects"].get(tag)
            if entry is None:
                print(f"{tag}: not registered")
                continue
            entry = index(tag, entry)
            registry["projects"][tag] = entry
            save(registry)
            if entry.get("error"):
                print(f"{tag:34} FAILED  {entry['error']}")
            else:
                print(f"{tag:34} {entry['nodes']:>6} nodes {entry['edges']:>6} edges "
                      f"{entry['seconds']:>7}s global={entry.get('inGlobal')}")

    if args.install_clients:
        for client, platform in CLIENT_PLATFORMS.items():
            result = run("install", "--platform", platform)
            lines = (result.stdout or result.stderr).strip().splitlines()
            print(f"{client:14} {platform:12} {'ok' if result.returncode == 0 else 'FAILED'}: "
                  f"{lines[-1][:110] if lines else ''}")

    if args.status:
        listed = run("global", "list")
        print(f"registry {REGISTRY}")
        print(f"global   {GLOBAL_GRAPH} {'(present)' if GLOBAL_GRAPH.exists() else '(not built yet)'}")
        for tag, entry in sorted(registry["projects"].items()):
            state = entry.get("error") or (f"{entry.get('nodes', 0):,} nodes, "
                                           f"{entry.get('edges', 0):,} edges, "
                                           f"indexed {entry.get('indexedAt', 'never')}")
            print(f"  {tag:34} {state}")
            print(f"  {'':34} {entry['path']}")
        print((listed.stdout or listed.stderr).strip()[:1500])

    if args.query:
        target = str(GLOBAL_GRAPH)
        if args.query_tag:
            entry = registry["projects"].get(args.query_tag)
            if not entry or not entry.get("graph"):
                raise SystemExit(f"{args.query_tag} has no graph yet; run --index {args.query_tag}")
            target = entry["graph"]
        result = run("query", args.query, "--budget", str(args.budget), "--graph", target)
        print(result.stdout or result.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
