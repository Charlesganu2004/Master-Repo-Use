# Security Scanning and Third-Party Repo Intake

> **Coverage audit, 2026-08-25.** Before this date, **0 of 252** catalogued repositories had ever
> been deep-scanned. Not "scanned and clean" — never scanned. The weekly job was metadata-only,
> the scanner install step was skipped on scheduled runs, and `--deep` sat behind a manual
> approval that had never been given at scale. A rotating read-only deep scan now runs weekly
> without a gate, and coverage is displayed on the site and in a
> `[Security Scan]` issue. See the README section "Security scanning" for the full account.

## Rotation and coverage

- **Schedule:** weekly, `deep-scan-rotation` in `.github/workflows/catalog-guardian.yml`.
- **Slice:** deterministic — whole weeks since the epoch, `--batch-size 20`. About 19 repos per
  run; first full coverage in roughly 13 weeks. Re-running scans the same slice.
- **Read-only:** the job never passes `--apply-removals`. Reporting a risk must not wait on a
  human; *changing* the catalog still requires `APPROVE CATALOG MAINTENANCE`.
- **State:** accumulates through the Actions cache, so `deep_scanned` coverage grows rather than
  resetting every run.
- **Non-fatal installs:** a scanner that fails to install degrades that scanner to
  `SCANNER-ERROR`. It does not fail the run. (On 2026-08-25 a single `go install` failure took
  the entire audit down; `tests/test_workflow_policy.py` now prevents that regression.)

### SCANNER-ERROR means unverified

Not clean. Not flagged. It means a scanner did not complete, so the repository's state is
**unknown** and it stays in the rotation for a rescan. Never report it as a pass.

### Known upstream gotcha

`go install github.com/gitleaks/gitleaks/v8@latest` fails: the project moved org but its `go.mod`
still declares `github.com/zricethezav/gitleaks/v8`. Install via the declared path.

This is the security gate for repositories in `Charlesganu2004/Master-Repo-Use`.

The goal is not to claim that static scanning can prove a repository safe. The goal is to catch common supply-chain, injection, malware, secret, lifecycle, and maintenance risks **before** a repo is trusted or executed.

Related files:

- `scripts/catalog_guardian.py` — automated metadata + source guardian entry point
- `scripts/catalog_security.py` — fail-closed security/redaction helpers
- `.github/workflows/catalog-guardian.yml` — GitHub Pro audit and owner-approval workflow
- `.github/workflows/safety-tests.yml` — assertion-based scanner/approval/privacy CI
- `docs/VETTING-REPORT.md` — vetting history
- `docs/CATALOG-STATUS.md` — current private status
- `docs/SECURITY.md` — repository-level agent/MCP security rules
- `docs/NEW-REPO-VETTING.md` — new-entry procedure

## Current lifecycle policy

Freshness is a maintenance signal, not a security verdict.

- **0–120 days since last push:** healthy from a freshness perspective.
- **121–269 days:** stale warning.
- **270–365 days:** replacement / managed-adoption review.
- **More than 365 days:** remove from the active/runtime catalog unless Charles approves a reference/stability exception.
- **Archived:** inspect archive reason, recent releases, sunset/EOL notice, successor, security state, licensing, and reference value before deciding.
- **Deleted or disabled:** immediate removal candidate.
- **Static research/reference repos:** may receive an explicit `reference` lifecycle override when inactivity is expected.

The 120-day warning is intentionally much earlier than deletion. Fast-moving AI tooling changes quickly, while stable libraries and research artifacts can legitimately be quiet.

## GitHub-first audit model

Routine maintenance does not require GPT, Claude, Copilot, or Codex.

The `Catalog Guardian` workflow runs a lightweight metadata audit weekly and when catalog/security policy files change. It creates or refreshes one `[Catalog Audit]` issue when attention is needed.

Deep maintenance requires Charles's exact issue comment:

```text
APPROVE CATALOG MAINTENANCE
```

After approval, GitHub Actions performs the deeper deterministic scan, prepares lifecycle/removal/adoption changes on an automation branch, and opens a PR. It does **not** merge `main`.

## Threat model

The gate looks for:

| Threat | Examples | Primary checks |
|---|---|---|
| Hidden/invisible instructions | bidi overrides, zero-width controls, hidden prompt text | Guardian Unicode scan + manual context read |
| Prompt/instruction injection | “ignore previous instructions”, secret exfiltration requests, safety bypass text | Guardian prompt-injection heuristics + manual review |
| Install-time execution | npm lifecycle hooks, `setup.py`, custom build backends, `curl | sh` | Guardian patterns + manual Stage B2 |
| SQL/command injection | interpolated SQL, unsafe shell construction | Guardian + Semgrep |
| Credential exposure/exfiltration | private keys, API tokens, code that sends env secrets | Guardian + Gitleaks/Semgrep |
| Malware/binary payloads | PE/ELF binaries, malicious fixtures, suspicious installers | Guardian + ClamAV + manual review |
| Vulnerable dependencies | HIGH/CRITICAL CVEs in runtime dependencies | OSV Scanner; Trivy/Snyk when available |
| CI supply-chain risk | `pull_request_target` + untrusted checkout; event data inside shell | manual workflow review + static audit |
| Typosquat/renamed slug | requested slug resolves to unexpected canonical repo | GitHub metadata canonical-name check |
| Abandonment/sunset | stale, archived, EOL, unsupported project | 120/270/365 lifecycle + successor review |
| License risk | no license, custom restrictions, copyleft obligations | GitHub metadata + manual LICENSE/NOTICE read |

