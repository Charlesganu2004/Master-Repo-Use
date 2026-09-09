# Auto mode

Auto mode removes the need to type a slash command for the standing workflow.
It also tells each supported client to discover and apply the skills, tools,
plugins, MCP servers and agents that fit the task. Enforcement strength depends
on whether the client exposes a native event before each user turn enters the
agent loop.

## The automatic three-layer pipeline

`scripts/hooks/skill_pipeline.py` supplies the same core pipeline through the
strongest context event each client exposes:

1. **Layer 1, before reading the request:** apply Caveman token discipline, full
   output enforcement and anti-slop rules.
2. **Layer 2, before producing anything:** plan the work, then apply design taste
   to anything a person will see.
3. **Layer 3, while acting and again before answering:** choose and name the
   relevant skills, tools, plugins and MCP servers; fan independent work out to
   agents; verify adversarially; then reapply Layer 1 to the result.

The core is unconditional. The hook may add at most one task-specific lane for
security, UI, dependency intake or time-sensitive research. A large multi-part
prompt also receives an orchestration reminder. Slash commands pass through the
same pipeline.

Claude Code, Codex, Gemini CLI and Antigravity expose events that can inject
context as each user turn enters the agent loop. GitHub Copilot CLI and coding
agent use `userPromptTransformed` to rewrite the model-facing prompt on each
turn.
Copilot's `userPromptSubmitted` configuration hook does not provide that same
rewrite. Cursor does not expose a prompt-rewrite output, so its always-applied
global or project rule carries the per-prompt foundation and `sessionStart`
reinforces local sessions. Cursor's `beforeSubmitPrompt` can observe or gate a
prompt, but it is not used here as a context-injection event.

The distinction is important. Native context injection guarantees that the
pipeline text arrives at the documented event. The model still executes those
instructions, so this is deterministic delivery rather than mathematical proof
of model compliance. The pre-tool guards below are external enforcement and can
block a matching command before it runs.

## Runtime pieces and token cost

| Piece | Event or location | What it does | Model-context cost |
|---|---|---|---|
| Standing context injector | `scripts/hooks/skill_pipeline.py` | Injects all three layers per prompt where supported, or at session start where that is the strongest supported context event | Roughly 400 to 500 tokens when injected, plus a small conditional lane when matched |
| No-prune guard | `scripts/hooks/no_prune_guard.py` | Blocks matching destructive Bash commands against protected capability paths | 0 tokens |
| No-compress guard | `scripts/hooks/no_compress_guard.py` | Blocks matching compression or truncation commands against protected rules and capability definitions | 0 tokens |
| Global instruction block | `docs/auto-mode-block.txt` | Carries the portable contract into each supported client's global instruction file | Loaded according to that client's instruction behavior; the installer reports the current byte estimate |
| Installed skills | canonical `skills/*/SKILL.md`, generated project mirror `.agents/skills/`, and client user paths | Makes repository skills discoverable to Claude Code, Codex, Cursor, Copilot CLI, Gemini CLI and Antigravity locally and in repository-aware cloud agents | Client-specific skill listing cost; a full skill body loads only when used. Codex uses `~/.agents/skills/` as its current shared user path and keeps `~/.codex/skills/` for compatibility |

The protected `NO-COMPRESS` content remains canonical in
`docs/auto-mode-block.txt`. Do not duplicate, summarize or hand-edit that block
in this guide.

### Canonical skills and the project mirror

`skills/` is the only canonical source. `scripts/sync_project_skills.py` merges
every immediate skill directory containing `SKILL.md` into `.agents/skills/`.
The mirror is tracked because Codex, Copilot coding agent and Cursor can
discover that project path in local or cloud repository sessions, while the
canonical `skills/` path by itself is not a shared client discovery path.

The sync is non-destructive. It refreshes source-owned files but never deletes a
destination-only file or directory. Run it after adding or updating a canonical
skill:

```bash
python scripts/sync_project_skills.py
```

Use `--dry-run` to list the destinations without writing them.

## Why slash commands were previously needed

