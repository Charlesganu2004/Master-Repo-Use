"""Read owned capability metadata without executing or shortening definitions."""
from __future__ import annotations

import hashlib
import pathlib
import re


def owned_agents(repo: pathlib.Path) -> list[dict]:
    records = []
    for path in sorted((repo / "agents").glob("*.md")):
        body = path.read_text(encoding="utf-8-sig")
        heading = re.search(r"^#\s+(.+)$", body, re.M)
        if not heading:
            continue
        def field(name: str) -> str:
            found = re.search(rf"^\*\*{re.escape(name)}:\*\*\s*(.+)$", body, re.M)
            return found.group(1).strip() if found else ""
        role = field("Job")
        if not role:
            continue  # supporting documents are not invented agent roles
        records.append({
            "id": f"agent-{path.stem}", "name": heading.group(1),
            "role": role, "category": field("Category") or "Specialist",
            "path": path.relative_to(repo).as_posix(),
            "detail": f"{role}. Read the full role contract for its scope, tools, approval gates and handoff requirements.",
        })
    return records


def read_owned_definition(repo: pathlib.Path, relative: str) -> dict | None:
    """Only local owned Markdown definitions, never a path outside these roots."""
    path = (repo / relative).resolve()
    roots = [(repo / folder).resolve() for folder in ("skills", "agents")]
    if path.suffix != ".md" or not any(path.is_relative_to(root) for root in roots):
        return None
    if not path.is_file():
        return None
    raw = path.read_bytes()
    return {"path": path.relative_to(repo.resolve()).as_posix(),
            "body": raw.decode("utf-8"), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}
