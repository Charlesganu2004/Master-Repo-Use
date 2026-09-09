---
name: dep-audit
description: Use before adding any third-party repo, package, or MCP server to a project - runs a two-stage supply-chain check covering metadata, secrets, known CVEs, code patterns, and anything that executes at install or build time. Free tools only, no account required.
---

# Dependency & Repo Audit

## What this is for

You are about to depend on code someone else wrote. This is the check that runs first.

The realistic threats, in rough order of how often they actually bite:

1. **Install-time execution** — `postinstall` scripts, `setup.py` build hooks, `Makefile`
   targets that pipe a download into a shell. Code that runs before you have run anything.
2. **Known-vulnerable dependencies** — transitively pulled CVEs
3. **Typosquats and hijacked names** — a repo that is not the project you think it is
4. **Abandoned code** — no maintainer means no patch when something is found
5. **Committed secrets** — the author's key in git history, now yours to rotate
6. **CI supply-chain holes** — `pull_request_target` with untrusted checkout

## The toolchain — all free, no account

| Tool | Covers | Install |
|---|---|---|
| [gitleaks](https://github.com/gitleaks/gitleaks) | Committed secrets | Single binary, GitHub releases |
| [Trivy](https://github.com/aquasecurity/trivy) | Dependency CVEs, secrets, IaC misconfig | Single binary, GitHub releases |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Lockfile vulns against OSV.dev | Single binary, GitHub releases |
| [Semgrep OSS](https://github.com/semgrep/semgrep) | Code patterns, injection, command exec | `pip install semgrep` |

Verify the checksum on any binary you download from a release page.

**On Snyk:** the free tier requires a Snyk account and `snyk auth` before it will run. It is
genuinely useful, but it is not in the same "download and run" category as the four above.
Trivy + OSV-Scanner + Semgrep OSS cover the same dependency-CVE and code-pattern ground with
no account. Treat Snyk as optional.

**Platform note:** Semgrep has no native Windows build. On Windows, run it under WSL.

## Stage A — metadata, no code executed

Answer these before cloning anything:

- **Is this the canonical upstream?** Compare the path you were given with what the API
  reports as `full_name`. GitHub silently redirects renamed repos — a 200 does not mean
  you have the right name. Watch for lookalike orgs.
- **Is it a fork?** If so, why are you using the fork rather than the parent?
- **Archived or disabled?**
- **When was the last push?** No commits in ~18 months on a security-relevant dependency
  is a finding, not a footnote.
- **What is the license?** Note non-commercial and copyleft terms explicitly. `NOASSERTION`
  means a custom license someone has to actually read.
- **Does the README tell you to pipe a download into a shell?**

## Stage B — clone and scan

```bash
git clone --depth 1 https://github.com/OWNER/NAME.git ./target

gitleaks detect --source ./target --no-git --redact --exit-code 0
trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL ./target
osv-scanner scan --recursive ./target
semgrep scan --config p/security-audit --config p/secrets --config p/command-injection ./target
```

## Stage B, part 2 — what executes if you use this

Scanners miss this because it is not a vulnerability, it is a design decision. Read it yourself.

| Look at | Why |
|---|---|
| `package.json` → `preinstall`, `install`, `postinstall`, `prepare` | Runs on `npm install`, before you run anything |
| `setup.py` → `cmdclass`, subprocess calls | Runs on `pip install` |
| `pyproject.toml` → custom build backend, build hooks | Same |
| `install.sh`, `Makefile` install targets | Check for `curl … \| bash` |
| `Dockerfile` → `RUN curl … \| sh`, `ADD <url>` | Unpinned remote fetch into the image |
| `.github/workflows/*` → `pull_request_target` + checkout of PR head | Privileged-context RCE; a classic |
| `.github/workflows/*` → `${{ github.event.* }}` inside `run:` | Script injection via PR title/branch name |
| `.npmrc`, `pip.conf` | Registry redirection to a non-default index |

## Reading the results

Findings are evidence, not verdicts. Most repos produce noise.

**Usually noise:**
- Secrets in `test/`, `fixtures/`, `examples/` that are obviously dummy values
- CVEs in dev-only or docs-build dependencies
- Semgrep hits inside vendored third-party trees
- Unpinned GitHub Actions in a repo you are not contributing to

**Usually real:**
- Any install-time script fetching from a URL
- A high-entropy secret in application source
- `pull_request_target` + untrusted checkout
- Critical CVE in a runtime dependency with no fix available
- Anything in a repo whose canonical name does not match what you were given

Judge each finding by whether it affects *your* use. A CVE in a code path you never call is
different from one in the entry point.

## Verdict format

Record every candidate — the rejections are the valuable part, because otherwise someone
re-proposes the same repo in six months.

```
REPO:     owner/name
VERDICT:  PASS | PASS-WITH-NOTE | REJECT
LICENSE:  SPDX id, plus any non-commercial or copyleft terms
ACTIVITY: last push date
FINDINGS: gitleaks N | trivy N | osv N | semgrep N | install-time hooks N
REASON:   one line, decisive
```

Re-audit on version bumps. A repo that passed at v1.2 is not a repo that passed at v2.0 —
maintainers change, and so does what runs at install time.

## Hard limits

- Scanning a repo is not authorisation to attack anything it points at
- Never commit scanner output containing unredacted secrets — `gitleaks --redact`
- A clean scan is not proof of safety; it is absence of evidence from four specific tools
