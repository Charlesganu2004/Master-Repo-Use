#!/usr/bin/env python3
"""Build (and verify) the privacy-safe public Pages payload.

The private repository keeps repo-by-repo lifecycle and security detail in
docs/catalog-status.json. GitHub Pages on a personal Pro plan is PUBLIC even when
the source repository is private, so the deployed artifact must carry aggregate
information only:

    updated · policy thresholds · HEALTHY/STALE/REVIEW/REMOVE counts

Never: repository names, notes, findings, scanner output, or override reasons.

Usage:
    python scripts/build_public_site.py                 # write _site/docs/catalog-status.json
    python scripts/build_public_site.py --verify-only   # fail if the artifact leaks
"""
from __future__ import annotations

import argparse
import html.parser
import datetime as dt
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE_STATE = ROOT / "docs" / "catalog-status.json"
SITE = ROOT / "_site"
PRIVATE_INDEX = ROOT / "index.html"
PUBLIC_STATE = SITE / "docs" / "catalog-status.json"
PUBLIC_SVG = SITE / "docs" / "catalog-status.svg"
PUBLIC_INDEX = SITE / "index.html"
PRIVATE_DESIGN_STUDIO = ROOT / "design-options.html"
PRIVATE_DESIGN_STUDIO_JS = ROOT / "design-options.js"
PUBLIC_DESIGN_STUDIO = SITE / "design-options.html"
PUBLIC_DESIGN_STUDIO_JS = SITE / "design-options.js"
PRIVATE_ATLAS_CSS = ROOT / "atlas.css"
PRIVATE_ATLAS_JS = ROOT / "atlas.js"
PUBLIC_ATLAS_CSS = SITE / "atlas.css"
PUBLIC_ATLAS_JS = SITE / "atlas.js"
PRIVATE_PROFILES = ROOT / "docs" / "hardware-profiles.json"
PUBLIC_PROFILES = SITE / "docs" / "hardware-profiles.json"
PUBLIC_VERSION = SITE / "version.json"
PRIVATE_DESIGNS = ROOT / "designs"
PUBLIC_DESIGNS = SITE / "designs"
PRIVATE_ATLAS_DATA = ROOT / "atlas-data.json"

# Keys allowed to reach the public artifact. Anything else is dropped by construction.
ALLOWED_TOP_LEVEL = {"updated", "policy", "counts", "public", "repos"}
ALLOWED_POLICY = {
    "stale_after_days",
    "adoption_review_days",
    "remove_stale_after_days",
    "archive_grace_days",
}
ALLOWED_COUNTS = {"HEALTHY", "STALE", "REVIEW", "REMOVE", "UNKNOWN"}

# Words that only ever appear in private security detail.
PRIVATE_WORDS = ("finding", "note", "gitleaks", "clamav", "semgrep", "trivy", "snyk", "osv", "scanner-error")

# The JSON payload must contain no owner/name pair at all. The SVG is prose, so it
# is checked against the real catalog instead and ordinary slashes never trip it.
REPO_SLUG = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9_.-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\b")


OWN_REPO = "Charlesganu2004/Master-Repo-Use"

# Slugs the owner has explicitly cleared for public display. The public setup page
# has to be able to say "install Ollama" and link to it, and a well-known upstream
# project reveals nothing about the private catalog's composition. Everything not
# listed here is still treated as private and blocked from the artifact.
PUBLIC_ALLOWLIST_FILE = ROOT / "repo-lists" / "public-allowlist.txt"


def public_allowlist() -> set[str]:
    """Owner-approved slugs that may appear in the public artifact."""
    if not PUBLIC_ALLOWLIST_FILE.exists():
        return set()
    allowed: set[str] = set()
    for line in PUBLIC_ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        slug = line.split("#", 1)[0].strip()
        if slug.count("/") == 1 and slug:
            allowed.add(slug)
    return allowed


def private_notes() -> set[str]:
    """Lifecycle/security notes from the private state. None may reach the public site."""
    if not PRIVATE_STATE.exists():
        return set()
    try:
        state = json.loads(PRIVATE_STATE.read_text(encoding="utf-8"))
    except ValueError:
        return set()
    notes = set()
    for row in state.get("repos") or []:
        note = str(row.get("note") or "").strip()
        if len(note) > 25:
            notes.add(note)
        for finding in row.get("findings") or []:
            notes.add(str(finding))
    return notes


