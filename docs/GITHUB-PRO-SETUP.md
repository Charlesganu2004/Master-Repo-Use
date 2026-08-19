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
2. Sets the default `GITHUB_TOKEN` to read-only and enables the one Actions workflow permission required for GitHub Actions to open pull requests.
3. Applies `scripts/branch-protection.json` to `main`.
4. Prints a verification block: `has_pages`, Pages build type and URL, `protected`, required reviews, Code Owner reviews, force pushes, deletions.
5. Dispatches the Pages deployment **once**, and only if the API confirms Pages is enabled.

It does **not** dispatch the Catalog Guardian audit, because that already runs weekly.
Pass `--run-audit` (bash) or `-RunAudit` (PowerShell) if you want to seed one now.

To re-check state later without changing anything or spending a runner minute:

```bash
bash scripts/enable-github-pro.sh --verify
```

```powershell
& "$HOME\Master-Repo-Use\scripts\enable-github-pro.ps1" -VerifyOnly
```

## What it does not do

- It does not make the private source repository public.
- It does not publish the private catalog or detailed security findings to Pages. The Pages artifact contains only the interactive page plus privacy-safe health counts.
- It does not let Catalog Guardian merge `main` automatically.
- It does not approve the `[Catalog Audit]` issue for you.
- It does not call GPT, Claude, Copilot, or Codex.
- It does not enable the optional token/work budget.
- It does not configure Codespaces, GitHub Models, Spark, or any paid AI credits.

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

## Cost control

See [COST-CONTROL.md](COST-CONTROL.md) for the Actions minute budget, the billing
alerts to enable, and the rules any new workflow has to follow.
