# Master Repo Agent Contract

This private repository is the canonical catalog and instruction layer for `Charlesganu2004/Master-Repo-Use`.

## Default behavior

For every task in this repository:

1. Read this file first.
2. Treat `docs/VETTING-REPORT.md`, `docs/REPO-HEALTH.md`, and `docs/SECURITY.md` as trust and safety gates.
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

## Important entrypoints

- Catalog: `docs/REPO-CATALOG.md`
- Per-repo setup: `docs/REPO-INSTRUCTIONS.md`
- Combining tools: `docs/COMBINING-REPOS.md`
- Standalone usage: `docs/STANDALONE-USAGE.md`
- Security: `docs/SECURITY.md`
- Vetting: `docs/VETTING-REPORT.md`
- Health: `docs/REPO-HEALTH.md`
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
