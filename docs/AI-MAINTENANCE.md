# AI Maintenance — Approval-Driven, No Background Model Spend

The Master Repo does **not** run recurring GPT, Claude, Copilot, Codex, or other paid model calls in the background.

Instead, maintenance is **monthly on next use**:

1. A supported local AI client opens a normal Master Repo-aware session.
2. Its global/repo instructions run:

   ```bash
   python scripts/maintenance_request.py --auto
   ```

3. The script uses the GitHub CLI/API to check whether an `[AI Maintenance]` issue is already open and whether the last request is at least 30 days old.
4. If a review is due, the script creates **one GitHub issue** containing the full maintenance prompt and assigns it to `Charlesganu2004`.
5. The AI stops there. It may summarize the request, but it must not change the catalog.
6. Charles approves by stating or commenting the exact phrase:

   ```text
   APPROVE AI MAINTENANCE
   ```

7. During an active AI session, the approved request can then be executed: inspect repos, run scans, compare replacements, prepare catalog changes, and open a PR.
8. The PR still requires Charles's review before `main` is merged.

## Why this is the default

A truly autonomous background AI reviewer needs scheduled compute and/or scheduled model/API calls. That can consume private-repository Actions minutes, model tokens, API credits, or subscription limits even when nothing useful changed.

The Master Repo therefore separates **free/cheap request detection** from **AI review work**:

```text
normal AI session starts
        |
        v
maintenance_request.py --auto
        |
        +-- not due --> do normal task
        |
        +-- due --> create one GitHub issue
                         |
                         v
                 WAIT FOR CHARLES
                         |
                 APPROVE AI MAINTENANCE
                         |
                         v
                 AI performs review
                         |
                         v
                   branch + PR
                         |
                         v
                 WAIT FOR CHARLES
                         |
                         v
                       merge
```

## Commands

Check only:

```bash
python scripts/maintenance_request.py --check
```

Recommended AI-client mode:

```bash
python scripts/maintenance_request.py --auto
```

Generate a local request without creating a GitHub issue:

```bash
python scripts/maintenance_request.py --generate
```

Explicitly create the GitHub issue if due:

```bash
python scripts/maintenance_request.py --open-issue
```

Use a different request interval:

```bash
python scripts/maintenance_request.py --auto --interval-days 45
```

The default is **30 days**. This is intentionally shorter than the 120-day stale threshold, giving several chances to notice a project slowing down before it becomes stale.

## What the AI maintenance review must check

After owner approval, review all new, stale, archived, disabled, deleted, replacement, and security-flagged repos. For each one:

- current upstream commits and releases/tags;
- README/archive/sunset/EOL notices;
- maintained successor or better replacement;
- runtime dependency versus static research/reference artifact;
- license and whether managed maintenance/forking is permitted;
- invisible/bidirectional Unicode and hidden-text patterns;
- prompt/instruction injection risks in agent/MCP content;
- SQL injection and command-injection patterns;
- embedded executable files and suspicious install hooks;
- private keys/secrets and credential-exfiltration patterns;
- dependency vulnerabilities and malware indicators;
- MCP filesystem/network/command scope;
- OSSF/security posture when available.

Use the repository's scanner stack where appropriate: Guardian, Semgrep/OpenGrep, Gitleaks/TruffleHog, Trivy, OSV Scanner, Snyk, ClamAV, OSSF Scorecard, Syft/Cosign, Cisco AI Defense MCP Scanner, and Garak.

## Lifecycle policy

- **0–120 days since last push:** healthy from a freshness perspective.
- **121–269 days:** stale warning.
- **270–365 days:** replacement / managed-adoption review.
- **>365 days:** remove from the active/runtime catalog unless Charles approves a stability/reference exception.
- **Archived + recent development/release:** review the reason first; archive status alone does not mean dead.
- **Archived + explicit sunset/EOL:** move toward replacement/reference/managed adoption even when the final release is recent.
- **Static research/reference repos:** can be retained through `repo-lists/lifecycle-overrides.json` when inactivity is expected.
- **Deleted/disabled or confirmed CRITICAL security finding:** immediate removal candidate.

## GitHub Actions

`.github/workflows/catalog-guardian.yml` is **manual-only**. It has no cron schedule. Charles may run it from **Actions → Catalog Guardian (Manual / Owner Approved) → Run workflow** when a cloud scan is wanted.

For zero Actions usage, run locally instead:

```bash
python scripts/catalog_guardian.py
```

or a deeper local scan:

```bash
python scripts/catalog_guardian.py --deep --batch-size 12
```

Local execution does not consume GitHub-hosted Actions minutes.

## Online GPT / Claude / Copilot

Browser-hosted products cannot be forced by this repository to execute a local Python script in every conversation. When the private repo is connected/selected, their repository instructions instead tell the AI to look for an open `[AI Maintenance]` issue and use the same approval phrase and PR gate.

If the online environment supports GitHub issue writes, it may create the request when due. If it does not, it should present the maintenance prompt to Charles rather than claim the request was created.
