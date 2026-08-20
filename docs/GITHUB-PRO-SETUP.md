# GitHub Pro Setup

Use this once to finish the server-side setup for `Charlesganu2004/Master-Repo-Use`, and rerun it whenever `scripts/branch-protection.json` changes.

The repo-side workflows/config describe the desired state. This bootstrap changes the GitHub server settings that committed files cannot change by themselves.

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
2. Sets the default `GITHUB_TOKEN` to read-only and enables the Actions repository permission required for approved maintenance to open pull requests.
3. Applies `scripts/branch-protection.json` to `main`.
4. Verifies `has_pages`, Pages build type/URL, protected state, required status contexts, server review count, Code Owner-review flag, conversation resolution, force pushes, and deletions.
5. Dispatches the Pages deployment **once**, and only if the API confirms Pages is enabled.

It does **not** dispatch the Catalog Guardian audit, because that already runs weekly. Pass `--run-audit` (bash) or `-RunAudit` (PowerShell) if you want to seed one now.

To re-check state later without changing anything or spending a runner minute:

```bash
bash scripts/enable-github-pro.sh --verify
```

```powershell
& "$HOME\Master-Repo-Use\scripts\enable-github-pro.ps1" -VerifyOnly
```

## Protected-main approval model

`main` requires a PR and the `owner-approval` status context. That status is bound to the exact current PR head SHA.

There are two approval paths:

- **Agent/bot/other-authored PR:** `Charlesganu2004` must submit a normal GitHub `APPROVED` review on the current head commit. A new commit invalidates the old approval.
- **Charles-authored PR:** GitHub does not permit the PR author to approve their own review, so Charles instead posts this exact PR conversation comment using the current 40-character head SHA:

```text
APPROVE OWNER PR <CURRENT_HEAD_SHA>
```

Obtain the current SHA with:

```bash
gh pr view PR_NUMBER -R Charlesganu2004/Master-Repo-Use --json headRefOid --jq .headRefOid
```

The server-side `required_approving_review_count` is intentionally `0` and `require_code_owner_reviews` is `false`. This does **not** remove Charles's gate: `.github/workflows/owner-approval.yml` and `scripts/owner_approval.py` enforce Charles's current-head approval and publish the required `owner-approval` status. Keeping a second mandatory GitHub review would make Charles-authored PRs impossible to satisfy without another reviewer.

The workflow uses trusted default-branch code and never checks out or executes PR-head code under `pull_request_target`.

`enforce_admins` remains off so Charles retains an emergency recovery bypass. Normal automation must not use that bypass.

## Important bootstrap note after changing approval policy

A PR that *introduces a new owner-approval implementation* is a bootstrap case: the new workflow is not trusted default-branch code until that PR is merged. If the old protection policy itself deadlocks that PR, Charles may use the existing `enforce_admins:false` emergency bypass **only after explicitly approving that exact PR/head**, then immediately rerun this bootstrap from updated `main` so the server protection matches the newly merged policy.

Do not permanently disable branch protection to get around the bootstrap.

After that bootstrap merge, verify the server policy without dispatching Actions:

```bash
gh api repos/Charlesganu2004/Master-Repo-Use/branches/main/protection --jq '{status:.required_status_checks.contexts,reviews:.required_pull_request_reviews.required_approving_review_count,code_owner:.required_pull_request_reviews.require_code_owner_reviews,force:.allow_force_pushes.enabled,delete:.allow_deletions.enabled}'
```

Expected approval fields are `status:["owner-approval"]`, `reviews:0`, and `code_owner:false`; force push and deletion must remain `false`.

## What it does not do

- It does not make the private source repository public.
- It does not publish the private catalog or detailed security findings to Pages. The public builder strips `data-private` markup and publishes count/policy data only; CI rejects catalog names/private findings in the artifact.
- It does not let Catalog Guardian merge `main` automatically.
- It does not approve the `[Catalog Audit]` issue for you.
- It does not call GPT, Claude, Copilot, or Codex.
- It does not enable the optional token/work budget.
- It does not configure Codespaces, GitHub Models, Spark, or any paid AI credits.

## Catalog-maintenance approval after setup

If Catalog Guardian creates or refreshes `[Catalog Audit] Owner approval required`, review it and comment exactly:

```text
APPROVE CATALOG MAINTENANCE
```

That triggers the deeper deterministic scan and an automation PR. The resulting PR still needs the separate current-head owner approval gate before merge.

Use `APPROVE AI MAINTENANCE` only for the separate optional model-assisted modernization path when deterministic tooling cannot make the decision safely.

## GitHub Pages privacy note

GitHub Pro can publish Pages from a private source repository, but the normal personal Pages site is public. For that reason `pages.yml` publishes only privacy-safe content:

- a sanitized `index.html` with all `data-private` elements/subtrees stripped;
- `docs/catalog-status.svg` containing aggregate counts only;
- sanitized `docs/catalog-status.json` containing counts/policy and no per-repository rows.

`scripts/build_public_site.py --verify-only` fails if a catalog repository name, private lifecycle/security note, scanner detail, or leftover `data-private` markup reaches the public artifact.

For the full private repo-by-repo table, run the interactive page locally from your clone.

## Cost control

See [COST-CONTROL.md](COST-CONTROL.md) for the Actions minute budget, billing alerts, and the rules any new workflow has to follow.