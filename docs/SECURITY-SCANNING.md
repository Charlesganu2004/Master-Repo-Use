# Security Scanning

The toolchain used to vet every third-party repo in this catalog before it was added. All four
tools are free and require no account. Every repo in [VETTING-REPORT.md](VETTING-REPORT.md) went
through this exact pipeline.

Related:
- [skills/dep-audit](../skills/dep-audit/SKILL.md) — portable version of this procedure for any agent
- [agents/scanner-vault.md](../agents/scanner-vault.md) — the agent that runs it
- [SECURITY.md](SECURITY.md) — repo-level agent injection and MCP scoping

---

## Threat model

You are about to depend on code someone else wrote. In rough order of how often it actually bites:

| Threat | What it looks like | Caught by |
|---|---|---|
| Install-time execution | `postinstall`, `setup.py` hooks, `curl \| bash` in a Makefile | Manual audit (stage B2) |
| Known-vulnerable dependencies | Transitively pulled CVEs | Trivy, OSV-Scanner |
| Typosquat / hijacked name | `owner/name` is not the project you think | Stage A canonical check |
| Abandoned code | No maintainer, no patch when a bug is found | Stage A last-push date |
| Committed secrets | Author's key in git history | Gitleaks, Trivy |
| CI supply-chain holes | `pull_request_target` + untrusted checkout | Manual audit (stage B2) |

The first and last rows matter most and are the ones scanners miss, because they are design
decisions rather than vulnerabilities. They require reading.

---

## The tools

