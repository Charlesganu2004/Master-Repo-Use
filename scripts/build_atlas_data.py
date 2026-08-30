#!/usr/bin/env python3
"""Generate atlas-data.json, the single data layer every atlas design reads.

Five designs share this file. Without it they drift, and a lane added to one
quietly goes missing from the other four.

Every lane is grounded in a file that exists. Nothing here is invented to pad a
count: a lane is a catalog list, a script, a workflow, a test module, a document,
or a named stage of the runtime path. If the file is deleted the lane disappears
on the next build, which is the behaviour you want from a map.

Components inside a lane are its real contents: the slugs in a list, the CLI
flags of a script, the classes in a test module, the headings of a document.

Nothing private ships. Catalog slugs are never emitted, only counts, because this
file is published and the catalog composition is not.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Written to both places on purpose. The designs fetch it relative to themselves,
# and a hand-copied second file is exactly the kind of thing that drifts silently.
OUT = ROOT / "atlas-data.json"
OUT_DESIGNS = ROOT / "designs" / "atlas-data.json"
SLUG_RE = re.compile(r"[\w.-]+/[\w.-]+")

# Not lanes: one is the union of every other list, one is a publish control file.
NOT_A_LANE = {"all-curated", "public-allowlist"}

FAMILIES = [
    ("intake", "Intake and routing", "instruction"),
    ("surfaces", "Client surfaces", "capability"),
    ("identity", "Identity and policy", "control"),
    ("instructions", "Instruction layer", "instruction"),
    ("skills", "Skills", "capability"),
    ("tools", "Tools", "capability"),
    ("mcp", "MCP and connectors", "capability"),
    ("agents", "Agents", "capability"),
    ("plugins", "Plugins", "capability"),
    ("knowledge", "Knowledge and retrieval", "knowledge"),
    ("models", "Models and serving", "model"),
    ("hybrid", "Hybrid routing", "model"),
    ("validation", "Validation and safety", "control"),
    ("observability", "Observability", "control"),
    ("automation", "Automation", "delivery"),
    ("delivery", "Delivery", "delivery"),
    ("domain", "Domain lanes", "knowledge"),
]

# Runtime stages: the path a task actually takes. Each carries the command a
# person would run, per platform where they differ.
STAGES = [
    ("intake", "task-intake", "Task intake", "Normalizes the request and starts the system trace.", None),
    ("intake", "scope-resolver", "Scope resolver", "Picks the smallest safe set of resources for the task.", None),
    ("intake", "lane-match", "Lane matcher", "Maps the task to a catalog lane before inventing a dependency.", "grep -ril '<topic>' repo-lists/"),
    ("intake", "budget-check", "Budget check", "Decides whether the work fits the session token target.", "cat docs/TOKEN-BUDGET.md"),
    ("intake", "hardware-gate", "Hardware gate", "Reads real RAM, GPU and disk before recommending a local model.", "python scripts/local_model_advisor.py"),
    ("surfaces", "claude-code", "Claude Code", "Terminal, desktop, web and IDE agent surface.", "claude"),
    ("surfaces", "codex", "Codex", "Repository aware coding and system work surface.", "codex"),
    ("surfaces", "copilot", "GitHub Copilot", "Native GitHub assistant surface.", "gh copilot explain"),
    ("surfaces", "gemini", "Gemini", "Multimodal and hosted model surface.", "gemini"),
    ("surfaces", "opencode", "OpenCode", "Multi-provider client surface.", None),
    ("identity", "owner-approval-stage", "Owner approval", "Only Charles approves, by passcode or by pinned revision.", "gh pr comment <n> --body 'I approve <passcode>'"),
    ("identity", "workspace-trust", "Workspace trust", "Binds access to the active repository and workspace.", None),
    ("identity", "secret-scope", "Secret scope", "Keeps credentials out of committed files and prompts.", None),
    ("skills", "caveman-compact", "caveman-ultra-compact", "Maximum compression pass over one natural-language file.", "/caveman-ultra-compact <file>"),
    ("skills", "caveman-repo", "caveman-ultra-compact-repo", "The same rules across a whole repository.", "/caveman-ultra-compact-repo"),
    ("skills", "master-repo-auto", "master-repo-auto", "Auto mode rules, loaded on demand rather than every session.", None),
    ("tools", "rtk", "rtk", "CLI proxy, 60-90 percent off common dev command output.", "rtk <command>"),
    ("tools", "rtt", "reducethemtokens", "Compresses a repo to a signature skeleton for orientation.", "rtt ."),
    ("mcp", "github-mcp", "github-mcp-server", "Official GitHub MCP server.", None),
    ("mcp", "merge-guard", "mcp-merge-guard", "Merge gating over MCP. Link only, no licence.", None),
    ("plugins", "plugin-registry", "Plugin registry", "Marketplaces and installed plugin state.", "claude plugin list"),
    ("validation", "no-prune-hook", "No-prune hook", "Blocks deletion of skills, tools, MCP and catalog paths.", None),
    ("observability", "token-gain", "Token savings", "What the reducers actually saved.", "rtk gain"),
    ("delivery", "branch-pr", "Branch and PR", "Every change lands on a branch, never straight to main.", "git switch -c feature/<name>"),
]

ROUTES = [
    ("local-first", "Local first, hosted on miss", "Small local model answers; escalate only when it cannot.",
     ["hardware-gate", "claude-code"], "cheapest", "8 GB RAM minimum"),
    ("draft-review", "Local draft, hosted review", "Local model drafts, hosted model reviews and corrects.",
     ["hardware-gate", "claude-code", "codex"], "balanced", "16 GB RAM"),
    ("parallel-vote", "Parallel then vote", "Several models answer independently; disagreement triggers a third.",
     ["claude-code", "codex", "gemini"], "highest confidence", "hosted only"),
    ("skeleton-retrieve", "Skeleton then retrieve", "rtt maps the repo, the model retrieves only what it names.",
     ["rtt", "lane-match", "claude-code"], "large repositories", "any"),
    ("compress-forward", "Compress then forward", "Compress context locally before spending hosted tokens.",
     ["caveman-compact", "rtk", "claude-code"], "long documents", "any"),
    ("guarded-write", "Guarded write", "Any deletion passes the hook before the model acts.",
     ["no-prune-hook", "branch-pr"], "safety critical", "any"),
    ("audit-approve", "Audit then approve", "Deterministic audit proposes; the owner approves by passcode.",
     ["owner-approval-stage", "branch-pr"], "maintenance", "any"),
    ("vision-route", "Multimodal split", "Vision to a multimodal model, reasoning to a text model.",
     ["gemini", "claude-code"], "image and document work", "hosted only"),
    ("budget-cap", "Budget capped", "Stop and report rather than silently overspending a token target.",
     ["budget-check", "token-gain"], "fixed budgets", "any"),
    ("offline", "Fully offline", "No hosted call at any stage. Quality is bounded by the machine.",
     ["hardware-gate", "rtt", "caveman-compact"], "air-gapped work", "16 GB RAM minimum"),
]

HARDWARE = [
    ("4gb", "4 GB RAM", "Hosted API only", 4,
     "Local inference will swap and thrash. That is the honest answer, not a limit to engineer around.", []),
    ("8gb", "8 GB RAM", "Smallest useful local tier", 8,
     "3B class models at 4-bit quantization, with headroom left for the OS.", ["phi3:mini", "gemma2:2b"]),
    ("16gb", "16 GB RAM", "Comfortable local tier", 16,
     "7B to 8B class at 4-bit. The common developer laptop.", ["phi3:medium", "gemma2:9b"]),
    ("32gb", "32 GB RAM", "Large local tier", 32,
     "13B to 14B class, or 7B at higher precision.", ["phi4", "gemma2:27b"]),
    ("apple", "Apple silicon", "Unified memory is shared", 0,
     "GPU and CPU draw on one pool, so usable model size sits below the headline number. Metal acceleration is automatic in Ollama.", []),
    ("gpu", "Discrete GPU", "VRAM is the real limit", 0,
     "System RAM does not substitute. A 12 GB card runs roughly what a 16 GB unified machine runs.", []),
]

FAMILY_HINTS = [
    (("mcp",), "mcp"), (("skill",), "skills"), (("agent", "adk"), "agents"),
    (("copilot", "client"), "surfaces"), (("local-models", "llm", "model"), "models"),
    (("rag", "knowledge", "live-rag", "multi-model"), "knowledge"),
    (("security", "observability"), "validation"),
    (("cost", "context", "token"), "hybrid"),
    (("design", "ui", "app-", "hackathon"), "delivery"),
]
KIND_HINTS = [
    (("security", "observability", "merge", "guardian", "approval", "freshness", "audit"), "control"),
    (("model", "llm", "hardware"), "model"),
    (("rag", "knowledge", "article", "spatial", "doc"), "knowledge"),
    (("design", "app-", "hackathon", "site", "pages"), "delivery"),
]


def pick(stem: str, hints, default: str) -> str:
    for needles, value in hints:
        if any(n in stem for n in needles):
            return value
    return default


def first_comment(path: pathlib.Path, markers: tuple[str, ...]) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            text = line.strip()
            for marker in markers:
                if text.startswith(marker) and len(text) > len(marker) + 3:
                    return text.lstrip(marker + " ").strip().rstrip(".") + "."
    except OSError:
        pass
    return ""


def lane(lid, name, family, kind, source, description, count, catalog=False) -> dict:
    return {"id": lid, "name": name, "family": family, "kind": kind, "source": source,
            "description": description or f"{name}.", "count": count, "catalog": catalog}


def catalog_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / "repo-lists").glob("*.txt")):
        if path.stem in NOT_A_LANE:
            continue
        slugs = []
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            candidate = text.split("#")[0].strip()
            if SLUG_RE.fullmatch(candidate):
                slugs.append(candidate)
        lid = f"cat-{path.stem}"
        lanes.append(lane(lid, path.stem.replace("-", " ").title(),
                          pick(path.stem, FAMILY_HINTS, "domain"),
                          pick(path.stem, KIND_HINTS, "capability"),
                          f"repo-lists/{path.name}",
                          first_comment(path, ("#",)), len(slugs), catalog=True))
    return lanes, comps


def script_lanes() -> tuple[list, list]:
    """Each script is a capability. Its components are its CLI flags."""
    lanes, comps = [], []
    for path in sorted((ROOT / "scripts").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        lid = f"tool-{path.stem}"
        flags = sorted(set(re.findall(r'add_argument\(\s*"(--[\w-]+)"', path.read_text(encoding="utf-8"))))
        fam = pick(path.stem, FAMILY_HINTS, "tools")
        kind = pick(path.stem, KIND_HINTS, "capability")
        lanes.append(lane(lid, path.stem.replace("_", " "), fam, kind,
                          f"scripts/{path.name}", first_comment(path, ('"""',)), len(flags) or 1))
        cmd = f"python scripts/{path.name}"
        comps.append({"id": f"{lid}-run", "name": f"run {path.stem}", "lane": lid, "family": fam,
                      "kind": kind, "detail": first_comment(path, ('"""',)) or f"Runs {path.name}.",
                      "cmd": {"windows": cmd, "wsl": f"python3 scripts/{path.name}",
                              "macos": f"python3 scripts/{path.name}", "linux": f"python3 scripts/{path.name}"}})
        for index, flag in enumerate(flags[:6]):
            comps.append({"id": f"{lid}{flag}", "name": flag, "lane": lid, "family": fam, "kind": kind,
                          "detail": f"Option of {path.name}.", "order": index + 1,
                          "cmd": {k: f"{cmd} {flag}" for k in ("windows", "wsl", "macos", "linux")}})
    return lanes, comps