def private_repo_names() -> set[str]:
    """Every repository slug the private side knows about, from state and lists."""
    names: set[str] = set()
    if PRIVATE_STATE.exists():
        try:
            state = json.loads(PRIVATE_STATE.read_text(encoding="utf-8"))
        except ValueError:
            state = {}
        for row in state.get("repos") or []:
            if isinstance(row, dict) and row.get("repo"):
                names.add(str(row["repo"]))
    for listing in (ROOT / "repo-lists").glob("*.txt"):
        if listing == PUBLIC_ALLOWLIST_FILE:
            continue
        for line in listing.read_text(encoding="utf-8").splitlines():
            slug = line.split("#", 1)[0].strip()
            if slug.count("/") == 1 and slug:
                names.add(slug)
    # Allowlisted upstreams are public by owner decision, so they are not "private
    # names" for leak-checking purposes. Subtracting last means adding a slug to a
    # private lane can never quietly re-privatise something already published.
    return names - public_allowlist()


class PrivateStripper(html.parser.HTMLParser):
    """Drop every element carrying a `data-private` attribute, and its subtree.

    The command center is one page serving two audiences. Run from a local clone it
    shows the full catalog; deployed to a public Pages site it must not. Marking the
    private parts in the markup keeps the two views from drifting apart.
    """

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.skip_depth = 0
        self.skip_tag: str | None = None
        self.removed = 0

    def _emit(self, text: str) -> None:
        if self.skip_depth == 0:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            if tag == self.skip_tag and tag not in self.VOID:
                self.skip_depth += 1
            return
        if any(name == "data-private" for name, _ in attrs):
            self.removed += 1
            if tag not in self.VOID:
                self.skip_depth, self.skip_tag = 1, tag
            return
        rebuilt = "".join(
            f" {name}" if value is None else f' {name}="{value}"' for name, value in attrs
        )
        self._emit(f"<{tag}{rebuilt}>")

    def handle_startendtag(self, tag, attrs):
        if self.skip_depth:
            return
        if any(name == "data-private" for name, _ in attrs):
            self.removed += 1
            return
        rebuilt = "".join(
            f" {name}" if value is None else f' {name}="{value}"' for name, value in attrs
        )
        self._emit(f"<{tag}{rebuilt}/>")

    def handle_endtag(self, tag):
        if self.skip_depth:
            if tag == self.skip_tag:
                self.skip_depth -= 1
                if self.skip_depth == 0:
                    self.skip_tag = None
            return
        self._emit(f"</{tag}>")

    def handle_data(self, data):
        self._emit(data)

    def handle_entityref(self, name):
        self._emit(f"&{name};")

    def handle_charref(self, name):
        self._emit(f"&#{name};")

    def handle_comment(self, data):
        self._emit(f"<!--{data}-->")

    def handle_decl(self, decl):
        self._emit(f"<!{decl}>")

    def unknown_decl(self, data):
        self._emit(f"<![{data}]>")

    def handle_pi(self, data):
        self._emit(f"<?{data}>")


def build_index() -> int:
    """Write the public index.html with all `data-private` content removed."""
    stripper = PrivateStripper()
    stripper.feed(PRIVATE_INDEX.read_text(encoding="utf-8"))
    stripper.close()
    PUBLIC_INDEX.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_INDEX.write_text("".join(stripper.out), encoding="utf-8")
    return stripper.removed


def build_design_studio() -> list[str]:
    """Publish every dependency-free user interface asset."""
    assets = (
        (PRIVATE_DESIGN_STUDIO, PUBLIC_DESIGN_STUDIO),
        (PRIVATE_DESIGN_STUDIO_JS, PUBLIC_DESIGN_STUDIO_JS),
        (PRIVATE_ATLAS_CSS, PUBLIC_ATLAS_CSS),
        (PRIVATE_ATLAS_JS, PUBLIC_ATLAS_JS),
    )
    missing = [source.name for source, _ in assets if not source.exists()]
    if missing:
        return [f"UI design studio assets are missing: {', '.join(missing)}"]

    for source, destination in assets:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return build_designs()


