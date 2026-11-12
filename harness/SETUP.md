# AI Harness Setup for GitHub Copilot CLI and OpenCode Desktop

This guide sets up a full AI coding harness on a Windows PC. You run one line in PowerShell, then sign in with GitHub. The guide is written for engineers who are new to these tools.

Prefer Copy buttons on every command? Download [SETUP.html](SETUP.html) and open it in a browser.

## 1. What you get

You get OpenCode Desktop and GitHub Copilot CLI, both set up with the same rules, skills and tools. Work is split across small agents, so large tasks stay organized and each result is checked.

- OpenCode Desktop and Copilot CLI share the same rules.
- CaveCrew multi-agent work. In OpenCode the default agent is `orchestrator`. It plans the task and runs `investigator`, `builder` and `reviewer` lanes. It cannot edit files itself. The `build` agent is for quick edits.
- 38 skills, loaded automatically when a task fits.
- `graphify`, `local-rag` and `token-goat` to find code and documents without reading whole files.
- The Playwright and rustwright browser tools.
- GitHub Copilot models, plus Google Vertex models if you have access.

## 2. Before you start

- Windows 10 or 11.
- A GitHub account with a Copilot seat.
- `winget` (the App Installer). Check with `winget --version`.
- About 2 GB of free disk space and 15 to 20 minutes.
- For Vertex models only: the Vertex AI User role on the Google Cloud project. Ask the project owner. The project id is `<vertex-project-id>`.

## 3. Install

Open PowerShell (not as administrator) and run one of these lines.

Copilot models only:

```powershell
irm https://raw.githubusercontent.com/Charlesganu2004/Master-Repo-Use/main/harness/install.ps1 | iex
```