def workflow_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        lid = f"flow-{path.stem}"
        text = path.read_text(encoding="utf-8")
        jobs = re.findall(r"^  ([a-z][\w-]*):\s*$", text, re.M)
        name = re.search(r"^name:\s*(.+)$", text, re.M)
        lanes.append(lane(lid, (name.group(1).strip() if name else path.stem), "automation", "control",
                          f".github/workflows/{path.name}",
                          f"GitHub Actions workflow with {len(jobs)} job(s).", len(jobs) or 1))
        for index, job in enumerate(jobs[:8]):
            comps.append({"id": f"{lid}-{job}", "name": job, "lane": lid, "family": "automation",
                          "kind": "control", "detail": f"Job in {path.name}.", "order": index,
                          "cmd": {k: f"gh workflow run {path.name}" for k in ("windows", "wsl", "macos", "linux")}})
    return lanes, comps


def test_lanes() -> tuple[list, list]:
    """Each test module is a guarantee. Its components are its test classes."""
    lanes, comps = [], []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        lid = f"test-{path.stem}"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        doc = (ast.get_docstring(tree) or "").split("\n")[0]
        lanes.append(lane(lid, path.stem.replace("test_", "").replace("_", " "),
                          "validation", "control", f"tests/{path.name}", doc, len(classes) or 1))
        for index, cls in enumerate(classes):
            comps.append({"id": f"{lid}-{cls}", "name": cls, "lane": lid, "family": "validation",
                          "kind": "control", "detail": f"Guarantee pinned by {path.name}.", "order": index,
                          "cmd": {k: f"python -m unittest tests.{path.stem}" for k in ("windows", "wsl", "macos", "linux")}})
    return lanes, comps