def build_designs() -> list[str]:
    """Publish the Atlas gallery, authored sources, and shared data layer.

    atlas-data.json carries lane names and counts, never catalog slugs. verify()
    checks that separately; a leak here would publish the catalog composition,
    which is the one thing this build exists to prevent.
    """
    if not PRIVATE_DESIGNS.is_dir():
        return ["designs/ is missing"]
    if not PRIVATE_ATLAS_DATA.exists():
        return ["atlas-data.json is missing; run scripts/build_atlas_data.py"]

    PUBLIC_DESIGNS.mkdir(parents=True, exist_ok=True)
    # This directory is generated output. Clear its top-level files before copying
    # so a design removed from the source tree cannot survive a later publication.
    # Nested directories are deliberately left alone because this builder owns only
    # the flat gallery assets below.
    for published in PUBLIC_DESIGNS.iterdir():
        if published.is_file() or published.is_symlink():
            published.unlink()

    for source in sorted(PRIVATE_DESIGNS.iterdir()):
        if source.suffix.lower() not in {
            ".html", ".js", ".css", ".json", ".ts", ".jsx", ".tsx"
        } or not source.is_file():
            continue
        # The two data files are rebuilt from the redacted payload below, never copied.
        if source.name in {"atlas-data.json", "atlas-data.js"}:
            continue
        (PUBLIC_DESIGNS / source.name).write_text(
            source.read_text(encoding="utf-8"), encoding="utf-8")

    public_payload = redact_atlas_data(json.loads(
        PRIVATE_ATLAS_DATA.read_text(encoding="utf-8")))
    rendered = json.dumps(public_payload, indent=1)
    (PUBLIC_DESIGNS / "atlas-data.json").write_text(rendered, encoding="utf-8")
    banner = "/* Redacted for publication by build_public_site.py. */\n"
    (PUBLIC_DESIGNS / "atlas-data.js").write_text(
        banner + "window.__ATLAS_DATA__ = " + rendered + ";\n", encoding="utf-8")
    return []


def redact_atlas_data(data: dict) -> dict:
    """Drop every component that carries a private catalog slug.

    Lanes stay, with their counts, because a lane name and a number reveal
    shape rather than composition. The entries inside them are the catalog, and
    the catalog is private. Routes that referenced a dropped component lose that
    member rather than pointing at nothing.
    """
    kept = [c for c in data.get("components", []) if not c.get("private")]
    keep_ids = {c["id"] for c in kept}

    for component in kept:
        for field in ("connects", "routes"):
            if field == "connects" and component.get("connects"):
                component["connects"] = [i for i in component["connects"] if i in keep_ids]

    routes = []
    for route in data.get("routes", []):
        trimmed = dict(route)
        trimmed["members"] = [m for m in route.get("members", []) if m in keep_ids]
        routes.append(trimmed)

    public = dict(data)
    public["components"] = kept
    public["routes"] = routes
    public["meta"] = dict(data.get("meta", {}))
    public["meta"]["components"] = len(kept)
    public["meta"]["redacted"] = True
    public["meta"]["note"] = "Catalog entries removed for publication."
    return public


def private_keys_present(raw: str, label: str) -> list[str]:
    """Private lifecycle/security FIELDS appearing in a published payload.

    Checked as object keys, not as substrings. The advisor dataset is prose-heavy and
    an English "Note that ..." is not a leak; a `note` or `findings` key copied over
    from the private catalog state is.
    """
    banned = {"note", "findings", "deep_scanned", "critical", "override", "archived"}
    problems: list[str] = []
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return [f"{label} is not valid JSON ({exc})"]

    def walk(node, path="") -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key.lower() in banned:
                    problems.append(f"{label} carries a private field: {path}{key}")
                walk(value, f"{path}{key}.")
        elif isinstance(node, list):
            for item in node:
                walk(item, path)

    walk(data)
    return problems