A slash command is an explicit invocation. The user names a capability, so the
client does not have to decide whether that one should run. Normal skills can
also be model-invocable: the client exposes their names and descriptions, and
the model chooses one when it matches the request. That is automatic, but it is
still a model judgment.

Model judgment is appropriate for conditional capabilities such as using a PDF
skill for a PDF. It is not strong enough for a rule that must arrive on every
prompt, because the missed invocation is the exact failure the rule is meant to
prevent. Global instructions and the registered hooks remove the slash
requirement for the standing workflow. A slash remains available when a user
wants to invoke one conditional skill explicitly.

## Native hooks, global instructions and hosted web

| Surface and mode | Setup used by this repository | Enforcement level |
|---|---|---|
| Claude Code | `UserPromptSubmit` runs the standing pipeline; `PreToolUse` runs both Bash guards; `~/.claude/CLAUDE.md` carries the global block | Native per-prompt delivery plus external Bash guards while those hooks are enabled |
| Google Antigravity | `PreInvocation` in `~/.gemini/config/hooks.json` runs the standing pipeline; `~/.gemini/GEMINI.md` carries the global block | Native per-invocation delivery for the prompt pipeline |
| Codex chat and code | `~/.codex/AGENTS.md` carries the global block; `~/.codex/hooks.json` registers `UserPromptSubmit` with `additionalContextLimit: 0` and both `PreToolUse` Bash guards; skills are installed to `~/.agents/skills/` and the compatible `~/.codex/skills/` path | Every-prompt hook, trust required. Codex skips a new or changed unmanaged hook until the user reviews and trusts its exact definition in the Hooks UI |
| Codex cloud repository task | Root `AGENTS.md` and the tracked `.agents/skills/` mirror travel with the repository | Repository instructions and project skills; the local user hook at `~/.codex/hooks.json` does not travel to the cloud task |
| Gemini CLI chat and code | `~/.gemini/GEMINI.md` carries the global block; `BeforeAgent` in `~/.gemini/settings.json` injects the pipeline on each turn; `BeforeTool` with matcher `run_shell_command` runs both guards; `~/.gemini/skills/` and `.agents/skills/` provide user and project skill discovery | Native per-prompt delivery plus external shell-tool guards |
| Cursor local Agent Chat | `~/.cursor/rules/master-repo-auto.mdc` is an always-applied global rule; `~/.cursor/hooks.json` runs the session injector and pre-tool guards; `~/.cursor/skills/` carries skills | Per-prompt global rule, session-start reinforcement and external pre-tool guards |
| Cursor local project | `.cursor/rules/master-repo-auto.mdc` carries the project-scoped rule and `.cursor/hooks.json` carries both `preToolUse` guards | Repository rule and command guards in a trusted workspace, independent of the user's global copy; the user-level hook supplies local `sessionStart` |
| Cursor Cmd+K and Inline Edit | Cursor Agent hooks apply to Cmd+K, but Cursor User Rules are documented for Agent Chat rather than Inline Edit | Session and pre-tool hook coverage without a claim that the global User Rule is injected into every Inline Edit |
| Cursor Tab | Tab uses its own completion and hook surface | Do not treat Agent Chat or Cmd+K coverage as Tab coverage |
| Cursor Cloud Agent | The tracked `.cursor/rules/master-repo-auto.mdc`, `.cursor/hooks.json`, `.agents/skills/` mirror and root `AGENTS.md` travel with the repository | Project rule, project skills and cloud-supported project hooks; local `~/.cursor/*` files do not travel to managed cloud workers, and managed cloud does not run `sessionStart` |
| GitHub Copilot CLI interactive chat and code | `~/.copilot/copilot-instructions.md` and `COPILOT_CUSTOM_INSTRUCTIONS_DIRS` carry rules; `~/.copilot/hooks/master-repo-auto.json` runs the `userPromptTransformed` per-turn rewrite, session-start reinforcement and both pre-tool guards | Native per-prompt rewrite, global instructions, session context and external pre-tool guards |
| GitHub Copilot web or IDE Chat | `.github/copilot-instructions.md` applies when this repository is in scope | Repository instruction behavior only; local CLI hooks do not run in ordinary web or IDE chat |
| GitHub Copilot coding agent | `.github/copilot-instructions.md`, `.github/hooks/master-repo-auto.json` and the `.agents/skills/` mirror travel with the repository | Repository instructions, project skills, native per-prompt rewrite, session-start context and pre-tool guards inside the coding-agent job; user-level `~/.copilot/*` files are not present there |
| ChatGPT, Claude.ai and Gemini on the hosted web | Account or project instructions and an authorized repository connection | Product-managed instructions only; a local repository cannot silently modify every hosted conversation |
| Local model runtimes | A wrapper, gateway or orchestrator must prepend the pipeline to each request | Deterministic delivery only when every request actually passes through that harness |

