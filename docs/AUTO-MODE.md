# Auto mode

One command writes a shared behaviour block into every AI client's global
instruction file, so Claude Code, Codex, Gemini and Copilot all start a session
under the same rules. The rules themselves live in one place,
`docs/auto-mode-block.txt`, and both setup scripts splice that same file in.

## The one liner

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\Master-Repo-Use\scripts\setup-global-ai.ps1" -RepoPath "$HOME\Downloads\Master-Repo-Use" -AutoSkills
```

WSL, Linux, macOS:

```bash
bash ~/Master-Repo-Use/scripts/setup-global-ai.sh ~/Master-Repo-Use --auto-skills
```

Re-run it any time. The block is delimited by `<!-- MASTER-REPO-USE:BEGIN -->`
and `<!-- MASTER-REPO-USE:END -->` markers and is replaced in place, so it never
duplicates and never disturbs anything you wrote around it.

Omit the flag to install the Master Repo block without the auto-mode rules.

## What the block turns on

- **Token discipline.** Route commands through `rtk`, skeleton a repo with `rtt`
  before reading it, compress with the local caveman skills, never paste a whole
  catalog file.
- **Compression safety.** Code blocks, backtick spans, URLs, paths, commands,
  environment variables, headings, versions, dates and error strings stay
  byte-for-byte. A pass saving under 15 percent is a failed pass.
- **No pruning.** Skills, tools, MCP servers, plugins and catalog entries are
  never removed, disabled or unloaded on the model's own initiative. Only an
  explicit request from Charles removes one. Context pressure is not a reason to
  drop a tool silently; the model says the context is tight and asks.
- **Every command runs.** A prompt may carry more than one slash command. All of
  them run, in the order written, each reporting its own result.

Auto mode changes how work is done, never what is permitted. Vetting, licence,
security and approval gates apply exactly as before, and nothing third-party is
installed or executed on the strength of this block.

## Honest limits

The block is instruction text, which is the only mechanism all four clients
share. It steers behaviour reliably but it is not a sandbox.

Two things it cannot do by itself:

- It cannot change a client's own slash-command parser. Claude Code still routes
  the single leading `/command` of a message into that skill. The rule makes the
  model act on further invocations it finds in the body; it does not make the
  terminal parse two leading slash commands.
- It cannot stop a client from compacting a long conversation. What it does stop
  is a model treating compaction as licence to forget which tools it had.

The deterministic parts are wired separately and do not depend on the block:
`rtk` runs as a Claude Code hook, and catalog entries can only be removed
through an owner-approved pull request.
