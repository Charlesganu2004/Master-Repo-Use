# PROMPT-ONLY SYNTHETIC verified benchmark suite (private)

Every report and graph carries **PROMPT-ONLY SYNTHETIC**. This is not an
installed full-agent harness comparison. Browser and RTK substudies execute real
local tools on synthetic fixtures; the suite label does not turn those timings
into simulated measurements. No n=1 ranking or statistical significance is claimed.
Displayed tokens and dollar cost are `null` / unavailable under the current
reporting instruction. Historical private provider counters remain unchanged.

The three targeted v2 correction slots can be selected and rescored from
already executed `generation-set-2` trials:

```powershell
python -m benchmarks.verified_2026.correction --evidence $work --output "$work\correction-v2" --python "$work\venv\Scripts\python.exe"
```

This command has no model adapter: it starts zero
generations, freezes the existing v1 rows, verifies source prompt hashes and
one-request controls, and scores the two no-Caveman cells plus the formerly
timed-out super-complex/super slot. The original timeout is never overwritten.

## Scope and claim boundaries

**Coding v1 is ABORTED AND UNCONTROLLED: 28 finalized model requests were
consumed when 12 were authorized. All twelve `control_valid` flags are false.**
Its 12-CLI-invocation ceiling did not
enforce the requested 12-generation ceiling. An empty `--available-tools=`
option exposed default native tools and some cells made several model calls.
Model execution was stopped as soon as the mismatch was discovered.
`execution-audit.json` gives exact observed call-start and finalized usage counts.
The `coding` command now fails closed without contacting a model. Re-enabling
requires a separate audited path and explicit authorization. The later authorized
`generation-set-2` uses `isolated.py`; it does not reopen the legacy command.
Only a complete valid new matrix permits controlled per-trial comparisons.

This suite compares six explicit instruction arms on two synthetic coding tasks,
and separately measures local command-output proxies and browser engines.
Raw evidence is private. Do not copy it to Pages or the public allowlist.

The coding experiment is a **prompt-only operationalization**, not proof that
the installed super-harness hooks run on every client or enforce token ceilings.
The actual private harness is owned and tested separately. No private repository
source, user attachment, credentials, or personal instructions enter model prompts.
The common safety/output instructions in `tasks.py::COMMON` are present even in
the bare arm. Native CLI system instructions still apply to every arm.

Six arms:

1. Bare: common safety and task only.
2. Super: explicit benchmark-authored super-chain instructions.
3. Super plus Ponytail plus Caveman: super-chain and both complete pinned public skills.
4. Super plus Ponytail, Caveman injection removed: the Caveman line removed from
   benchmark context and no Caveman skill injected. Installed definitions are untouched.
5. Ponytail alone: common safety, pinned full public skill, task.
6. Caveman alone: common safety, pinned full public skill, task.

The initial pilot's no-Caveman arm had a line-boundary defect: removing the
Caveman-bearing line also removed the finish-status clause and retained a
safety-only continuation. Its results are a modified-context observation, not
a pure one-variable ablation. Protocol v2 separates those lines and has a guard
test. Original pilot prompts are immutable once a generation ledger exists.
No additional model generations were spent repairing that pilot.

Offline scoring revision v3 can recover a complete JSON object inside a closed
JSON fence following prose in a finalized assistant message. This does not turn
that response into a valid JSON-only response: `response_contract_valid` remains
false. Streaming deltas, incomplete fences, and truncated output are never
treated as completed answers. Original raw responses and executed prompts remain
unchanged; `reevaluation-v3.json` records only a local recheck of saved code.

Do not confuse `reevaluation-v2.json` with `generation-set-2`: the former is
offline rescoring of stored v1 answers; only the latter contains new model calls.
Its rejected wildcard-deny preflight, corrected canary, and subsequent invocations
have separate artifacts. The canary remains the complex/bare matrix cell.

The two exact tasks in `tasks.py::TASKS` require an atomic idempotent ledger and
a concurrent weighted multi-key sliding-window limiter with transactional restore.
The two transfer prompts extend those tasks with reversible holds and
versioned reconfiguration. They are generated verbatim into `prompts/`.

## Reproduce

Use Python 3.12+. Set `$work` to an
isolated session artifact directory, never the source checkout or a shared home
configuration directory. Commands below write only there.

