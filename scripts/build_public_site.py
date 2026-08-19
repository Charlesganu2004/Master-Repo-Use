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
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIVATE_STATE = ROOT / "docs" / "catalog-status.json"
SITE = ROOT / "_site"
PUBLIC_STATE = SITE / "docs" / "catalog-status.json"
PUBLIC_SVG = SITE / "docs" / "catalog-status.svg"

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
