# Auto mode

Auto mode makes your skills, tools, agents and MCP servers behave the same way
in every conversation, on every client, without paying for that consistency in
tokens on each session.

## Why it is built in three layers

The obvious approach, writing the rules into each client's global instruction
file, costs about **616 tokens per session per client**. Four clients, every
session, forever. That is worse than the problem it solves.

So the rules are split by what each layer actually costs:

| Layer | File | Cost per session | Carries |
|---|---|---|---|
| Hook | `scripts/hooks/no_prune_guard.py` | **0 tokens** | Deletion protection, enforced outside the model |
| Skill | `skills/master-repo-auto/SKILL.md` | Name and description only | Token discipline, compression safety, full no-prune policy |
| Block | `docs/auto-mode-block.txt` | About 120 tokens | The two rules that must be known before any lookup |

Total standing cost is roughly **120 tokens** instead of 616, and the deletion
protection is genuinely free because a hook runs outside the model context.

### What "carries over with no token cost" can and cannot mean

Honestly: a capability the model must *know about* costs something. A skill's
name and description sit in the listing, roughly 20 to 40 tokens each. That is
the floor for anything discoverable.

Truly zero is available only for things that do not need the model at all, which
is why deletion protection is a hook rather than a sentence in a prompt. A hook
works when the model is distracted, mid-compaction, or on a different client
entirely.

## Install

Every path below wires all three layers and is safe to re-run. The block is
delimited by `<!-- MASTER-REPO-USE:BEGIN -->` and `<!-- MASTER-REPO-USE:END -->`
and replaced in place, so it never duplicates and never disturbs your own text.

### Any machine with Python (the portable path)

```bash
python scripts/install_auto_mode.py
```

This detects Windows, WSL, macOS or Linux on its own. Add `--dry-run` to see
exactly what it would touch first, `--no-hook` to install instructions only.

### Windows PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\Master-Repo-Use\scripts\install_auto_mode.py"
```

Or the older wrapper, which also sets the Copilot environment variable and the
watermark helper:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\Master-Repo-Use\scripts\setup-global-ai.ps1" -RepoPath "$HOME\Downloads\Master-Repo-Use" -AutoSkills
```

### WSL and Ubuntu

WSL has its own home directory and its own client config, separate from Windows.
Installing on Windows does **not** cover it, so run it inside the distro too:

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

### A machine that does not have the repo yet

```bash
git clone https://github.com/Charlesganu2004/Master-Repo-Use.git ~/Master-Repo-Use && python3 ~/Master-Repo-Use/scripts/install_auto_mode.py
```

### A machine where you cannot register hooks

```bash
python scripts/install_auto_mode.py --no-hook
```

Instructions and skill only. Deletion protection then depends on the model
reading the rules, which is weaker, so prefer the hook wherever it is allowed.

## What the no-prune hook does

It blocks a destructive command aimed at a protected path: `.claude/skills`,
`.claude/plugins`, `.claude/agents`, `.claude/settings.json`, `.mcp.json`,
`repo-lists/`, `skills/`, and the client contract files.

It is deliberately narrow, because a guard that interrupts ordinary work gets
switched off and then protects nothing. It ignores:

- heredoc bodies and single-quoted strings, so writing or grepping text that
  merely mentions a deletion is not treated as one
- plain `>` redirects, which are how these files get written in the first place
- every tool other than Bash

To delete something on purpose, append the override:

```bash
rm -rf ~/.claude/skills/old-thing  # APPROVED PRUNE
```

That is a typed statement of intent, which is the bar the policy asks for.

## Verify an install

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

To confirm the hook is live on this machine, check that `settings.json` has a
`PreToolUse` entry naming `no_prune_guard`, and that
`~/.claude/skills/master-repo-auto` exists.

## Honest limits

- The block cannot change a client's slash-command parser. Claude Code still
  routes the single leading `/command` into that skill. The rule makes a model
  act on further invocations it finds in the message body; it does not make the
  terminal parse two leading slash commands.
- The hook only sees Bash tool calls. Deletions through a client's own UI, or
  through the Write and Edit tools, do not pass through it.
- `rtk` and `rtt` have to be installed separately. The rules reference them, but
  referencing a tool does not install it.