With Google Vertex models:

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/Charlesganu2004/Master-Repo-Use/main/harness/install.ps1))) -VertexProject <vertex-project-id>
```

The installer does these 7 steps:

1. Checks Windows, PowerShell and `winget`. Only a Restricted execution policy is changed automatically, to RemoteSigned for your user. With AllSigned the installer asks first. If you say no, the npm command shims will not run.
2. Installs the apps, per user where possible: Git, GitHub CLI, GitHub Copilot CLI, Python 3.12 and OpenCode Desktop 2.2.7. With `-VertexProject` it also installs the Google Cloud SDK. With `-WithClaudeCode` it installs Claude Code. OpenCode Desktop comes from the GitHub release, because opencode.ai is blocked on some corporate networks.
3. Clones or updates the Master Repo (public, git over HTTPS, with a zip fallback).
4. Installs the tools into `%USERPROFILE%\.local` and adds `.local\node` and `.local\bin` to your user PATH. The tools are portable Node 24.20.0, uv, graphify 0.9.79 (with graphify-mcp), token-goat 2.9.1, Playwright MCP 0.0.80 with Chromium, rustwright-mcp 0.1.0 and the local-rag engine (in `.local\lib\kb`, with its own Python 3.12 environment, plus the `local-rag` command).
5. Writes the harness files, after a backup. For OpenCode it writes the `AGENTS.md` rule blocks, merges `opencode.json` (orchestrator as default agent, the three lanes, MCP servers, the Copilot skills folder, the Vertex provider if chosen), and adds the `graphify.js` and `rate-limit-wait.js` plugins and the graphify skill. For Copilot CLI it writes the `copilot-instructions.md` rule blocks, the CaveCrew agents, the hooks, a merged `mcp-config.json`, 38 skills and `bin/rustwright-launch.js`. It also adds the token-goat skill to `~/.claude/skills`.
6. Asks you to sign in (see section 4). Skip this with `-NoSignIn`.
7. Prints a summary: versions, counts and the backup folder.

The installer is safe to rerun. Backups go to `%USERPROFILE%\.harness-backup\<timestamp>`.

The OpenCode Desktop installer, uv and Node downloads are checked against pinned SHA-256 hashes before anything runs.

### Options

| Option | What it does |
| --- | --- |
| `-RepoPath` | Where the Master Repo lives. Default `$HOME\Master-Repo-Use`. |
| `-Branch` | Branch to use. Default `main`. |
| `-VertexProject` | Adds Google Vertex models and installs the Google Cloud SDK. |
| `-VertexLocation` | Vertex location. Default `us`. |
| `-OpenCodeVersion` | OpenCode Desktop version. Default `2.2.7`. |
| `-WithClaudeCode` | Also installs Claude Code. Only needed for the signed-in Edge browser flow. |
| `-SkipApps` | Skips app installs. |
| `-SkipTools` | Skips tool installs. |
| `-NoSignIn` | Skips the sign-in prompts. |
| `-NoPathUpdate` | Advanced. Skips writing the user PATH. Implied by `-TargetHome`. |
| `-TargetHome` | Writes to another home folder. For testing only. |
| `-SandboxTools` | Testing. With `-TargetHome`, also installs the tools inside the target folder. |
| `-DryRun` | Lists what would happen and changes nothing. On a PC without the repo it skips the harness file details until the repo is cloned. |

The `irm | iex` line cannot take options. To change a setting with that line, set these environment variables first: `HARNESS_REPO_PATH`, `HARNESS_BRANCH`, `HARNESS_VERTEX_PROJECT`, `HARNESS_VERTEX_LOCATION` and `HARNESS_NO_PATH_UPDATE` (set it to `1` to skip the PATH update). For example:

```powershell
$env:HARNESS_VERTEX_PROJECT = "<vertex-project-id>"
irm https://raw.githubusercontent.com/Charlesganu2004/Master-Repo-Use/main/harness/install.ps1 | iex
```

## 4. Sign in with GitHub

The installer prompts you to sign in. If you skipped it, or a code expired, sign in by hand.

Copilot CLI:

```powershell
copilot login
```

You can also type `/login` inside `copilot`.

OpenCode:

```powershell
& (Get-ChildItem "$env:APPDATA\ai.opencode.desktop\cli\*\opencode-cli.exe" | Select-Object -Last 1).FullName auth login github-copilot --method device --answer deploymentType=github.com
```

The command prints a code. Enter it at https://github.com/login/device and approve the sign-in.

In OpenCode Desktop you can also connect GitHub Copilot from the provider settings. Menu names can differ by version. The command above always works.

GitHub CLI (optional):

```powershell
gh auth login
```

Google Vertex (only if you installed with `-VertexProject`):

```powershell
gcloud auth application-default login
```

```powershell
gcloud auth application-default set-quota-project <vertex-project-id>
```

## 5. Check it works

Open a new terminal, then run:

```powershell
graphify --version
```

Expect `0.9.79`.

```powershell
token-goat --version
```

Expect `2.9.1`.

```powershell
copilot --version
```

```powershell
local-rag memory-search test
```

This returns results or none, without errors.

In OpenCode Desktop, start a new session. The agent picker shows `orchestrator`. Ask "list your subagents". The answer names `investigator`, `builder` and `reviewer`.

## 6. Daily use

OpenCode Desktop:

- A new session starts in `orchestrator`. Describe the task. It plans and hands work to its lanes.
- Switch to `build` for a quick one-line edit.
- Pick a model in the model picker. Copilot models appear after sign-in, Vertex models if you installed with `-VertexProject`.
- The first time you open a repo, the agent builds the graphify graph by itself.

Copilot CLI:

- Open a terminal in a repo folder and run `copilot`.
- The agents and skills load automatically.

## 7. Update

Rerun the same line you used to install. It updates the repo, the tools and the harness files. Your old files are backed up first.

## 8. Troubleshooting

- **opencode.ai is blocked.** The installer already downloads OpenCode Desktop from GitHub, so no action is needed.
- **"running scripts is disabled".** Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then run the install line again.
- **Command not found right after install.** Open a new terminal so the new PATH loads.
- **`winget` is missing.** Install App Installer from the Microsoft Store, then rerun.
- **Vertex shows 403 or 404.** You need access to the project. Ask the project owner for the Vertex AI User role. Keep the location at `us`.
- **The `ollama` entry shows as failed in OpenCode, or clashes with the Ollama tray app.** The installer adds an optional `ollama` entry only on PCs that already have Ollama installed. It starts Ollama's own server (`ollama serve`), which is not an MCP server. OpenCode may show it as failed, or it may clash with the Ollama tray app on port 11434. If that happens, set `"disabled": true` on `mcp.servers.ollama` in `%USERPROFILE%\.config\opencode\opencode.json`.
- **The sign-in code expired.** Rerun the sign-in command to get a new code.

## 9. Undo

Restore your old files from `%USERPROFILE%\.harness-backup\<timestamp>`. Copy the saved files back over the ones in `~/.config/opencode`, `~/.copilot` and `~/.claude`. To remove the apps, use Settings > Apps.

## 10. For maintainers

- Refresh the snapshot with `pwsh harness/export-harness.ps1` (PowerShell 7; Windows PowerShell 5.1 is refused). It needs a local leak-terms file at `%USERPROFILE%\.config\harness\leak-terms.txt` or semicolon-separated terms in `$env:HARNESS_LEAK_TERMS` (not a file path), and it refuses to export without it.
- Do not run the installer on the owner's PC. It asks before it changes anything.
- Render the guide to HTML with:

```powershell
uv run --no-project --with markdown python harness/tools/render_guide.py --in harness/SETUP.md --out-dir harness --html-name SETUP.html --no-md
```

- For a copy with a real project id, add `--set vertex-project-id=<your-project-id>` and a different `--out-dir`. Keep that copy out of the repo.
