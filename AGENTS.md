# Master Repo Agent Contract

This private repository is the canonical catalog and instruction layer for `Charlesganu2004/Master-Repo-Use`.

## Default behavior

For every task in this repository:

1. Read this file first.
2. Run `python scripts/maintenance_request.py --auto` once near the start of a Master Repo session when shell access and authenticated `gh` are available. This check does **not** start maintenance work. It only creates a single `[AI Maintenance]` GitHub issue when a review is due and no open request already exists.
3. If a maintenance issue/request exists, summarize it to Charles but **do not perform maintenance changes until Charles explicitly says `APPROVE AI MAINTENANCE`**.
4. After that approval, the AI may review/update a branch and open a PR. It must never merge `main` without Charles's explicit approval.
5. Treat `docs/VETTING-REPORT.md`, `docs/REPO-HEALTH.md`, `docs/CATALOG-STATUS.md`, and `docs/SECURITY.md` as trust and safety gates.
6. Search `docs/REPO-CATALOG.md` and `repo-lists/` for the task-relevant lane before inventing a new dependency.
7. Load only the minimum relevant files, skills, MCP servers, libraries, or repos needed for the current task. Do not load the entire catalog into context.
8. Prefer already-vetted entries over adding duplicates.
9. For a third-party repo that is not already vetted, inspect it before recommending installation or execution.
10. Prefer integrations in this order when adapting a catalog entry to an AI client:
   - native MCP server;
   - native skill/plugin/instructions;
   - CLI or API wrapper;
   - direct library integration.
11. Never assume a repo listed in the catalog is automatically executable by GitHub Copilot, Claude, Codex, ChatGPT, or another client. Use the appropriate adapter/setup path.
12. Keep secrets out of committed files. Scope filesystem and MCP access to the minimum required directories and tools.
13. For financial/trading tooling, keep research and paper-trading defaults unless an explicit audited live-action workflow requires otherwise.

## No-background-cost maintenance policy

- Do **not** start scheduled GPT, Claude, Copilot, Codex, or other paid model calls.
- Do **not** create a recurring Actions schedule for catalog maintenance by default.
- The maintenance request cadence is **30 days, on next use**: when a supported local AI session is already running, `scripts/maintenance_request.py --auto` checks GitHub Issues. If the last request is at least 30 days old and none is open, it creates a new review issue and stops.
- Creating/checking the issue uses the GitHub CLI/API, not a background model call.
- If `gh` is unavailable, the script writes `docs/AI-MAINTENANCE-REQUEST.md` locally instead.
- The owner approval phrase is exactly: `APPROVE AI MAINTENANCE`.
- Maintenance work must be proposed through a branch/PR and remain subject to `@Charlesganu2004` review.

## Lifecycle policy

- 0–120 days since last push: healthy from a freshness perspective.
- 121–269 days: stale warning.
- 270–365 days: replacement or managed-adoption review.
- More than 365 days: remove from the active/runtime catalog unless an owner-approved stability/reference exception applies.
- Archived + recent activity: review the reason, releases, sunset notice, and successor; do not auto-delete from the archive flag alone.
- Static research/reference artifacts can receive explicit `reference` overrides when quietness is expected.
- Deleted/disabled repos or confirmed CRITICAL security findings are immediate removal candidates.

## Important entrypoints

- Catalog: `docs/REPO-CATALOG.md`
- Per-repo setup: `docs/REPO-INSTRUCTIONS.md`
- Combining tools: `docs/COMBINING-REPOS.md`
- Standalone usage: `docs/STANDALONE-USAGE.md`
- Security: `docs/SECURITY.md`
- Vetting: `docs/VETTING-REPORT.md`
- Live status: `docs/CATALOG-STATUS.md`
- Health: `docs/REPO-HEALTH.md`
- AI maintenance: `docs/AI-MAINTENANCE.md`
- Global client setup: `docs/GLOBAL-AI-SETUP.md`
- GitHub Copilot: `docs/COPILOT-SETUP.md`
- Optional token/work budget: `docs/TOKEN-BUDGET.md`
- Full curated list: `repo-lists/all-curated.txt`

## High-use cross-agent tools

- `getomnico/omni`
- `thedotmack/claude-mem`
- `headroomlabs-ai/headroom`
- `hoangsonww/Claude-Code-Agent-Monitor`
- `github/copilot-cli`
- `github/copilot-sdk`
- `github/awesome-copilot`
- `github/github-mcp-server`
- `openai/codex`
- `D-Ogi/WatermarkRemover-AI` — only for media the user owns or is authorized to modify.

## Context efficiency

Do not paste large catalog files into prompts by default. Search by lane/name first, retrieve only the relevant entries, and use Headroom/LLMLingua or another vetted compression path when large tool output must be passed to a model.
