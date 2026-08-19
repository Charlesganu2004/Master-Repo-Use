# Claude Code — Master Repo

Use `AGENTS.md` as the canonical portable contract for this repository and follow it for every Claude Code task here.

## Claude-specific defaults

- Read `AGENTS.md` before making repo changes.
- Use `docs/GLOBAL-AI-SETUP.md` for global Claude Code installation and refresh instructions.
- Claude-Mem is optional. When persistent observation/search memory is wanted, use `thedotmack/claude-mem` and its supported installer rather than hand-editing its hooks.
- Headroom is optional. Use it when context compression or cross-agent memory is useful; do not make it a mandatory dependency.
- Prefer MCP/skills/hooks that are already listed and vetted in this repo.
- Keep user-level secrets and machine-specific config outside the repository.
- Do not load the entire catalog into context. Find the task-relevant lane, then read only what is needed.

Canonical files:
- `AGENTS.md`
- `docs/REPO-CATALOG.md`
- `docs/VETTING-REPORT.md`
- `docs/SECURITY.md`
- `docs/TOKEN-BUDGET.md`
