# Gemini — Master Repo

Use `AGENTS.md` as the canonical portable contract for this repository and follow it for every
Gemini CLI / Gemini Code Assist task here.

## Gemini-specific defaults

- Read `AGENTS.md` before making repo changes.
- Two Gemini surfaces touch this repo and they have different jobs:
  - **Gemini CLI** (`google-gemini/gemini-cli`) — interactive local work. Reads this file.
  - **Gemini Code Assist for GitHub** — automated PR review. Reads `.gemini/config.yaml`
    and `.gemini/styleguide.md`. Read the styleguide before reviewing; it lists what is
    deliberately out of scope.
- Routine catalog health/security maintenance is GitHub-first. Treat
  `.github/workflows/catalog-guardian.yml` and `[Catalog Audit]` issues as the default
  audit path; do not replace them with recurring Gemini calls.
- **You have no authority in the approval gate.** Only Charles approves, with the exact
  phrases `APPROVE CATALOG MAINTENANCE` / `APPROVE AI MAINTENANCE` / `APPROVE OWNER PR`.
  Never post those phrases and never state that a review constitutes approval.
- Do not load the entire catalog into context. Find the task-relevant lane in
  `repo-lists/`, then read only what is needed.
- Do not create scheduled Gemini maintenance calls. GitHub Actions performs the non-AI
  audit; Gemini is used only when Charles is already working and judgment is needed.
- Keep user-level secrets and machine-specific config outside the repository.

## Local-first preference

When a task can be done by a local model, prefer it over a hosted Gemini call. Check
`docs/LOCAL-MODEL-HARDWARE.md` for what the current machine can host, and
`repo-lists/local-models.txt` for the runtimes. Hosted Gemini is the correct fallback when
RAM is the binding constraint — notably at 4 GB, where no local chat model fits.

Canonical files:
- `AGENTS.md`
- `.gemini/styleguide.md`
- `docs/ADK-GUIDE.md`
- `docs/LOCAL-MODEL-HARDWARE.md`
- `docs/TOKEN-BUDGET.md`
- `docs/SECURITY.md`
