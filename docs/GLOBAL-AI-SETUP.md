# Global AI Setup

This guide makes the Master Repo the shared instruction/catalog source for supported AI coding clients while keeping the catalog itself private and loading tools on demand.

## Design

The global setup does **not** install every repository in `repo-lists/all-curated.txt`. Instead it installs a tiny persistent pointer/instruction layer that tells each client where the Master Repo lives and how to discover the correct lane for a task.

Default flow:

```text
prompt
  -> read client/global Master Repo instructions
  -> identify task lane
  -> search Master Repo catalog
  -> load only relevant files/repos/skills/MCP servers
  -> execute with that client's supported integration
```

## One-command setup

### Windows / PowerShell

```powershell
$p="$HOME\Master-Repo-Use"; if (Test-Path "$p\.git") { git -C $p pull } else { gh repo clone Charlesganu2004/Master-Repo-Use $p }; & "$p\scripts\setup-global-ai.ps1" -RepoPath $p
```

### Bash / WSL / macOS / Linux

```bash
p="$HOME/Master-Repo-Use"; if [ -d "$p/.git" ]; then git -C "$p" pull; else gh repo clone Charlesganu2004/Master-Repo-Use "$p"; fi; bash "$p/scripts/setup-global-ai.sh" "$p"
```

## Claude Code

The repository contains `CLAUDE.md`. The global scripts also create/update a marked Master Repo block in:

```text
~/.claude/CLAUDE.md
```

That block tells Claude Code to use this private repo as the canonical catalog when a task would benefit from one of its tools.

Optional additions:

```bash
npx claude-mem install
uv tool install --python 3.13 "headroom-ai[all]"
headroom doctor
```

Claude-Mem and Headroom remain optional and are not silently installed by the bootstrap.

## Codex

The repository contains `AGENTS.md`. The global scripts create/update a marked Master Repo block in:

```text
~/.codex/AGENTS.md
```

The block tells Codex to discover relevant tools from the Master Repo rather than loading the entire catalog.

For repo-local work, the root `AGENTS.md` remains the source of truth.

## GitHub Copilot

Repository-local instructions:

```text
.github/copilot-instructions.md
```

Copilot CLI global discovery is configured by the scripts using `COPILOT_CUSTOM_INSTRUCTIONS_DIRS`, pointing at the Master Repo. This lets Copilot CLI discover the repo's instruction files from other working directories.

Verify with:

```text
/instructions
```

See `docs/COPILOT-SETUP.md`.

## ChatGPT / GPT online

A private GitHub repository cannot force itself into every unrelated ChatGPT conversation from a committed file alone. To use the Master Repo online:

1. Connect GitHub in ChatGPT with access to this private repository.
2. Select/reference `Charlesganu2004/Master-Repo-Use` for coding or repository tasks.
3. Keep `AGENTS.md` as the portable repo contract for Codex-backed coding workflows.
4. Use ChatGPT account/project instructions for truly account-wide preferences; do not put secrets in them.

The repo can provide the source instructions and portable skills, but the online product controls which connected tools and instructions are available in a given conversation.

## Claude.ai / Claude online

A private GitHub repository likewise cannot silently modify all Claude.ai conversations from a commit. Use one of the supported connected/project paths:

1. Connect/add the private GitHub repo to the relevant Claude project/workspace, or use Claude Code on the web with this repo.
2. Keep `CLAUDE.md` committed so repo-aware Claude Code sessions use the same rules.
3. Use Claude profile/project preferences for account/project-wide behavioral preferences.

## GitHub.com / Copilot online

Keep `.github/copilot-instructions.md` and `AGENTS.md` committed. Repository-aware GitHub Copilot workflows can consume those files when they operate on this repository. Access to the private catalog from other repositories depends on the permissions and environment of that Copilot session.

## Google Antigravity

Antigravity reads its **global rules from `~/.gemini/GEMINI.md`**, the same file the Gemini CLI
uses. There is no `~/.antigravity/` tree, and a script that writes one produces a file nothing
loads. Verified against `antigravity.google/docs/rules-workflows/` on 2026-09-04.

Where it differs from Gemini is everything else, all of it under `~/.gemini/config/`:

