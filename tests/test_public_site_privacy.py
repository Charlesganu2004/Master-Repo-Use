#!/usr/bin/env python3
"""The public Pages artifact must never carry private catalog content.

GitHub Pages on a personal Pro plan is PUBLIC even when the source repository is
private, so everything the deploy publishes is world-readable. These tests assert
both halves of the contract:

  * the builder strips what it should (data-private markup, per-repo rows)
  * the verifier actually fails when something private slips through

Run: python tests/test_public_site_privacy.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_public_site as builder  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (f"  -> {detail}" if not ok else ""))
    if not ok:
        FAILURES.append(name)


def stage() -> None:
    """Reproduce the workflow's staging step."""
    shutil.rmtree(builder.SITE, ignore_errors=True)
    (builder.SITE / "docs").mkdir(parents=True)
    (builder.SITE / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy(ROOT / "docs" / "catalog-status.svg", builder.PUBLIC_SVG)
    payload = builder.build()
    builder.PUBLIC_STATE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    builder.build_index()


def test_clean_build_passes() -> None:
    stage()
    payload = json.loads(builder.PUBLIC_STATE.read_text(encoding="utf-8"))
    problems = builder.verify(payload)
    check("clean build passes verification", not problems, "; ".join(problems))
    check("public payload has no per-repo rows", payload["repos"] == [])
    check("public payload is flagged public", payload["public"] is True)


def test_index_is_stripped() -> None:
    private = (ROOT / "index.html").read_text(encoding="utf-8")
    public = builder.PUBLIC_INDEX.read_text(encoding="utf-8")

    check("private source marks content private", "data-private" in private)
    check("public build removed all data-private markup", "data-private" not in public)
    check("public build is smaller than private source", len(public) < len(private))

    catalog = builder.private_repo_names() - {builder.OWN_REPO}
    leaked = sorted(n for n in catalog if n in public)
    check("public index names no catalogued repository", not leaked, str(leaked[:5]))

    # The parts that must survive stripping.
    for keep in ("Health/Security", "Access/Deploy", "healthRows", "loadHealth"):
        check(f"public index keeps {keep!r}", keep in public)


def test_verifier_catches_injected_leaks() -> None:
    cases = {
        "per-repo row": lambda p: p.update(repos=[{"repo": "FlowiseAI/Flowise", "note": "x"}]),
        "extra key": lambda p: p.update(note="clamav HIGH"),
        "slug in a value": lambda p: p.update(updated="see thedotmack/claude-mem"),
    }
    for name, mutate in cases.items():
        stage()
        payload = json.loads(builder.PUBLIC_STATE.read_text(encoding="utf-8"))
        mutate(payload)
        problems = builder.verify(payload)
        check(f"verifier rejects {name}", bool(problems), "verifier stayed silent")

    # And an un-stripped index must be rejected too.
    stage()
    shutil.copy(ROOT / "index.html", builder.PUBLIC_INDEX)
    payload = json.loads(builder.PUBLIC_STATE.read_text(encoding="utf-8"))
    problems = builder.verify(payload)
    check("verifier rejects an unstripped index.html", bool(problems), "verifier stayed silent")
    check(
        "rejection names the data-private cause",
        any("data-private" in p for p in problems),
        str(problems[:3]),
    )


if __name__ == "__main__":
    try:
        test_clean_build_passes()
        test_index_is_stripped()
        test_verifier_catches_injected_leaks()
    finally:
        shutil.rmtree(builder.SITE, ignore_errors=True)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} check(s) failed: {', '.join(FAILURES)}")
        raise SystemExit(1)
    print("all public-site privacy checks passed")
