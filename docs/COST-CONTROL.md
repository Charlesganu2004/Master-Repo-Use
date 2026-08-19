# Cost Control and Billing Safety

Plan: **GitHub Pro, $4/month.** The goal of this document is that routine metered
overage stays at **$0** and nothing in this repository can quietly start spending.

## What GitHub Pro includes

| Product | Included on Pro | This repo's routine use |
|---|---|---|
| Actions minutes (private repos) | **3,000 min/month** on Linux | roughly **20–40 min/month** |
| Actions storage | 1 GB packages/artifacts | Pages artifact only, a few MB |
| GitHub Pages | available from private source repos | 1 deploy per real change |
| Codespaces | 120 core-hours + 15 GB storage | **not used** |
| Copilot / Models / Spark / AI credits | not included | **not used, not configured** |

Linux (`ubuntu-latest`) minutes bill at a **1× multiplier**. Windows is 2× and macOS
is 10×, so every job in this repository runs on `ubuntu-latest`. There are no larger
runners and no self-hosted runners.

## Scheduled work in this repository

| Workflow | Trigger | Frequency | Approx. minutes |
|---|---|---|---|
| `catalog-guardian.yml` (audit) | weekly cron `23 7 * * 1`, push to catalog files, manual | **1×/week** | ~2–4 min/run |
| `catalog-guardian.yml` (deep) | owner comments `APPROVE CATALOG MAINTENANCE` | **only when you ask** | ~20–60 min/run |
| `pages.yml` | push to main touching site/status files, manual | **only on real change** | ~1–2 min/run |
| `owner-approval.yml` | pull request events | per PR event | <1 min/run |

**There is no recurring Pages schedule.** The former `cron: '17 */6 * * *'` was removed:
it redeployed a static site four times a day whether or not anything had changed, which
is roughly 120 pointless runs a month.

**There are no scheduled AI or model calls anywhere.** No workflow calls the Anthropic,
OpenAI, Copilot, or Codex APIs. `scripts/maintenance_request.py` only writes a request
file for a human to act on later; it never calls a paid API by itself.

Expected routine total: **well under 100 minutes/month against a 3,000-minute allowance**,
so the metered Actions bill should stay at $0 even if usage grows several times over.

## Owner actions to make overage structurally impossible

These are account-level settings and cannot be committed to a repository. Do them once at
**Settings → Billing and licensing → Budgets and alerts**:

1. **Included-usage alerts** — enable the **90%** and **100%** included-usage alerts for
   Actions. These are notifications only and cost nothing.
2. **Actions budget** — create a budget scoped to the **Actions** product with a hard limit
   of **$1.00/month**, and enable **"Stop usage when budget limit is reached."**
   With a 3,000-minute allowance this should never trigger; if it does, something is wrong
   and you want it stopped rather than billed.
3. Leave **Codespaces**, **Copilot**, **GitHub Models**, **Spark**, and **AI credits**
   unconfigured. Do not add budgets for them — an unconfigured paid product cannot bill,
   and adding a budget is not a prerequisite for anything here.

## Rules for anything added later

- New workflows run on `ubuntu-latest`. No Windows, macOS, larger, or self-hosted runners.
- Every job sets `timeout-minutes`, so a hang costs minutes instead of hours.
- Every workflow sets `concurrency` with `cancel-in-progress: true` unless cancelling
  would corrupt state (the owner-approved deep maintenance job is the one exception).
- Nothing new gets a `schedule:` trigger without a written reason in this file.
- Deep scanning is gated: it runs for repositories newly added to a catalog list, for
  repositories already flagged REVIEW/REMOVE, or when the owner explicitly approves.
- Do not re-dispatch a failing workflow to "see if it passes." Read the log first.
  `scripts/enable-github-pro.sh --verify` inspects state without spending a runner minute.

## Checking spend

```bash
gh api /users/Charlesganu2004/settings/billing/actions
```

Or **Settings → Billing and licensing → Usage**, filtered to Actions.
