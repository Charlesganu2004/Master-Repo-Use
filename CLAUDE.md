# Claude Code — Master Repo

Use `AGENTS.md` as the canonical portable contract for this repository and follow it for every Claude Code task here.

## Claude-specific defaults

- Read `AGENTS.md` before making repo changes.
- When shell access and authenticated `gh` are available, run `python scripts/maintenance_request.py --auto` once near the start of a Master Repo session. This may create a monthly-on-next-use maintenance issue, but it must **not** start maintenance work.
- If an `[AI Maintenance]` request is open, summarize the request and wait for Charles to state the exact approval phrase `APPROVE AI MAINTENANCE` before performing catalog maintenance.
- After approval, work on a branch and open a PR; do not merge `main` yourself.
- Use `docs/GLOBAL-AI-SETUP.md` for global Claude Code installation and refresh instructions.
- Claude-Mem is optional. When persistent observation/search memory is wanted, use `thedotmack/claude-mem` and its supported installer rather than hand-editing its hooks.
- Headroom is optional. Use it when context compression or cross-agent memory is useful; do not make it a mandatory dependency.
- Prefer MCP/skills/hooks that are already listed and vetted in this repo.
- Keep user-level secrets and machine-specific config outside the repository.
- Do not load the entire catalog into context. Find the task-relevant lane, then read only what is needed.
- Do not create scheduled Claude/model maintenance calls. The maintenance request is intentionally generated only when Claude is already in use, so there is no background model spend.

Canonical files:
- `AGENTS.md`
- `docs/AI-MAINTENANCE.md`
- `docs/REPO-CATALOG.md`
- `docs/VETTING-REPORT.md`
- `docs/SECURITY.md`
- `docs/TOKEN-BUDGET.md`
