# Claude Code — Master Repo

Use `AGENTS.md` as the canonical portable contract for this repository and follow it for every Claude Code task here.

## Claude-specific defaults

- Read `AGENTS.md` before making repo changes.
- Routine catalog health/security maintenance is GitHub-first. Treat `.github/workflows/catalog-guardian.yml` and `[Catalog Audit]` issues as the default audit/approval path; do not replace them with recurring Claude calls.
- If a `[Catalog Audit]` issue is open, summarize it when relevant. Do not try to impersonate the owner approval comment; only Charles may approve the deterministic workflow with `APPROVE CATALOG MAINTENANCE`.
- Use `python scripts/maintenance_request.py --auto` only when deterministic checks leave a task that genuinely needs model judgment, such as managed adoption, modernization, successor analysis, or architecture work.
- If an `[AI Maintenance]` request is open, summarize it and do not perform that AI-assisted maintenance until Charles states the exact phrase `APPROVE AI MAINTENANCE`.
- After AI-maintenance approval, work on a branch and open a PR; do not merge `main` yourself.
- Use `docs/GLOBAL-AI-SETUP.md` for global Claude Code installation and refresh instructions.
- Claude-Mem is optional. When persistent observation/search memory is wanted, use `thedotmack/claude-mem` and its supported installer rather than hand-editing its hooks.
- Headroom is optional. Use it when context compression or cross-agent memory is useful; do not make it a mandatory dependency.
- Prefer MCP/skills/hooks that are already listed and vetted in this repo.
- Keep user-level secrets and machine-specific config outside the repository.
- Do not load the entire catalog into context. Find the task-relevant lane, then read only what is needed.
- Do not create scheduled Claude/model maintenance calls. GitHub Actions performs the non-AI audit; Claude is used only when Charles is already using it and judgment is needed.

Canonical files:
- `AGENTS.md`
- `docs/LOCAL-MODEL-HARDWARE.md`
- `docs/ADK-GUIDE.md`
- `docs/CATALOG-TRIAGE-2026-08-25.md`
- `docs/AI-MAINTENANCE.md`
- `docs/CATALOG-STATUS.md`
- `docs/REPO-CATALOG.md`
- `docs/VETTING-REPORT.md`
- `docs/SECURITY.md`
- `docs/TOKEN-BUDGET.md`