The Web UI selector can group chosen clients and generate the right setup steps.
It cannot grant itself access to a hosted account, edit account-wide settings or
intercept prompts sent directly to another provider.

## Harness, plugin or global command?

For deterministic every-prompt delivery, something must own the request path:

- Use a native pre-prompt hook when the client provides one. This is the Claude
  Code, Codex, Gemini CLI and Antigravity path implemented here. Codex
  additionally requires one-time review and trust for each unmanaged hook
  definition.
- Pair per-prompt global rules with a native session-start context hook when a
  client does not let command hooks rewrite every prompt. This is the Cursor
  path.
- Use Copilot's `userPromptTransformed` event for a native per-turn rewrite;
  retain global instructions and `sessionStart` as the standing and initial
  layers.
- Use a local harness, model gateway or orchestrator for local models and for
  clients whose requests can be routed through it.
- Use a plugin only if that plugin receives every request. A plugin that is
  merely available in a catalog is still conditional and cannot enforce itself.
- Use global instructions as the broad compatibility fallback. They provide the
  standing rule but are not an external guard and may be subject to the host
  product's context, precedence and compaction behavior.

No repository file can create a universal hook inside unrelated hosted web
products. Each provider must expose a native interception point, or the request
must pass through a harness controlled by the user.

## Install

Every path below is safe to rerun. The installer updates only the marked
`MASTER-REPO-USE` block, merges skill files without deleting extra files, and
preserves other client settings. Use `--dry-run` to inspect the planned changes.

### Any machine with Python

```bash
python scripts/install_auto_mode.py
```

Add `--no-hook` to install the instruction blocks, Cursor rules and skill copies
without registering Claude Code, Codex, Gemini CLI, Antigravity, Cursor or
Copilot hooks.

### Windows PowerShell

Run the Python script with Python, not PowerShell's `-File` switch:

```powershell
python "$HOME\Downloads\Master-Repo-Use\scripts\install_auto_mode.py" --repo "$HOME\Downloads\Master-Repo-Use"
```

Or use the PowerShell wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\Master-Repo-Use\scripts\setup-global-ai.ps1" -RepoPath "$HOME\Downloads\Master-Repo-Use" -AutoSkills
```

To configure only Cursor:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\Master-Repo-Use\scripts\setup-global-ai.ps1" -RepoPath "$HOME\Downloads\Master-Repo-Use" -Client cursor -AutoSkills
```

### WSL and Ubuntu

WSL has its own home directory and client configuration. A Windows install does
not configure the WSL home, so run the installer inside the distribution too:

```bash
wsl -e bash -lc "cd /mnt/c/Users/Charl/Downloads/Master-Repo-Use && python3 scripts/install_auto_mode.py"
```

From inside Ubuntu directly:

```bash
python3 /mnt/c/Users/Charl/Downloads/Master-Repo-Use/scripts/install_auto_mode.py
```

### macOS and Linux

```bash
bash ~/Master-Repo-Use/scripts/setup-global-ai.sh ~/Master-Repo-Use --auto-skills
```

To configure only Cursor on Bash, WSL, macOS or Linux:

```bash
bash ~/Master-Repo-Use/scripts/setup-global-ai.sh ~/Master-Repo-Use --client cursor --auto-skills
```

### A machine that does not have the repository yet

```bash
git clone https://github.com/Charlesganu2004/Master-Repo-Use.git ~/Master-Repo-Use && python3 ~/Master-Repo-Use/scripts/install_auto_mode.py
```

