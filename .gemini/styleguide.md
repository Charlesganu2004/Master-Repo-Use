# Review style guide — Master Repo Use

Gemini Code Assist: read this before reviewing. This repository is a **catalog and
instruction layer**, not an application. Reviews that treat it like a product codebase
generate false positives.

## What this repository is

- `repo-lists/*.txt` — curated URL catalogs. **No third-party code is vendored here.**
- `scripts/` — deterministic Python: lifecycle auditing, security scanning, site building.
- `docs/` — the instruction layer that Claude Code, Codex, Copilot and Gemini all read.
- `index.html` — a single-file command center that serves two audiences (private local
  clone vs. public GitHub Pages).

## Priorities, in order

1. **Privacy leaks.** The Pages artifact is public even though the repo is private.
   Anything that could move a repo slug, security note, or scanner finding from the
   private side into `_site/` is the highest-severity finding you can report. The
   contract lives in `scripts/build_public_site.py` and `tests/test_public_site_privacy.py`.
   Elements marked `data-private` are stripped at build time; removing that attribute
   from a private card is a leak, not a cleanup.
2. **Security-scanner correctness.** In `scripts/catalog_security.py`, a scanner that
   fails must classify as `SCANNER-ERROR`, never as "clean" and never as "malware
   found". Fail-closed. Flag any change that makes a scanner failure look like a pass.
3. **Secret redaction.** Gitleaks runs with `--redact`. Only rule, file and line may be
   reported. Flag anything that could write a raw credential into logs or an issue body.
4. **Owner-gate integrity.** `scripts/owner_approval.py` binds approval to a commit SHA.
   Flag any change that would let an approval survive a force-push or a new commit.
5. **Actions cost.** This is a private repo, so Actions minutes are metered. Flag new
   `schedule:` triggers, removed `concurrency`/`cancel-in-progress`, removed
   `timeout-minutes`, or matrix expansion. `tests/test_workflow_policy.py` locks the
   current policy.

## What NOT to comment on

- Adding or removing lines in `repo-lists/*.txt`. Those are curation decisions made by
  the owner and audited by Catalog Guardian. Do not review them for style or suggest
  alternative repositories.
- Long single-line HTML/CSS in `index.html`. It is deliberately dense to keep the
  single-file page small; it is not accidental minification.
- Markdown prose style, heading levels, or line length in `docs/`.
- Requests to add type annotations to short scripts, or to convert `unittest` to pytest.
- Suggestions to add a build system, bundler, or framework to `index.html`. Single-file
  and dependency-free is a requirement, not an oversight.

## Authority boundary

Gemini Code Assist has **no role in the approval gate**. Only Charles (`@Charlesganu2004`)
approves, using the exact phrases `APPROVE CATALOG MAINTENANCE` / `APPROVE AI MAINTENANCE` /
`APPROVE OWNER PR`. Never post those phrases, never suggest that a review constitutes
approval, and never recommend merging. Say what you found and stop.