## Automated tools

Owner-approved/new-repo GitHub scans install or use:

- **Semgrep OSS** — SQL/command injection and code-pattern checks.
- **Gitleaks** — committed secret detection.
- **OSV Scanner** — dependency vulnerabilities against OSV.
- **ClamAV** — malware signatures where applicable.
- **Snyk CLI** — optional; used when `SNYK_TOKEN` is configured.

Guardian also supports **Trivy** automatically if it is installed in the runner/environment. The catalog contains additional security projects such as OpenGrep, TruffleHog, Cisco AI Defense MCP Scanner, OSSF Scorecard, Syft, Cosign, and Garak.

## Secret-output handling

The persistence boundary is designed so scanner-returned secret values are not copied into catalog state, issues, PR bodies, or Pages artifacts:

- Gitleaks runs with `--redact` and writes a JSON report. Guardian persists only safe metadata such as the **rule ID, file, and line**. An unreadable/empty report after a findings exit becomes `SCANNER-ERROR`, never a fabricated `CRITICAL` result.
- Generic external scanners do **not** persist their stdout/stderr at all. A known findings exit produces a category-only message; a failure produces `SCANNER-ERROR`. Full scanner detail is intentionally left for a local/manual rerun.
- Built-in source heuristics report category + path, not the matched credential value.
- `redact()` in `scripts/catalog_security.py` is defense in depth for short exception/diagnostic strings and covers the credential shapes exercised by the test suite, including GitHub/OpenAI/AWS/Google/Stripe/npm/SendGrid/Mailgun/Slack/JWT/Twilio-labelled/basic-auth/private-key examples.
- `deep_scan()` still applies a final masking pass before results leave the lifecycle engine.
- The public Pages artifact carries counts and policy only. `scripts/build_public_site.py` rebuilds it from scratch and **fails the build** if repository names, private notes/findings, or scanner detail reaches the public artifact.

This is intentionally narrower than claiming that no imaginable secret format could ever be printed by any future tool. New scanner integrations must preserve the no-raw-output boundary and add tests for any new credential formats they may surface.

`tests/test_scanner_safety.py` and `.github/workflows/safety-tests.yml` enforce the current contract with real `unittest` assertions. The CI suite also imports the actual `scripts/catalog_guardian.py` entry point so the tests cannot silently exercise an unused helper module.

Run locally after touching scanner code:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/catalog_guardian.py --help
```

## CLEAN vs FINDING vs SCANNER ERROR

A scanner that fails to run tells you nothing about the repository, so Guardian keeps the three outcomes separate:

| Outcome | Prefix | Meaning |
|---|---|---|
| Clean | *(no entry)* | The scanner ran and found nothing. |
| Finding | `HIGH` / `CRITICAL` | The scanner ran and reported something real. |
| Scanner error | `SCANNER-ERROR` | The scanner did not complete. **No conclusion about the repo.** |

Only explicitly configured exit codes become findings. **Unknown scanners fail closed:** a non-zero exit from a scanner without an explicit exit-code policy is `SCANNER-ERROR`, not automatically a finding. This avoids repeating the original ClamAV bug.

ClamAV is the clearest example: exit code `1` means *infected* while exit code `2` means *the scan failed*, commonly because the signature database is unavailable. A missing/uninitialised database reports:

```text
SCANNER-ERROR clamav signature database is missing or not initialised (run freshclam);
malware scanning was skipped and no malware conclusion can be drawn
```

A `SCANNER-ERROR` marks the repository for **rescan**, clears `deep_scanned`, and blocks managed-adoption promotion. It never sets `CRITICAL` and never proposes removal by itself.

## Stage A — metadata only

Before cloning or executing a repo, inspect GitHub metadata:

```bash
gh api repos/OWNER/NAME
```

Check at minimum:

1. `full_name` exactly matches the intended canonical repository or a verified rename.
2. `archived` and `disabled` state.
3. `fork` status and whether the parent should be used instead.
4. `pushed_at` against the 120/270/365 lifecycle policy.
5. `license.spdx_id` and the actual LICENSE/NOTICE files.
6. README/archive/EOL/successor notices.
7. Security advisories and active maintenance signals when the repo will execute code.

A recent `updated_at` value alone is not proof of active code maintenance; stars, issues, metadata changes, or documentation can change it without a source push.

## Stage B — clone and scan

Recommended WSL/Linux workflow:

```bash
mkdir -p /tmp/master-repo-vet
cd /tmp/master-repo-vet
git clone --depth 1 https://github.com/OWNER/NAME.git target

