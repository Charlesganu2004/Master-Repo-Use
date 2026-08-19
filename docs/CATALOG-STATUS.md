# Catalog Status

![Catalog health](catalog-status.svg)

The Master Repo no longer runs Catalog Guardian every six hours. That recurring schedule was removed to avoid unnecessary private-repository Actions usage and any temptation to attach recurring paid AI/model work to maintenance.

## Current refresh model

- `scripts/maintenance_request.py --auto` is checked by supported AI clients **when you are already using them**.
- Every 30 days on next use, it can create one `[AI Maintenance]` GitHub issue if none is already open.
- AI maintenance work waits for the exact owner approval phrase: `APPROVE AI MAINTENANCE`.
- `.github/workflows/catalog-guardian.yml` is manual-only.
- For zero GitHub-hosted Actions usage, run Guardian locally.
- Guardian changes/removals should go through an owner-reviewed branch/PR; they must not silently merge to `main`.

The current `catalog-status.json` is a seeded lifecycle snapshot so the interactive page has working health data immediately. A full local/manual Guardian run will replace it with a full catalog snapshot.

## Lifecycle meanings

- 🟢 **HEALTHY** — source activity is within 120 days and no stronger lifecycle/security signal exists.
- 🟡 **STALE** — 121–269 days since last source push.
- 🟠 **REVIEW** — 270–365 days since push, archived transition/reference state, owner lifecycle exception, or HIGH security finding requiring review.
- 🔴 **REMOVE** — >365 days for an active/runtime dependency without an approved exception, deleted/disabled upstream, explicit unsupported replacement case, or confirmed CRITICAL security finding.

Archive status alone is not enough to delete a repo. The review must check recent releases, sunset/EOL notices, successors, whether the repo is a runtime dependency or static research/reference artifact, licensing, and security posture.

See:

- `docs/LIFECYCLE-REVIEW-2026-08-19.md`
- `docs/AI-MAINTENANCE.md`
- `docs/SECURITY-SCANNING.md`
- `repo-lists/lifecycle-overrides.json`
- `managed-repos/README.md`