## What the guards do

`no_prune_guard.py` blocks matching destructive Bash commands aimed at protected
skills, plugins, agents, MCP configuration, client contracts, hook sources and
catalog paths. A deliberate approved removal requires the documented
`# APPROVED PRUNE` suffix.

`no_compress_guard.py` blocks matching compression or truncation commands that
would rewrite a protected `NO-COMPRESS` block or a capability definition. A
deliberate approved recompression requires `# APPROVED RECOMPRESS`.

Both guards are deliberately narrow. They do not inspect deletions performed in
a graphical UI, direct file writes from tools that do not pass through the Bash
hook, administrator actions or clients that do not load the registered hooks.

## Verify an install

Run the repository tests:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

For Claude Code, confirm that `~/.claude/settings.json` contains both
`PreToolUse` guards and a `UserPromptSubmit` entry naming `skill_pipeline`.
Confirm that `~/.claude/skills/` contains the repository skills.

For Antigravity, confirm that `~/.gemini/config/hooks.json` contains an enabled
`master-repo-pipeline` entry with `PreInvocation`, and that
`~/.gemini/config/skills/` contains the repository skills.

For Gemini CLI, confirm `~/.gemini/settings.json` contains `BeforeAgent` for the
standing pipeline and two `BeforeTool` entries matched to `run_shell_command`.
Confirm its user skills under `~/.gemini/skills/`; the tracked
`.agents/skills/` mirror supplies workspace skills when the repository is in
scope.

For Cursor local, confirm the always-applied rule at
`~/.cursor/rules/master-repo-auto.mdc`, the skill folders under
`~/.cursor/skills/`, and `sessionStart` plus `preToolUse` in
`~/.cursor/hooks.json`. For Cursor cloud, confirm the tracked project rule and
hook files exist. Managed cloud workers do not load the local home-directory
files.

For Copilot CLI, confirm the marked block in
`~/.copilot/copilot-instructions.md`, skills under `~/.copilot/skills/`, and
`userPromptTransformed`, `sessionStart` and `PreToolUse` in
`~/.copilot/hooks/master-repo-auto.json`. For Copilot coding agent, confirm the
tracked `.github/hooks/master-repo-auto.json` file exists.

For Codex, confirm `~/.codex/hooks.json` contains `UserPromptSubmit` and both
`PreToolUse` guards, and confirm skills exist under `~/.agents/skills/` and
`~/.codex/skills/`. Then review and trust the exact hook definitions once in the
Codex Hooks UI. Registration alone does not mean an unmanaged hook executed;
Codex skips it until trusted and asks for review again after its definition
changes.

## Honest limits

- The pipeline selects from capabilities the client can actually see. It does
  not install every plugin, MCP server or third-party repository automatically.
- `rtk` and `rtt` must be installed separately. Referencing a tool does not
  install it.
- The guards protect matching Bash commands only on clients where they are
  registered. They are not operating-system access controls.
- Codex unmanaged hooks are inert until their exact definitions are reviewed
  and trusted. This is a one-time setup gate, not a slash required on each
  prompt.
- Cursor local Agent coverage does not imply identical behavior in Cursor Tab.
  Cursor managed cloud loads tracked project hooks, not local user hooks, and it
  does not run the local `sessionStart` path.
- Copilot CLI hooks do not run in ordinary Copilot web or IDE Chat. The Copilot
  coding agent loads tracked repository hooks in its own cloud job.
- Hosted web products retain control over account instructions, connected
  repositories, enabled tools and the context supplied to each conversation.
- A native hook or an owned request harness is required if instruction-based
  behavior is not strong enough for the deployment.

## Product references

- [Cursor rules](https://cursor.com/docs/rules)
- [Cursor hooks](https://cursor.com/docs/hooks)
- [Cursor skills](https://cursor.com/docs/skills)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [Gemini CLI hooks reference](https://geminicli.com/docs/hooks/reference/)
- [Gemini CLI agent skills](https://geminicli.com/docs/cli/skills/)
- [GitHub Copilot CLI custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions)
- [GitHub Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference)
