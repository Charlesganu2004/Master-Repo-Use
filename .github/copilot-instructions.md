# GitHub Copilot Instructions — Master Repo

This repository is the canonical private catalog and shared instruction layer for `Charlesganu2004/Master-Repo-Use`.

For every Copilot task in this repository:

- Read and follow `AGENTS.md` as the canonical cross-client contract.
- When Copilot has local shell access and authenticated `gh`, run `python scripts/maintenance_request.py --auto` once near the start of a Master Repo session. This only creates/checks the no-background-cost maintenance request.
- If an `[AI Maintenance]` issue/request exists, summarize it but do not perform maintenance until Charles explicitly states `APPROVE AI MAINTENANCE`.
- After approval, make maintenance changes on a branch and open a pull request. Never merge `main` without Charles's explicit approval.
- Do not schedule recurring Copilot/model calls for maintenance. The request is generated only when Copilot is already being used.
- Search `docs/REPO-CATALOG.md` and `repo-lists/` before proposing new third-party dependencies.
- Prefer vetted, healthy repos already in this catalog.
- Load only the task-relevant lane; never inject the full catalog into every prompt.
- Use integrations in this order when possible: native MCP → skill/plugin/instructions → CLI/API wrapper → direct library.
- Do not claim every listed repo is a native Copilot extension. Adapt it through the supported interface documented by the repo.
- Use `docs/COPILOT-SETUP.md` for Copilot CLI/global setup.
- Use `docs/GLOBAL-AI-SETUP.md` for cross-client setup.
- Use `docs/AI-MAINTENANCE.md` for the approval-driven maintenance flow.
- Use `docs/TOKEN-BUDGET.md` only when the user has opted into budget/routing controls.
- Follow `docs/SECURITY.md`, `docs/VETTING-REPORT.md`, and `docs/REPO-HEALTH.md` before enabling a third-party tool.
- Keep secrets and machine-specific credentials out of committed files.
- For financial/trading tools, default to research/paper modes and retain explicit human approval gates for live actions.
- `D-Ogi/WatermarkRemover-AI` may be used only for media the user owns or is authorized to modify.

High-use cross-agent entries include:
`getomnico/omni`, `thedotmack/claude-mem`, `headroomlabs-ai/headroom`, `hoangsonww/Claude-Code-Agent-Monitor`, `github/copilot-cli`, `github/copilot-sdk`, `github/awesome-copilot`, `github/github-mcp-server`, and `openai/codex`.