```powershell
$work = Join-Path $env:COPILOT_SESSION_FILES "benchmark-evidence"
python -m benchmarks.verified_2026.audit --output $work --upstreams
python -m benchmarks.verified_2026.run prepare --output $work
python -m unittest discover -s tests -p "test_benchmark*.py" -v
python -m benchmarks.verified_2026.run coding --output $work --max-attempts 12
python -m benchmarks.verified_2026.run reconcile --output $work
```

The `coding` command above intentionally records the blocker and does not invoke
the CLI. `reconcile` rescans existing private evidence and evaluates saved
solutions offline. To evaluate a manually produced synthetic answer:

```powershell
python benchmarks\verified_2026\hidden.py complex "$work\manual\solution.py"
python benchmarks\verified_2026\hidden.py super_complex "$work\manual\solution.py"
```

If `COPILOT_SESSION_FILES` is not defined, set `$work` explicitly to the session's
`files\benchmark-evidence` directory. No global installation, hooks, `rtk init`,
configuration copying, or provider reconfiguration is required.

`audit --archive ZIP --comparison JSON --output $work` optionally inventories
the supplied archival export, selectively recovers only a fixed allowlist of
benchmark evidence/checks, and hashes both the archive and parent comparison.
It never extracts an archive wholesale, executable build outputs, or embedded ZIPs.

The upstream audit is deliberately limited: metadata, licensing and selected
install manifests, not a complete malware or CVE clearance. Unavailable scanner
results are `null`. Evaluate that limitation before enabling third-party binaries.
Ponytail is MIT; Caveman skill licensing is distinct from its BSL engine.
Caveman-browse is source-available BSL-1.1, not MIT; production redistribution
and hosted embedding require separate licensing review. See pinned downloaded
LICENSE files and `upstream-audit.json`, not inferred GitHub license metadata.

Optional engine/lint dependencies are pinned in `requirements.txt`. The original
validation environment lacked these packages. Create a venv inside `$work`,
then install wheels only:

```powershell
python -m venv "$work\venv"
& "$work\venv\Scripts\python.exe" -m pip install --only-binary=:all: -r benchmarks\verified_2026\requirements.txt
python -m benchmarks.verified_2026.binaries --output $work
& "$work\venv\Scripts\python.exe" -m benchmarks.verified_2026.run commands --output $work --rtk "$work\bin\rtk.exe"
& "$work\venv\Scripts\python.exe" -m benchmarks.verified_2026.browser --output $work --chromium $chromium
python -m benchmarks.verified_2026.run report --output $work
```

Set `$chromium` to one existing Chromium executable. Both Python engines receive
that same path and record its hash and runtime version. Do not download separate
browsers for separate arms. An optional `--caveman` points at a separately
verified Go CLI binary; a snapshot-only probe is labeled representation-only
and is **not** substituted for a completed action benchmark.

### Explicitly authorized isolated generation set

This path costs model requests. Obtain authorization first. Use a new directory;
never overwrite a previous set. Keep live super mode unchanged throughout.
The public upstream instruction files must already have passed the intake above.

```powershell
$second = Join-Path $work "generation-set-2"
New-Item -ItemType Directory -Path $second
Copy-Item "$work\upstreams" "$second\upstreams" -Recurse
python -m benchmarks.verified_2026.run prepare --output $second
python -m unittest tests.test_isolated_benchmark -v
python -m benchmarks.verified_2026.isolated --output "$second\controlled-runs" --prompt "$second\prompts\complex\bare.txt" --authorize-one-invocation
```

Stop and inspect `controlled-runs\01-complex-bare\audit.json` before proceeding:
exactly one observed start and finalized request, no tool calls or subagents,
zero **active** MCP servers, and `control_valid: true`. Disabled MCP inventory
entries remain visible rather than being counted as active servers.
The non-empty `--available-tools __benchmark_no_tools__` value is essential.
An empty value exposes default tools. `--deny-tool '*'` is invalid CLI grammar
and is rejected by the regression before spawn; it is not in the corrected vector.
`--help` alone did not validate that rule grammar in the failed preflight.

After reporting and accepting the canary, run the remaining cells once:

```powershell
python -c "import pathlib,shutil,sys; from benchmarks.verified_2026.isolated import remaining; root=pathlib.Path(sys.argv[1]); sys.exit(0 if remaining(root/'controlled-runs',root/'prompts',pathlib.Path(shutil.which('copilot'))) else 1)" $second
python -m benchmarks.verified_2026.run report --output $work
```

