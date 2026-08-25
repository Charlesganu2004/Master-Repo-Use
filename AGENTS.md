# Master Repo Agent Contract

This private repository is the canonical catalog and instruction layer for `Charlesganu2004/Master-Repo-Use`.

## Default behavior

For every task in this repository:

1. Read this file first.
2. Treat `docs/VETTING-REPORT.md`, `docs/REPO-HEALTH.md`, `docs/CATALOG-STATUS.md`, and `docs/SECURITY.md` as trust and safety gates.
3. Search `docs/REPO-CATALOG.md` and `repo-lists/` for the task-relevant lane before inventing a new dependency.
4. Load only the minimum relevant files, skills, MCP servers, libraries, or repos needed for the current task. Do not load the entire catalog into context.
5. Prefer already-vetted entries over adding duplicates.
6. For a third-party repo that is not already vetted, inspect it before recommending installation or execution.
7. Prefer integrations in this order when adapting a catalog entry to an AI client:
   - native MCP server;
   - native skill/plugin/instructions;
   - CLI or API wrapper;
   - direct library integration.
8. Never assume a repo listed in the catalog is automatically executable by GitHub Copilot, Claude, Codex, ChatGPT, or another client. Use the appropriate adapter/setup path.
9. Keep secrets out of committed files. Scope filesystem and MCP access to the minimum required directories and tools.
10. For financial/trading tooling, keep research and paper-trading defaults unless an explicit audited live-action workflow requires otherwise.

## Maintenance and approval behavior

Routine maintenance is **GitHub-first and deterministic**, not an automatic paid-model loop.

- `.github/workflows/catalog-guardian.yml` performs weekly/on-change metadata audits without calling GPT, Claude, Copilot, or Codex.
- New catalog repos receive immediate source scanning through Guardian.
- When the audit finds attention items, it creates/refreshes a `[Catalog Audit]` issue and stops.
- Do not execute the deeper catalog-maintenance workflow unless Charles has commented the exact phrase `APPROVE CATALOG MAINTENANCE` on that audit issue.
- The approved GitHub workflow may create/update `automation/catalog-guardian` and open a PR, but it must never merge `main` automatically.
- Use `scripts/maintenance_request.py --auto` only when deterministic checks leave a task that genuinely needs model judgment, such as managed adoption, modernization, successor research, or architectural review.
- Do not perform that optional AI work until Charles has explicitly approved `APPROVE AI MAINTENANCE`.
- AI-assisted maintenance must also end in a branch/PR and must not merge `main` without Charles's approval.

## Lifecycle policy

- 0–120 days since last push: active/healthy from a freshness perspective.
- 121–269 days: stale warning.
- 270–365 days: replacement or managed-adoption review.
- More than 365 days: active/runtime removal threshold unless an owner-approved exception applies.
- Archived repositories must be checked for recent releases, archive reason, sunset/EOL, successor projects, security, licensing, and reference value before removal.
- Research/reference artifacts may receive an explicit lifecycle override when inactivity is expected.

## Important entrypoints

- Catalog: `docs/REPO-CATALOG.md`
- Per-repo setup: `docs/REPO-INSTRUCTIONS.md`
- Combining tools: `docs/COMBINING-REPOS.md`
- Standalone usage: `docs/STANDALONE-USAGE.md`
- Security: `docs/SECURITY.md`
- Security scanning: `docs/SECURITY-SCANNING.md`
- Vetting: `docs/VETTING-REPORT.md`
- Health: `docs/REPO-HEALTH.md`
- Live/private status: `docs/CATALOG-STATUS.md`
- Global client setup: `docs/GLOBAL-AI-SETUP.md`
- GitHub Copilot: `docs/COPILOT-SETUP.md`
- Optional token/work budget: `docs/TOKEN-BUDGET.md`
- Optional AI maintenance: `docs/AI-MAINTENANCE.md`
- Full curated list: `repo-lists/all-curated.txt`
- Local model sizing: `docs/LOCAL-MODEL-HARDWARE.md` + `docs/hardware-profiles.json`
- Agent development kits: `docs/ADK-GUIDE.md`
- Current lifecycle triage: `docs/CATALOG-TRIAGE-2026-08-25.md`

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

## Local-first model selection

Before spending hosted tokens on a task a small local model can do, check what the machine can
host: `docs/hardware-profiles.json` carries the sizing formula, tiers and per-model minimums, and
`docs/LOCAL-MODEL-HARDWARE.md` explains them. Vendors in that lane are limited to Microsoft,
Google/Gemini and Ollama. Below roughly 8 GB of RAM on Windows, local inference is not a real
option and a hosted API is the correct answer — say so rather than recommending something
that will swap.

## Public vs private surface

`repo-lists/public-allowlist.txt` is the only sanctioned way a catalog slug reaches the public
Pages site. Do not add a slug there to make a build pass; a build failure means the artifact was
about to publish private catalog composition. Elements flagged private in `index.html` are
stripped at build time.

## Context efficiency

Do not paste large catalog files into prompts by default. Search by lane/name first, retrieve only the relevant entries, and use Headroom/LLMLingua or another vetted compression path when large tool output must be passed to a model.
