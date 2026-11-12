---
name: catalog-freshness
description: Use when checking whether catalogued repos, dependencies, or pinned tools are still maintained - and when deciding what to do about one that has gone stale. Covers running the automated check, reading the result, and replacing an abandoned dependency safely.
---

# Catalog Freshness

## The problem

A curated list rots silently. The links keep working. The README still reads well. Nothing
announces that the project stopped being maintained eighteen months ago — and an unmaintained
security-relevant dependency is a liability, not a convenience.

Star counts do not tell you this. They are a lagging indicator of past popularity, not current
maintenance. Check commits and issue responsiveness instead.

## Running the check

```bash
GITHUB_TOKEN=... python scripts/check_freshness.py
```

Reads every `repo-lists/*.txt`, queries GitHub, rewrites the status block in
`docs/REPO-HEALTH.md`, and exits non-zero if anything needs attention.

| Flag | Effect |
|---|---|
| `--check-only` | Report and set exit code, write nothing |
| `--json out.json` | Also emit machine-readable results |
| `--limit N` | Check only the first N repos (for testing) |

| Exit | Meaning |
|---|---|
| 0 | Everything active or slow |
| 1 | At least one repo stale, archived, deprecated, unmaintained, or missing |
| 2 | Check could not complete (network or rate limit) |

**Set `GITHUB_TOKEN`.** Unauthenticated GitHub allows 60 requests/hour. A catalog of a couple
hundred repos cannot be checked in one pass without a token, and a partial check that looks
complete is worse than no check.

Exit code 2 is not "healthy". Treat an incomplete check as unknown, not as a pass.

## Status thresholds

| Status | Rule | What to do |
|---|---|---|
| `active` | Pushed within 90 days | Safe |
| `slow` | 90–365 days | Fine, but watch it |
| `stale` | 1 year to 18 months | Research alternatives before new adoption |
| `unmaintained` | 18+ months | Do not use for new work |
| `archived` | GitHub archived flag | Replace |
| `deprecated` | Maintainer says so | Use their named replacement |
| `missing` | 404 — deleted, renamed, or made private | Investigate immediately |

`missing` deserves special attention. A repo that disappears may have been renamed (usually
benign) or removed for cause (not benign). Find out which before restoring the link — and if the
name was freed up, treat anything now occupying it as untrusted until vetted.

## Automation

`.github/workflows/repo-freshness.yml` runs the check weekly, commits the refreshed
`REPO-HEALTH.md`, and maintains exactly one tracking issue labelled `catalog-freshness` —
opening it when repos degrade, updating it as the set changes, closing it when everything
recovers. One issue, not a new one every week.

## Deciding what to do about a stale repo

Staleness is not automatically disqualifying. Ask in this order:

1. **Is it finished?** Some libraries are small, correct, and genuinely done. A stable parser
   with no commits in two years may be fine. A web framework in the same state is not.
2. **What is the blast radius?** A stale doc-generation tool is a nuisance. A stale crypto,
   auth, or network-parsing library is a security problem.
3. **Are there open CVEs with no fix?** This converts "stale" into "remove".
4. **Has the community moved?** Look for a widely-adopted fork. Prefer one with a real
   maintainer team over one person's copy.

Then pick: **keep and document the risk**, **replace**, or **drop**.

## Replacing a dependency

Any replacement is a new third-party dependency and goes through the full check first —
see [dep-audit](../dep-audit/SKILL.md) and [docs/SECURITY-SCANNING.md](../../docs/SECURITY-SCANNING.md).

Forks need extra care. A fork of an abandoned project is exactly the shape a supply-chain
attack takes: familiar name, plausible story, new maintainer nobody has vetted. Confirm the
maintainer has a real history, check what the fork changed relative to upstream, and never
adopt a fork solely because it appears first in search results.

Record the outcome in [docs/VETTING-REPORT.md](../../docs/VETTING-REPORT.md), including
rejections, so the same dead repo is not re-proposed in six months.

## Keeping the check honest

- Do not widen the thresholds to make the report green. The point is to surface decay.
- Do not mark something `active` because it "seems fine" — the check reads commit dates.
- If the run aborts on rate limit, say the check is incomplete. Never report a partial
  scan as a clean bill of health.

## Related

- [dep-audit](../dep-audit/SKILL.md) — security vetting for anything new
- [verify-before-complete](../verify-before-complete/SKILL.md) — run the check, quote the output
- [agents/repo-issue-iris.md](../../agents/repo-issue-iris.md) — repo issue triage
- [agents/dependency-watch-delta.md](../../agents/dependency-watch-delta.md) — package-level version drift
