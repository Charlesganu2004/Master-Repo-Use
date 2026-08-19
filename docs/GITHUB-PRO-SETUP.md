# GitHub Pro Setup

Use this once to finish the server-side setup for `Charlesganu2004/Master-Repo-Use`.

The repo-side workflows/config are already committed. This bootstrap changes the GitHub server settings that committed files cannot change by themselves.

## Windows / PowerShell — one command

```powershell
$p="$HOME\Master-Repo-Use"; if (Test-Path "$p\.git") { git -C $p pull --ff-only } else { gh repo clone Charlesganu2004/Master-Repo-Use $p }; & "$p\scripts\enable-github-pro.ps1"
```

## Bash / WSL / macOS / Linux — one command

```bash
p="$HOME/Master-Repo-Use"; if [ -d "$p/.git" ]; then git -C "$p" pull --ff-only; else gh repo clone Charlesganu2004/Master-Repo-Use "$p"; fi; bash "$p/scripts/enable-github-pro.sh"
```

## What the bootstrap does

1. Enables GitHub Pages with `build_type=workflow`.
2. Enables the repository Actions workflow permission required for GitHub Actions to create pull requests.
3. Applies `scripts/branch-protection.json` to `main`.
4. Dispatches the Pages deployment workflow.
5. Dispatches the Catalog Guardian audit workflow.

## What it does not do

- It does not make the private source repository public.
- It does not publish the private catalog or detailed security findings to Pages. The Pages artifact contains only the interactive page plus privacy-safe health counts.
- It does not let Catalog Guardian merge `main` automatically.
- It does not approve the `[Catalog Audit]` issue for you.
- It does not call GPT, Claude, Copilot, or Codex.
- It does not enable the optional token/work budget.

## Owner approval after setup

If Catalog Guardian creates or refreshes `[Catalog Audit] Owner approval required`, review it and comment exactly:

```text
APPROVE CATALOG MAINTENANCE
```

That triggers the deeper deterministic scan and an automation PR. The PR still requires your review before merge.

Use `APPROVE AI MAINTENANCE` only for the separate optional model-assisted modernization path when deterministic tooling cannot make the decision safely.

## GitHub Pages privacy note

GitHub Pro can publish Pages from a private source repository, but the normal personal Pages site is public. For that reason `pages.yml` deliberately publishes only:

- `index.html`;
- `docs/catalog-status.svg`;
- a sanitized `docs/catalog-status.json` containing counts/policy but no private repository names or detailed findings.

For the full private repo-by-repo table, run the interactive page locally from your clone.