def doc_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / "docs").glob("*.md")):
        lid = f"doc-{path.stem.lower()}"
        text = path.read_text(encoding="utf-8", errors="replace")
        heads = re.findall(r"^##\s+(.+)$", text, re.M)
        title = re.search(r"^#\s+(.+)$", text, re.M)
        lanes.append(lane(lid, (title.group(1).strip() if title else path.stem), "knowledge", "knowledge",
                          f"docs/{path.name}", f"Reference document with {len(heads)} section(s).",
                          len(heads) or 1))
        for index, head in enumerate(heads[:6]):
            comps.append({"id": f"{lid}-{index}", "name": head[:48], "lane": lid, "family": "knowledge",
                          "kind": "knowledge", "detail": f"Section of {path.name}.", "order": index})
    return lanes, comps


def stage_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    grouped: dict[str, list] = {}
    for family, cid, name, detail, cmd in STAGES:
        grouped.setdefault(family, []).append((cid, name, detail, cmd))
    fam_names = {f: n for f, n, _ in FAMILIES}
    fam_kinds = {f: k for f, _, k in FAMILIES}
    for family, entries in grouped.items():
        lid = f"sys-{family}"
        lanes.append(lane(lid, fam_names.get(family, family), family, fam_kinds.get(family, "capability"),
                          "runtime", f"Runtime stage: {fam_names.get(family, family).lower()}.", len(entries)))
        for index, (cid, name, detail, cmd) in enumerate(entries):
            comps.append({"id": cid, "name": name, "lane": lid, "family": family,
                          "kind": fam_kinds.get(family, "capability"), "detail": detail, "order": index,
                          "cmd": {k: cmd for k in ("windows", "wsl", "macos", "linux")} if cmd else None})
    return lanes, comps