| Tool | Covers | Account needed |
|---|---|---|
| [Gitleaks](https://github.com/gitleaks/gitleaks) | Committed secrets | No |
| [Trivy](https://github.com/aquasecurity/trivy) | Dependency CVEs, secrets, IaC misconfig | No |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Lockfile vulns against OSV.dev | No |
| [Semgrep OSS](https://github.com/semgrep/semgrep) | Code patterns, injection, command exec | No |
| [Snyk](https://github.com/snyk/cli) | SCA, SAST, container, IaC | **Yes** — free tier requires `snyk auth` |

**On Snyk.** It is genuinely good, but its free tier requires creating an account and
authenticating through a browser before the CLI will run. That puts it in a different category
from the four above, which you download and run. Trivy + OSV-Scanner + Semgrep OSS cover the same
dependency-CVE and code-pattern ground with no account. Treat Snyk as optional.

### Install

Download from the official release pages and **verify the checksum**. Every release above ships
a checksums file; a scanner you cannot verify is not a security tool.

```bash
# example: gitleaks
curl -fsSL -o gitleaks.tar.gz \
  https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz
curl -fsSL -o sums.txt \
  https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_checksums.txt
sha256sum -c --ignore-missing sums.txt
tar xzf gitleaks.tar.gz gitleaks
```

Semgrep installs via pip and is best kept in a venv:

```bash
python3 -m venv ~/semgrep-venv
~/semgrep-venv/bin/pip install semgrep
```

On Debian/Ubuntu, a bare `pip install --user` is refused under
[PEP 668](https://peps.python.org/pep-0668/) (externally-managed environment). Use the venv.

### Windows

**Run this pipeline under WSL, not native Windows.** Three things break otherwise:

1. **Semgrep has no native Windows build.**
2. **`Filename too long`** — Windows' 260-character `MAX_PATH` makes `git clone` fail outright on
   repos with deep trees. Several major projects cannot be cloned on Windows without
   `core.longpaths`, and even then tooling downstream misbehaves.
3. **File locking** — Windows Defender and the search indexer hold handles on freshly cloned
   files, so `rm -rf` fails with "Device or resource busy" and leaves broken directories that
   poison the next clone.

Cloning and scanning inside WSL's ext4 filesystem avoids all three, and semgrep runs several
times faster there than over `/mnt/c`.

---

## Stage A — metadata, no code executed

```bash
curl -s -H "Accept: application/vnd.github+json" \
     "https://api.github.com/repos/OWNER/NAME"
```

Check:

- **`full_name` vs what you asked for.** GitHub silently redirects renamed repos, so a 200
  response does not confirm the name. A mismatch is the typosquat signature — reject on it.
- **`archived`, `disabled`**
- **`fork`** — if true, why this fork and not the parent?
- **`pushed_at`** — no commits in ~18 months on a security-relevant dependency is a finding
- **`license.spdx_id`** — `NOASSERTION` means a custom license a human must read
- **README install instructions** — does it tell you to pipe a download into a shell?

Unauthenticated the API allows 60 requests/hour, which is the practical batch limit.

---

## Stage B — clone and scan

```bash
git clone --depth 1 https://github.com/OWNER/NAME.git ./target

gitleaks detect --source ./target --no-git --redact --exit-code 0 \
         --report-format json --report-path gitleaks.json

trivy fs --scanners vuln,secret,misconfig --severity HIGH,CRITICAL \
      --format json --output trivy.json ./target

osv-scanner scan --recursive --format json --output osv.json ./target

semgrep scan --config p/security-audit --config p/secrets --config p/command-injection \
        --json -o semgrep.json --no-git-ignore --timeout 60 --metrics=off ./target

rm -rf ./target
```

Always pass `--redact` to gitleaks. Scanner output containing live secrets must never be
committed anywhere.

---

## Stage B2 — what executes if you use this

Scanners do not flag these, because they are not vulnerabilities. Read them yourself.

| Look at | Why it matters |
|---|---|
| `package.json` → `preinstall`, `install`, `postinstall`, `prepare` | Runs on `npm install`, before you run anything |
| `setup.py` → `cmdclass`, subprocess calls | Runs on `pip install` |
| `pyproject.toml` → custom build backend, build hooks | Same |
| `install.sh`, Makefile install targets | Check for `curl … \| bash` |
| `Dockerfile` → `RUN curl … \| sh`, `ADD <url>` | Unpinned remote fetch into the image |
| `.github/workflows/*` → `pull_request_target` + checkout of PR head | Privileged-context RCE |
| `.github/workflows/*` → `${{ github.event.* }}` inside `run:` | Script injection via PR title or branch name |
| `.npmrc`, `pip.conf` | Registry redirection away from the default index |

---

## Reading the results

Findings are evidence, not verdicts. Large healthy repos routinely produce dozens of hits.

**Usually noise:**
- Secrets in `test/`, `fixtures/`, `examples/` that are obviously dummy values
- CVEs in dev-only or docs-build dependencies
- Semgrep hits inside vendored third-party trees
- Unpinned GitHub Actions in a repo you are not contributing to

**Usually real:**
- Any install-time script fetching from a URL
- A high-entropy secret in application source
- `pull_request_target` combined with untrusted checkout
- A critical CVE in a runtime dependency with no fix available
- Any canonical-name mismatch

Judge each finding against *your* use. A CVE in a code path you never call is not the same as
one in the entry point.

---

## Verdict format

Record every candidate, including rejections — otherwise the same bad candidate gets
re-proposed in six months.

```
REPO:     owner/name
VERDICT:  PASS | PASS-WITH-NOTE | REJECT
LICENSE:  SPDX id, plus non-commercial or copyleft terms
ACTIVITY: last push date
FINDINGS: gitleaks N | trivy N | osv N | semgrep N | install-time hooks N
REASON:   one decisive line
```

Re-audit on major version bumps. A repo that passed at v1.2 is not a repo that passed at v2.0.

---

## Limits

A clean scan is the absence of evidence from four specific tools. It is not proof of safety.
None of this detects a deliberate backdoor written to look like ordinary code, and none of it
substitutes for reading what you are about to install.

## Stage B without installing scanners

`scripts/static_audit.py` runs the four checks that actually gate this catalog, using
only the Python standard library — no gitleaks/Trivy/Semgrep download, no network:

```bash
mkdir -p /tmp/vet && cd /tmp/vet
git clone --depth 1 https://github.com/OWNER/NAME.git OWNER_NAME
python scripts/static_audit.py /tmp/vet
```

| Class | Blocking? | What it catches |
| --- | --- | --- |
| hidden unicode | yes | zero-width, bidi override, Unicode tag chars, soft hyphen in **source** paths |
| unsafe pr_target | yes | `pull_request_target` that checks out `pull_request.head` — runs fork code with write tokens |
| hidden (fixture) | no | the same characters under `tests/`, `fixtures/`, `testdata/` |
| sql injection | no | queries built by concatenation, f-string, or `.format()` |
| fetch-and-exec | no | `curl … \| sh`, `iwr … \| iex` |
| install hooks | no | npm lifecycle, `setup.py`/`pyproject` build hooks |
| malware fixtures | no | paths that look like a shipped malware corpus |

A non-zero count is not a verdict. **Open every finding and read it.** Only the two
blocking classes stop a repo automatically, and even those get a human look.

### Known false-positive shapes

Recorded from real runs so they are not re-litigated each time:

- **Parameterised SQL with a constant interpolated.** `f"SELECT {COLS} FROM t WHERE id = ANY($1)"`
  is safe — user data goes through `$1`. The scanner skips a match when a bound-parameter
  marker (`?`, `$1`, `%s`, `:name`) sits nearby.
- **`U+200D` between emoji.** That is a ZWJ sequence rendering one glyph, not concealment.
  Only counted when neither neighbour is pictographic.
- **Hidden characters in test fixtures.** A repo that ships invisible-character samples is
  usually testing its own detector. Reported in a separate bucket, never blocking.
- **Dangerous strings in blocklists.** `"wget * | sh"` inside a `DANGEROUS_COMMANDS` set is
  a control, not a call. Always read the surrounding lines.
- **`curl … | sh` in README/Dockerfile.** Install documentation, not repo behaviour. What
  matters is whether *your* install path executes it.
- **English prose.** "update", "delete" in a sentence are not SQL. The keyword must be
  followed by real SQL syntax to match.

### Two things that are always checked by hand

1. **Canonical name.** Ask the API for the repo and compare `full_name` to what you typed.
   A mismatch means the project moved org — as `chopratejas/headroom` →
   `headroomlabs-ai/headroom` did. Update the slug. A stale slug is a live supply-chain
   hole: abandoned org names can be re-registered by anyone.
2. **Licence.** `NOASSERTION` means GitHub could not identify one. Read the LICENSE file
   before use; no licence means no permission.