| What | Path |
|---|---|
| Global rules | `~/.gemini/GEMINI.md` (shared with the Gemini CLI) |
| Skills | `~/.gemini/config/skills/<folder>/SKILL.md` |
| Plugins | `~/.gemini/config/plugins/<name>/plugin.json` |
| MCP servers | `~/.gemini/config/mcp_config.json` |
| Workspace rules | `.agents/rules/` in the repository |

So `--client gemini` gives Antigravity its rules, and `--client antigravity` gives it the rules
**plus** every skill in this repository copied into the path the Gemini CLI does not read:

```bash
bash "$HOME/Master-Repo-Use/scripts/setup-global-ai.sh" "$HOME/Master-Repo-Use" --client antigravity --auto-skills
```

Its hosted models are reference entries in the atlas rather than setup recipes, because a hosted
model is signed into rather than installed. The three non-Google ones, Claude Sonnet 4.6 (thinking),
Claude Opus 4.6 (thinking) and GPT-OSS-120b, are the ones a plan change takes away.

The CLI has a vendor-published installer, which is unusual enough to be worth stating plainly: both
`antigravity.google/cli/install.ps1` and `.../install.sh` return 200 from Google Frontend and the
shell script was read before this was written. It installs to `$HOME/.local/bin`. It covers **the
CLI only**; the desktop client, the IDE and the SDK are separate downloads, OS package repositories
and PyPI respectively. On PyPI the SDK is `google-antigravity`; plain `antigravity` is an unrelated
joke package.

## Adopting a catalogued skill pack

A catalog entry is a reference, not an install: the repository deliberately gives no way to run one,
because a URL is not a vetting. `scripts/install_catalog_skill.py` is the reviewed middle step.

```bash
python "$HOME/Master-Repo-Use/scripts/install_catalog_skill.py" --list
python "$HOME/Master-Repo-Use/scripts/install_catalog_skill.py" mattpocock/skills --dry-run
python "$HOME/Master-Repo-Use/scripts/install_catalog_skill.py" mattpocock/skills
```

It installs into Claude Code and Antigravity together, and four things it refuses to do are the
reason it is safe to run:

- **A slug that is not in `repo-lists/` is refused**, before anything is fetched. A skills
  marketplace is exactly where a near-name repository gets installed by mistake, and the catalog
  already knows which one was vetted.
- **Nothing from the repository is executed.** No `npm install`, no postinstall, no build. Hooks are
  disabled for the clone, submodules are not fetched, and only directories containing a `SKILL.md`
  are copied.
- **A skill folder it did not install is never overwritten.** Installs are namespaced by owner and
  carry a `.installed-from` marker, so two packs shipping a `review` skill cannot silently replace
  each other, and nothing removes a capability somebody else put there.
- **Scanner findings block the install** until you have read them and passed `--accept-findings`.

Expect false positives and read them rather than forcing past them. `mattpocock/skills` trips the
prompt-injection heuristic on one line of a setup wizard that tells a human to click "Reveal test
key" in a Stripe dashboard. That is documentation of a manual step, not an attack, which is exactly
why the script refuses rather than deletes.

## Making catalog repos work across clients

Use this compatibility order:

1. **MCP:** best when the upstream repo exposes a server and the client supports MCP.
2. **Skill/plugin/instructions:** best for reusable prompt/workflow behavior.
3. **CLI/API wrapper:** best for tools that expose commands or HTTP APIs.
4. **Direct library:** use from the project code when no agent-native adapter exists.

Do not duplicate every upstream repository into client-specific folders. Maintain one catalog entry and document its adapters.

## Refresh

```bash
git -C "$HOME/Master-Repo-Use" pull
```

Then rerun the platform bootstrap if the global pointer text changed.

## Remove the global pointers

The setup scripts use clearly marked blocks:

```text
<!-- MASTER-REPO-USE:BEGIN -->
...
<!-- MASTER-REPO-USE:END -->
```

Remove only that block from the relevant user instruction file to stop the global behavior. For Copilot CLI, also remove `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` if you no longer want global discovery.

## Optional token/work budget

Budget enforcement and paid-to-free/local fallback are intentionally separate from this setup. See `docs/TOKEN-BUDGET.md`.