def hook_lanes() -> tuple[list, list]:
    """Hooks are the zero-token enforcement layer, so they get their own lanes."""
    lanes, comps = [], []
    for path in sorted((ROOT / "scripts" / "hooks").glob("*.py")):
        lid = f"hook-{path.stem}"
        text = path.read_text(encoding="utf-8")
        guards = sorted(set(re.findall(r"^([A-Z_]{4,})\s*=", text, re.M)))
        lanes.append(lane(lid, path.stem.replace("_", " "), "validation", "control",
                          f"scripts/hooks/{path.name}", first_comment(path, ('"""',)),
                          len(guards) or 1))
        for index, guard in enumerate(guards[:6]):
            comps.append({"id": f"{lid}-{guard}", "name": guard, "lane": lid, "family": "validation",
                          "kind": "control", "detail": f"Rule table in {path.name}.", "order": index})
    return lanes, comps


def skill_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        lid = f"skill-{path.parent.name}"
        text = path.read_text(encoding="utf-8")
        heads = re.findall(r"^##\s+(.+)$", text, re.M)
        desc = re.search(r"^description:\s*(.+)$", text, re.M)
        lanes.append(lane(lid, path.parent.name, "skills", "capability",
                          f"skills/{path.parent.name}/SKILL.md",
                          (desc.group(1).strip() if desc else ""), len(heads) or 1))
        for index, head in enumerate(heads[:6]):
            comps.append({"id": f"{lid}-{index}", "name": head[:48], "lane": lid, "family": "skills",
                          "kind": "capability", "detail": f"Rule group in {path.parent.name}.",
                          "order": index})
    return lanes, comps


