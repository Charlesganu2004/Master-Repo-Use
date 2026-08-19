# Security Scanning and Third-Party Repo Intake

This is the security gate for repositories in `Charlesganu2004/Master-Repo-Use`.

The goal is not to claim that static scanning can prove a repository safe. The goal is to catch common supply-chain, injection, malware, secret, lifecycle, and maintenance risks **before** a repo is trusted or executed.

Related files:

- `scripts/catalog_guardian.py` — automated metadata + source guardian
- `.github/workflows/catalog-guardian.yml` — GitHub Pro audit and owner-approval workflow
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

Always redact secret-scanner output before storing logs. Do not commit live secret material into this repo as “evidence.”

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

## Hidden text and prompt injection

The Guardian treats these as review signals:

- bidi overrides and zero-width control characters in source/instruction files;
- text attempting to override system/developer/user instructions;
- instructions asking an agent to reveal secrets/system prompts;
- instructions that try to disable approval/safety/security gates.

These heuristics can false-positive in security test fixtures or blocklists. Open every finding and read the surrounding context.

## SQL injection review

A string containing SQL is not automatically unsafe. Distinguish:

**Safer:**

```text
SELECT ... WHERE id = $1
```

with user input passed through a bound parameter.

**Review/unsafe shape:**

```text
"SELECT ... WHERE id = " + user_input
f"SELECT ... WHERE id = {user_input}"
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
REASON: decisive explanation
```

## Limits

No combination of static scanners can prove third-party software safe. Deliberate backdoors can look like ordinary code, dependency compromise can happen after a prior pass, and a clean source tree can still be dangerous when granted broad credentials or network access.

Use least privilege, pin versions when appropriate, keep secrets scoped, re-audit major version changes, and keep Charles's approval gate in front of catalog removals/adoptions and protected-`main` changes.