def profile_leaks(raw: str, label: str) -> list[str]:
    """Repository slugs in the advisor dataset that the owner has not made public.

    Checked against the *structured* slug fields rather than a regex over the whole
    file: prose like "CPU/NPU" or "Node/TypeScript" matches an owner/repo pattern and
    would otherwise produce false failures. Every declared slug must be allowlisted,
    and any private catalog name appearing anywhere in the file — including free text —
    is still a leak.
    """
    problems: list[str] = []
    allowed = public_allowlist() | {OWN_REPO}
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return [f"{label} is not valid JSON ({exc})"]

    for entry in data.get("repos") or []:
        slug = str(entry.get("slug") or "").strip()
        if slug and slug not in allowed:
            problems.append(f"{label} names a non-allowlisted repository: {slug}")
    for model in data.get("models") or []:
        tag = str(model.get("tag") or "").strip()
        if tag.count("/") == 1 and tag not in allowed:
            problems.append(f"{label} names a non-allowlisted repository: {tag}")

    for name in sorted(private_repo_names() - {OWN_REPO}):
        if name in raw:
            problems.append(f"{label} mentions a private catalogued repository: {name}")
    return problems


def build_profiles() -> list[str]:
    """Publish the hardware advisor's dataset, refusing anything not allowlisted.

    The Local Models tab is useless without this file, so it has to reach the public
    artifact. But it names repositories, which is exactly what the privacy contract
    exists to stop. The compromise: copy it verbatim, then assert that every slug it
    mentions is on the owner-controlled public allowlist. A slug added to the profile
    data without also being allowlisted fails the build rather than shipping quietly.
    """
    problems: list[str] = []
    if not PRIVATE_PROFILES.exists():
        return ["docs/hardware-profiles.json is missing; the Local Models tab will not render"]

    raw = PRIVATE_PROFILES.read_text(encoding="utf-8")
    problems.extend(profile_leaks(raw, "hardware-profiles.json"))
    problems.extend(private_keys_present(raw, "hardware-profiles.json"))

    if not problems:
        PUBLIC_PROFILES.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_PROFILES.write_text(raw, encoding="utf-8")
    return problems


