# Cost Control and Billing Safety

Plan: **GitHub Pro, $4/month.** The goal of this document is that routine metered overage stays at **$0** and nothing in this repository can quietly start spending.

## What matters for this repo

| Product | Cost-control position |
|---|---|
| GitHub Actions | GitHub Pro included usage first; workflows are designed to stay well below the allowance |
| GitHub Pages | deploy only on relevant `main` changes or manual request |
| Codespaces | **not required by this repo** |
| GitHub Models / paid AI credits | **not required or configured by this repo** |
| Snyk | optional only when `SNYK_TOKEN` is deliberately configured |

All repository workflows use `ubuntu-latest`. There are no Windows/macOS/larger/self-hosted runners configured here.

## Scheduled and event-driven work

| Workflow | Trigger | Frequency / intent |
|---|---|---|
| `catalog-guardian.yml` lightweight audit | weekly cron, catalog/security changes, manual | **1×/week** plus real changes |
| `catalog-guardian.yml` deep maintenance | new repo intake or owner approval | **only when required** |
| `pages.yml` | relevant push to `main`, manual | **no recurring schedule after the cost-control PR is merged** |
| `owner-approval.yml` | PR/review/owner-comment events | only while PRs need approval |
| `safety-tests.yml` | relevant PR/main changes | only when security/workflow/site code changes |

**Desired Pages state has no recurring schedule.** The former `cron: '17 */6 * * *'` redeployed a static site four times a day even when nothing changed and is removed by the cost-control PR. Until that PR reaches `main`, the old default-branch workflow can still run; do not describe the branch-only removal as already live.

**There are no scheduled AI/model calls.** No recurring workflow calls Anthropic, OpenAI, Copilot, Codex, Gemini, or another paid model API. `scripts/maintenance_request.py` only prepares a request for explicit human action; it is not a background model worker.

Routine usage is intentionally small relative to the GitHub Pro included allowance. Setup, testing, manual dispatches, and owner-approved deep scans can temporarily use more minutes, so do not treat a fixed monthly estimate as a billing guarantee. The target is **$0 net Actions overage**.

## Owner actions to cap overage

These are account-level settings and are not represented by repository commits. Under **Settings → Billing and licensing → Budgets and alerts**:

1. Enable included-usage alerts (for example **90%** and **100%**) for Actions.
2. Create an **Actions-scoped** budget with a small overage ceiling such as **$1/month** and enable **Stop usage when budget limit is reached**, if that option is available for the account/product.
3. Do not enable Codespaces, paid GitHub Models, Spark, paid AI credits, or paid scanner plans merely for this repository unless there is a deliberate need.

The billing UI may show a **gross** amount for metered usage even when included usage discounts reduce the **billed/net amount to $0**. Check the billed/net amount rather than interpreting gross usage as a charge.

## Rules for future workflows

Any new or changed workflow should follow these defaults unless a concrete technical requirement justifies an exception:

- `ubuntu-latest`;
- explicit `timeout-minutes`;
- least-privilege `permissions`;
- `concurrency` / `cancel-in-progress` for replaceable runs;
- no polling when an event trigger exists;
- no recurring deployment of unchanged static content;
- no automatically scheduled paid AI/model calls;
- deep security work only on new/flagged/owner-approved items;
- never merge protected `main` automatically;
- never weaken the `owner-approval` gate just to make a workflow green.

Do not re-dispatch a failing workflow merely to “see if it passes.” Diagnose the failed step first. `scripts/enable-github-pro.sh --verify` / `-VerifyOnly` checks server state without dispatching a runner.

## Approval and cost interaction

The desired required `owner-approval` status is event-driven and SHA-bound. It does not poll.

- Agent/bot/other-authored PRs require Charles's `APPROVED` review on the current head SHA.
- Charles-authored PRs require the exact `APPROVE OWNER PR <CURRENT_HEAD_SHA>` PR conversation comment from Charles.
- A new commit changes the SHA and invalidates the old approval without a recurring runner.

The safety workflow runs real `unittest` assertions only when relevant scripts/tests/workflows/site files change. That small amount of CI compute is intentional because it prevents security/privacy logic from being “green” without actually asserting anything.

## Deep scans

Deep scans can install Semgrep, Gitleaks, OSV Scanner, ClamAV, and optionally Snyk when explicitly configured. They are intentionally not part of the weekly baseline for every catalog entry.

A deep scan should happen for:

- a newly added catalog repo;
- an item flagged for security/lifecycle review;
- an owner-approved maintenance run;
- a deliberate manual investigation.

This concentrates runner minutes where they have security value rather than spending them continuously.

## Checking spend

Use **Settings → Billing and licensing → Usage**, filtered to Actions, and distinguish **gross usage** from the **billed/net amount** after included usage.