The default timeout is 240 seconds per invocation, unchanged from v1 rather than
extended to chase successful samples. No timeout is retried. Unknown or invalid
accounting stops the batch, even with cells remaining. Each invocation has its own
argument vector, event capture and usage file. The ledger includes the canary and
enforces the 16-finalized-request ceiling; a clean 6-by-2 matrix needs only 12.
The CLI model is `claude-sonnet-5`. This is n=1 per task/arm cell; two trials per
arm on different tasks are not statistical significance. Provider caches are not
under experimental control.

### Reviewed export

Raw originals stay in session artifacts. Use an empty export directory:

```powershell
python -m benchmarks.verified_2026.export --source $work --destination "$work\reviewed-export" --zip "$work\reviewed-benchmark-report.zip"
```

The export retains measured numeric fields and flags, redacts local paths, omits
raw CLI transcripts and raw usage objects, and records separate original/export
hashes. Pinned public skill files retain their original bytes. Engine temporary
directories, caches and vendored browser assets are excluded by explicit file
selection. A narrow credential-pattern check is not comprehensive security
clearance. The raw private ZIP is not a public Pages artifact.

## Controls and scoring

Each recorded coding cell used a new working directory and separate HOME, USERPROFILE,
APPDATA, cache/config/data directories, COPILOT_HOME and logs. CLI hooks are
disabled in that isolated config; built-in MCP, custom instructions, automatic
updates, Bash startup scripts and experimental behavior were disabled.
The intended tool disabling did not work, which invalidates the pilot controls.
Only existing GH_TOKEN/GITHUB_TOKEN authentication may be inherited, never
printed or copied to files. Provider-side cache disabling is not exposed.
The default model is not overridden, and unknown actual model identity remains
null. Do not claim that a fresh directory means a cold provider cache.

`generation-ledger.json` records 12 CLI invocations, not model generations.
That distinction was initially missed. Some invocations made multiple calls,
so the requested generation ceiling was exceeded. No judge agents or swarm
were used. No additional generations may be spent trying more models.

Hidden checks run outside the model directory with a 30-second subprocess
timeout. A conservative AST gate rejects non-allowlisted imports, filesystem
builtins and dunder introspection; this prevents common accidental side effects,
but it is **not an adversarial OS sandbox**. Treat generated code as untrusted.
Model-authored tests are preserved as text, not mistaken for passing tests.
Correctness is the proportion of explicit contract test methods passed;
mutant guard tests verify rollback, expiry and partial-write mistakes are caught.
No arbitrary judge score is added. LOC counts nonblank generated solution lines.

Command fixtures execute real local git, Ruff, and unittest success/failure
cases. Exact stdout/stderr bytes are preserved as hex plus readable text,
with separate byte counts, exit codes, and elapsed time. RTK is the canonical
`rtk-ai/rtk` binary, verified against publisher SHA256, never the unrelated
crates.io package. RTK reduces shell output; its built-in `bytes / 4` estimate
is not tokenizer usage or LLM cost. No tokenizer is installed merely to invent
a token metric. See the pinned upstream README in the evidence.

Browser tasks assert lookup, checkout receipt, and exact row count on a
deterministic local HTTP fixture. Python Playwright and Python Rustwright use
their real APIs. Rustwright is alpha and Chromium-only. Process startup and
cold/warm task timing are separate from snapshot representation measurement;
OS page-cache flushing is not performed. Snapshot representations are not
guaranteed semantically equivalent; an inner-text fallback is explicitly labeled.
No cloud browser, model agent loop, or MCP timing is inferred.

## Evidence and report

`report` derives SVG graphs from JSON evidence, prominently labels the coding
pilot invalid, and packages
`private-benchmark-report.zip`: report, graphs, exact prompts, raw evidence,
source and guard tests. Unknown values display as “not measured”, never zero.
Archival completeness gets a separately labeled chart; old coding costs and
medians are never mixed into the fresh pilot.

Report elapsed time, nonblank LOC, deterministic correctness, tool/agent counts,
and correct test cases per second. Input/output tokens, cache usage and actual
cost remain null unless a documented provider/CLI usage field supplies them.
Raw usage remains available for schema review; do not guess rate units.
`reconcile` normalizes the observed CLI `modelMetrics.*.usage` counters,
preserving uncached input, cache read/write and reasoning counts separately.
It records premium-request and nano-AIU units without converting them to USD.
No robust ranking follows from one observation per cell. Every unmet comparison
is named in the report as a blocker, not silently replaced with another tool.
