# GitHub Copilot Instructions — Master Repo

This repository is the canonical private catalog and shared instruction layer for `Charlesganu2004/Master-Repo-Use`.

For every Copilot task in this repository:

- Read and follow `AGENTS.md` as the canonical cross-client contract.
- Routine catalog health/security maintenance is GitHub-first. Treat `.github/workflows/catalog-guardian.yml` and `[Catalog Audit]` issues as the default audit/approval path; do not create recurring Copilot/model maintenance calls.
- If a `[Catalog Audit]` issue is open, summarize it when relevant. Only Charles may approve the deterministic workflow by commenting `APPROVE CATALOG MAINTENANCE`.
- Use `python scripts/maintenance_request.py --auto` only when deterministic checks leave a task that genuinely needs model judgment, such as managed adoption, modernization, successor analysis, or architecture work.
- If an `[AI Maintenance]` issue exists, summarize it but do not perform AI-assisted maintenance until Charles explicitly states `APPROVE AI MAINTENANCE`.
- After AI-maintenance approval, make changes on a branch and open a pull request. Never merge `main` without Charles's explicit approval.
- Search `docs/REPO-CATALOG.md` and `repo-lists/` before proposing new third-party dependencies.
- Prefer vetted, healthy repos already in this catalog.
- Load only the task-relevant lane; never inject the full catalog into every prompt.
- Use integrations in this order when possible: native MCP → skill/plugin/instructions → CLI/API wrapper → direct library.
- Do not claim every listed repo is a native Copilot extension. Adapt it through the supported interface documented by the repo.
- Use `docs/COPILOT-SETUP.md` for Copilot CLI/global setup.
- Use `docs/GLOBAL-AI-SETUP.md` for cross-client setup.
- Use `docs/AI-MAINTENANCE.md` for optional model-assisted maintenance only.
- Use `docs/TOKEN-BUDGET.md` only when the user has opted into budget/routing controls.
- Follow `docs/SECURITY.md`, `docs/VETTING-REPORT.md`, `docs/CATALOG-STATUS.md`, and `docs/REPO-HEALTH.md` before enabling a third-party tool.
- Keep secrets and machine-specific credentials out of committed files.
- For financial/trading tools, default to research/paper modes and retain explicit human approval gates for live actions.
- `D-Ogi/WatermarkRemover-AI` may be used only for media the user owns or is authorized to modify.

High-use cross-agent entries include:
`getomnico/omni`, `thedotmack/claude-mem`, `headroomlabs-ai/headroom`, `hoangsonww/Claude-Code-Agent-Monitor`, `github/copilot-cli`, `github/copilot-sdk`, `github/awesome-copilot`, `github/github-mcp-server`, and `openai/codex`.