def build() -> dict:
    lanes, comps = [], []
    for producer in (stage_lanes, catalog_lanes, script_lanes, workflow_lanes,
                 test_lanes, doc_lanes, hook_lanes, skill_lanes):
        l, c = producer()
        lanes.extend(l)
        comps.extend(c)

    routes = [{"id": r[0], "name": r[1], "detail": r[2], "members": r[3],
               "bestFor": r[4], "requires": r[5]} for r in ROUTES]

    by_id = {c["id"]: c for c in comps}
    for route in routes:
        for member in route["members"]:
            if member in by_id:
                by_id[member].setdefault("routes", []).append(route["id"])
        for a, b in zip(route["members"], route["members"][1:]):
            for x, y in ((a, b), (b, a)):
                if x in by_id and y != x:
                    by_id[x].setdefault("connects", [])
                    if y not in by_id[x]["connects"]:
                        by_id[x]["connects"].append(y)

    # Lane level connections, so a design can draw lane-to-lane wiring.
    lane_of = {c["id"]: c["lane"] for c in comps}
    for route in routes:
        route["lanes"] = sorted({lane_of[m] for m in route["members"] if m in lane_of})

    return {
        "meta": {"lanes": len(lanes), "components": len(comps), "routes": len(routes),
                 "families": len(FAMILIES),
                 "note": "Generated by scripts/build_atlas_data.py. Do not hand-edit."},
        "families": [{"id": f, "name": n, "kind": k} for f, n, k in FAMILIES],
        "lanes": lanes,
        "components": comps,
        "routes": routes,
        "hardware": [{"id": i, "label": l, "verdict": v, "gb": g, "detail": d, "models": m}
                     for i, l, v, g, d, m in HARDWARE],
    }


def main() -> int:
    data = build()
    payload = json.dumps(data, indent=1)
    OUT.write_text(payload, encoding="utf-8")
    if OUT_DESIGNS.parent.is_dir():
        OUT_DESIGNS.write_text(payload, encoding="utf-8")
    m = data["meta"]
    print("atlas-data.json written to root and designs/")
    for key in ("lanes", "components", "routes", "families"):
        print(f"  {key:<11}{m[key]}")
    families: dict[str, int] = {}
    for entry in data["lanes"]:
        families[entry["family"]] = families.get(entry["family"], 0) + 1
    print("  lanes per family:", ", ".join(f"{k} {v}" for k, v in sorted(families.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