gitleaks detect --source target --no-git --redact --exit-code 0
osv-scanner scan source -r target
semgrep scan --config p/security-audit --config p/secrets --config p/command-injection target
clamscan -r --infected target
```

If installed:

```bash
trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL target
snyk test --all-projects --severity-threshold=high
```

Do not commit live secret material into this repo as “evidence.” For manual scanner runs, redact output before saving it anywhere persistent.

## Stage B2 — manual execution-path review

Static tools do not understand intent. Read the files that can execute automatically:

- `package.json`: `preinstall`, `install`, `postinstall`, `prepare`.
- `setup.py`: `cmdclass`, subprocess/network calls.
- `pyproject.toml`: custom build backends/hooks.
- `install.sh`, PowerShell installers, Makefile install targets.
- Dockerfiles: remote fetch + execute, unpinned artifacts.
- `.github/workflows/*`: `pull_request_target`, untrusted checkouts, event data interpolated into `run:`.
- `.npmrc`, `pip.conf`, registry mirrors.
- MCP manifests and agent instructions that request broad filesystem/network/secrets access.
- Browser automation or financial integrations that can perform real external actions.

For this repository's own `pull_request_target` owner gate, the workflow checks out the trusted default branch only and never checks out or executes PR-head code. The status writer is intentionally minimal (`statuses:write`) and approval is evaluated from GitHub API identity + current head SHA.

## Hidden text and prompt injection

The Guardian treats these as review signals:

- bidi overrides and zero-width control characters in source/instruction files;
- text attempting to override system/developer/user instructions;
- instructions asking an agent to reveal secrets/system prompts;
- instructions that try to disable approval/safety/security gates.

These heuristics can false-positive in security test fixtures or blocklists. Open every finding and read the surrounding context.

## SQL and command injection review

A string containing SQL or a shell command is not automatically unsafe. Distinguish parameterized/structured calls from user-controlled string construction.

**Safer SQL:**

```text
SELECT ... WHERE id = $1
```

with user input passed through a bound parameter.

**Review/unsafe SQL shape:**

```text
"SELECT ... WHERE id = " + user_input
f"SELECT ... WHERE id = {user_input}"
```

**Review/unsafe command shape:**

```text
subprocess.run(request.args["cmd"], shell=True)
```

Guardian/Semgrep findings are evidence for inspection, not an automatic guilty verdict.

## New repo intake rule

Every new catalog repo should receive an immediate deep source scan. The workflow detects newly added `owner/repo` lines in `repo-lists/*.txt` and deep-scans those additions during the same GitHub Actions run.

A new repo is not “trusted because it is in the file.” It becomes usable only after its security/lifecycle/license findings are acceptable.

## Removal and managed adoption

A repo can become a removal candidate because it is deleted, disabled, lifecycle-expired, explicitly sunset, or has a confirmed CRITICAL finding.

Before preserving useful code as a Charles-managed replacement:

1. deep-scan the source;
2. resolve all HIGH/CRITICAL findings;
3. verify license/NOTICE/attribution obligations;
4. identify only the useful components;
5. modernize dependencies, tests, CI, and security controls;
6. re-scan the maintained version;
7. add it back only through an owner-approved PR.

Automation may create a managed-adoption **candidate note**, but it must not silently copy/fork third-party source code.

## Windows

For full scanning, prefer WSL on an ext4 filesystem. Semgrep and Unix security tooling generally work more reliably there than against deep Windows trees under `/mnt/c`.

The Python-only `scripts/static_audit.py` remains useful when external scanners are unavailable, but the owner-approved GitHub workflow is the preferred reproducible scan path.

## Verdict format

Record a concise decision:

```text
REPO: owner/name
VERDICT: PASS | PASS-WITH-NOTE | REVIEW | REJECT | REFERENCE
LICENSE: SPDX/custom status
ACTIVITY: pushed_at + lifecycle status
ARCHIVE/EOL: yes/no + successor if any
FINDINGS: hidden/prompt/sql/command/secrets/malware/dependencies
SCAN COMPLETENESS: all scanners completed | SCANNER-ERROR present (rescan required)
REASON: decisive explanation
```

## Limits

No combination of static scanners can prove third-party software safe. Deliberate backdoors can look like ordinary code, dependency compromise can happen after a prior pass, and a clean source tree can still be dangerous when granted broad credentials or network access.

Use least privilege, pin versions when appropriate, keep secrets scoped, re-audit major version changes, and keep Charles's approval gate in front of catalog removals/adoptions and protected-`main` changes.