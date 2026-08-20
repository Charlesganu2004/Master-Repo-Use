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
import json
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

# Keys allowed to reach the public artifact. Anything else is dropped by construction.
ALLOWED_TOP_LEVEL = {"updated", "policy", "counts", "public", "repos"}
ALLOWED_POLICY = {
    "stale_after_days",
    "adoption_review_days",
    "remove_stale_after_days",
    "archive_grace_days",
}
ALLOWED_COUNTS = {"HEALTHY", "STALE", "REVIEW", "REMOVE"}

# Words that only ever appear in private security detail.
PRIVATE_WORDS = ("finding", "note", "gitleaks", "clamav", "semgrep", "trivy", "snyk", "osv", "scanner-error")

# The JSON payload must contain no owner/name pair at all. The SVG is prose, so it
# is checked against the real catalog instead and ordinary slashes never trip it.
REPO_SLUG = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9_.-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\b")


OWN_REPO = "Charlesganu2004/Master-Repo-Use"


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
        for line in listing.read_text(encoding="utf-8").splitlines():
            slug = line.split("#", 1)[0].strip()
            if slug.count("/") == 1 and slug:
                names.add(slug)
    return names


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


def build() -> dict:
    source = json.loads(PRIVATE_STATE.read_text(encoding="utf-8"))
    policy = source.get("policy") or {}
    counts = source.get("counts") or {}
    return {
        "updated": source.get("updated"),
        "policy": {key: policy[key] for key in ALLOWED_POLICY if key in policy},
        "counts": {key: counts.get(key, 0) for key in ("HEALTHY", "STALE", "REVIEW", "REMOVE")},
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

    if PUBLIC_INDEX.exists():
        page = PUBLIC_INDEX.read_text(encoding="utf-8")
        if "data-private" in page:
            problems.append("public index.html still contains data-private markup")
        # The page links to its own repository on purpose; every other catalogued
        # repository is private catalog content and must not appear.
        for name in sorted(catalog - {OWN_REPO}):
            if name in page:
                problems.append(f"public index.html names a catalogued repository: {name}")
        for note in sorted(private_notes()):
            if note in page:
                problems.append(f"public index.html contains a private note: {note[:50]}...")

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