def build_id() -> str:
    """Identify this publish. Commit SHA in CI, timestamp locally."""
    sha = os.environ.get("GITHUB_SHA", "").strip()
    if sha:
        return sha[:12]
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def build_version(identifier: str) -> None:
    """Publish version.json and stamp the same id into both public HTML pages.

    The page compares the two at runtime. Without this, a browser holding a cached
    index.html has no way to discover that a newer one exists -- and an ordinary
    refresh will not tell it, because the cached copy's own metadata looks current.
    """
    PUBLIC_VERSION.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_VERSION.write_text(
        json.dumps({
            "build_id": identifier,
            "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    for page_path, label in (
        (PUBLIC_INDEX, "index.html"),
        (PUBLIC_DESIGN_STUDIO, "design-options.html"),
    ):
        if not page_path.exists():
            print(f"::warning::{label} is missing; it could not be build stamped")
            continue
        page = page_path.read_text(encoding="utf-8")
        stamped = page.replace('<meta name="build-id" content="dev">',
                               f'<meta name="build-id" content="{identifier}">', 1)
        if stamped == page:
            print(f"::warning::{label} has no build-id placeholder; "
                  "stale-cache detection will not work")
        page_path.write_text(stamped, encoding="utf-8")


def build() -> dict:
    source = json.loads(PRIVATE_STATE.read_text(encoding="utf-8"))
    policy = source.get("policy") or {}
    counts = source.get("counts") or {}
    return {
        "updated": source.get("updated"),
        "policy": {key: policy[key] for key in ALLOWED_POLICY if key in policy},
        "counts": {key: counts.get(key, 0) for key in ("HEALTHY", "STALE", "REVIEW", "REMOVE", "UNKNOWN")},
        "public": True,
        "repos": [],
    }


def verify(payload: dict) -> list[str]:
    problems: list[str] = []

    extra = set(payload) - ALLOWED_TOP_LEVEL
    if extra:
        problems.append(f"unexpected top-level keys in public artifact: {sorted(extra)}")
    if payload.get("repos"):
        problems.append("public artifact contains per-repository rows")
    if payload.get("public") is not True:
        problems.append("public artifact is not flagged public")

    bad_policy = set(payload.get("policy") or {}) - ALLOWED_POLICY
    if bad_policy:
        problems.append(f"unexpected policy keys: {sorted(bad_policy)}")
    bad_counts = set(payload.get("counts") or {}) - ALLOWED_COUNTS
    if bad_counts:
        problems.append(f"unexpected count keys: {sorted(bad_counts)}")

    blob = json.dumps(payload)
    for word in PRIVATE_WORDS:
        if word in blob.lower():
            problems.append(f"public artifact mentions private detail: {word!r}")
    for slug in sorted(set(REPO_SLUG.findall(blob))):
        problems.append(f"public artifact leaks a repository slug: {slug}")

    catalog = private_repo_names()
    for name in sorted(catalog):
        if name in blob:
            problems.append(f"public artifact names a catalogued repository: {name}")

    if PUBLIC_SVG.exists():
        svg = PUBLIC_SVG.read_text(encoding="utf-8")
        for name in sorted(catalog):
            if name in svg:
                problems.append(f"public SVG names a catalogued repository: {name}")
        for word in PRIVATE_WORDS + ("critical",):
            if word in svg.lower():
                problems.append(f"public SVG mentions private detail: {word!r}")

    if PUBLIC_DESIGNS.is_dir():
        for published in sorted(PUBLIC_DESIGNS.iterdir()):
            if not published.is_file():
                continue
            text = published.read_text(encoding="utf-8", errors="replace")
            for name in sorted(catalog):
                if name in text:
                    problems.append(
                        f"published design {published.name} names a catalogued repository: {name}")

    if PUBLIC_PROFILES.exists():
        published = PUBLIC_PROFILES.read_text(encoding="utf-8")
        problems.extend(profile_leaks(published, "public hardware-profiles.json"))
        problems.extend(private_keys_present(published, "public hardware-profiles.json"))

    public_ui_assets = (
        (PUBLIC_INDEX, "public index.html"),
        (PUBLIC_ATLAS_CSS, "public atlas.css"),
        (PUBLIC_ATLAS_JS, "public atlas.js"),
        (PUBLIC_DESIGN_STUDIO, "public design-options.html"),
        (PUBLIC_DESIGN_STUDIO_JS, "public design-options.js"),
    )
    for page_path, label in public_ui_assets:
        if not page_path.exists():
            problems.append(f"{label} is missing")
            continue
        page = page_path.read_text(encoding="utf-8")
        if "data-private" in page:
            problems.append(f"{label} still contains data-private markup")
        # The index links to its own repository on purpose. Every other catalogued
        # repository remains private catalog content and cannot reach any UI asset.
        for name in sorted(catalog - {OWN_REPO}):
            if name in page:
                problems.append(f"{label} names a catalogued repository: {name}")
        for note in sorted(private_notes()):
            if note in page:
                problems.append(f"{label} contains a private note: {note[:50]}...")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="check the already-written _site artifact instead of rebuilding it",
    )
    args = parser.parse_args()

    if args.verify_only:
        if not PUBLIC_STATE.exists():
            print(f"error: {PUBLIC_STATE} does not exist; build the site first", file=sys.stderr)
            return 1
        payload = json.loads(PUBLIC_STATE.read_text(encoding="utf-8"))
    else:
        payload = build()
        PUBLIC_STATE.parent.mkdir(parents=True, exist_ok=True)
        PUBLIC_STATE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        removed = build_index()
        print(f"public index.html written ({removed} private element(s) removed)")
        profile_problems = build_profiles()
        if profile_problems:
            for problem in profile_problems:
                print(f"PRIVACY FAILURE: {problem}", file=sys.stderr)
            return 1
        print("public hardware-profiles.json written (all slugs owner-allowlisted)")
        studio_problems = build_design_studio()
        if studio_problems:
            for problem in studio_problems:
                print(f"PRIVACY FAILURE: {problem}", file=sys.stderr)
            return 1
        print("public UI design studio written")
        identifier = build_id()
        build_version(identifier)
        print(f"version.json written (build {identifier})")

    problems = verify(payload)
    if problems:
        for problem in problems:
            print(f"PRIVACY FAILURE: {problem}", file=sys.stderr)
        return 1

    counts = payload["counts"]
    print(
        "public artifact OK — aggregate only "
        f"(healthy {counts['HEALTHY']} · stale {counts['STALE']} · "
        f"review {counts['REVIEW']} · remove {counts['REMOVE']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
