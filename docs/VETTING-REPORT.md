# Vetting Report

Every candidate repo considered for this catalog, with its security verdict and the reason.
Rejections are recorded so the same candidate is not re-proposed later.

Procedure: [docs/SECURITY-SCANNING.md](SECURITY-SCANNING.md) · Portable version: [skills/dep-audit](../skills/dep-audit/SKILL.md) · Agent: [Vault](../agents/scanner-vault.md)

**Round 1 — 2026-08-05** · Candidates 61 · Accepted 57 · Rejected 4  
**Round 2 — 2026-08-14** · Candidates 9 · Accepted 9 · Rejected 0  
**Round 3 — 2026-08-14** · Candidates 6 · Accepted 6 · Rejected 0 (Codex CLI & portable skills)  
**Catalog total:** 234 repos. Round 1 rejections and the quarantined legacy entry are
recorded below so the same candidates are not re-proposed.

## Method

Two stages, both required. Scanner versions: gitleaks 8.30.1, Trivy 0.73.0, OSV-Scanner 2.4.0, Semgrep OSS 1.172.0.

| Stage | Checks |
| --- | --- |
| A — metadata | canonical-name match (typosquat), archived, fork status, last-push recency, license, README installer |
| B — static scan | shallow clone, then gitleaks (secrets), Trivy (CVE/secret/misconfig), OSV-Scanner (lockfile vulns), Semgrep (code patterns) |
| B2 — run-code audit | npm lifecycle hooks, setup.py/pyproject build hooks, install.sh, Makefile and Dockerfile fetch-and-exec, GitHub Actions `pull_request_target` and script injection, registry redirection |

**Semgrep ruleset disclosure.** Most repos were scanned with `p/security-audit`, `p/secrets` and
`p/command-injection`. Six large repos (`aquasecurity/trivy`, `vllm-project/vllm`,
`sgl-project/sglang`, `unslothai/unsloth`, `BerriAI/litellm`, `NVIDIA-NeMo/Nemotron`) exceeded the
time budget on `p/security-audit` and were re-scanned with `p/secrets` and `p/command-injection`
only. They therefore have narrower code-pattern coverage than the rest. Gitleaks, Trivy,
OSV-Scanner and the run-code audit ran identically for every repo.

Verdicts:

- **PASS** — no blockers, no findings needing judgement
- **PASS-WITH-NOTE** — accepted, but carries something you should know (license terms, install-time hooks, dependency CVEs, quiet maintenance)
- **REJECT** — excluded from the catalog

## Antivirus detections during vetting

Stage B shallow-clones each candidate to disk. On a Windows host with Defender real-time
protection on, that clone is scanned as it lands, and **repos whose test suites contain real
malware samples will be quarantined**. This is the scanner working correctly, not an infection:
the files are inert test fixtures that are never executed by the vetting procedure.

Recorded on 2026-08-05 (Defender, real-time protection, files remediated automatically —
no execution, no persistence, no installed artefact):

| Repo | File | Defender name |
| --- | --- | --- |
| DataDog/guarddog | `tests/analyzer/sourcecode/npm-exfiltrate-sensitive-data.js` | `Trojan:NPM/MiniShaiHrd.ZA!MTB` |
| DataDog/guarddog | `tests/analyzer/sourcecode/threat-runtime-obfuscation-dynamic-eval.js` | `Trojan:Win32/DownNPM.YAB!MTB` |

Both files are guarddog's own detection fixtures — the corpus its Semgrep rules are unit-tested
against. Any malware-detection tool ships something equivalent. Expect the same from
`trufflesecurity/trufflehog`, `semgrep/semgrep` and `NVIDIA/garak` if their fixtures grow.

Do not create antivirus exclusions to make a clone succeed. This catalog excludes repositories
whose fixtures trigger resident antivirus; inspect such repositories only in a disposable,
isolated analysis environment when there is a specific need.

## Rejected (4)

| Repo | Verdict | Reason |
| --- | --- | --- |
| [DataDog/guarddog](https://github.com/DataDog/guarddog) | REJECT | Not malicious — a legitimate Apache-2.0 DataDog supply-chain scanner. Withdrawn on operational grounds: its `tests/analyzer/sourcecode/` corpus contains live malware samples, so cloning it triggers resident antivirus and the working tree gets silently modified by quarantine. See [Antivirus detections during vetting](#antivirus-detections-during-vetting). Equivalent coverage is available from the remaining lane members without the AV interaction. |
| [BerriAI/litellm](https://github.com/BerriAI/litellm) | REJECT | No malware claim. Held out of automatic recommendation because Semgrep scanned zero of 9,385 files, the repo exposes a shell installer, and the remaining scans reported 25 non-test secret-pattern hits plus a critical Trivy finding. Reconsider only after a complete, version-specific review. |
| [NVIDIA-NeMo/Nemotron](https://github.com/NVIDIA-NeMo/Nemotron) | REJECT | No malware claim. The reduced Semgrep ruleset and large unresolved dependency surface (362 Trivy HIGH/CRITICAL findings and 1,258 OSV findings in the captured scan) do not meet this catalog's unattended-install threshold. Reconsider a pinned subcomponent after a scoped review. |
| [unslothai/unsloth](https://github.com/unslothai/unsloth) | REJECT | No malware claim. The run-code audit found remote-evaluation/shell-installer behavior and five install-time hooks. That is too much install-time execution for an automatic recommendation without a version-specific manual review. |

### Quarantined legacy entry (outside the 61-candidate run)

| Repo | Verdict | Reason |
| --- | --- | --- |
| [Compresr-ai/Context-Gateway](https://github.com/Compresr-ai/Context-Gateway) | QUARANTINE | No malware claim and no matching installed artifact was found on this host. Removed from active guidance because the catalog told users to pipe a mutable remote installer directly into a shell for a component positioned between agents and model APIs. It requires a separate source, release, and installer audit before reconsideration. |

## Round 2 — agent tooling (2026-08-14)

**Candidates:** 9 · **Accepted:** 9 · **Rejected:** 0

Stage B ran on [`scripts/static_audit.py`](../scripts/static_audit.py) — standard-library
only, no scanner install. It covers hidden Unicode, SQL injection, fetch-and-exec,
install-time hooks and shipped malware fixtures. Every non-clean result below was opened
and read; the triage is recorded rather than summarised away.

| Repo | Verdict | License | Stars | Last push | Findings triaged |
| --- | --- | --- | --- | --- | --- |
| [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | PASS | Apache-2.0 | 90.7k | 2026-08-14 | SQL all parameterised (`.prepare().run(?,?)`); ZWJ is an emoji sequence in `plugin/modes/law-study.json`; 47 `curl\|bash` are install docs |
| [headroomlabs-ai/headroom](https://github.com/headroomlabs-ai/headroom) | PASS-WITH-NOTE | Apache-2.0 | 66.3k | 2026-08-14 | **moved org** from `chopratejas/headroom` — catalog slug updated; ZWSP at `headroom/learn/analyzer.py:494` breaks up a fenced block inside a docstring; `pull_request_target` checks out `base.sha` |
| [omnigent-ai/omnigent](https://github.com/omnigent-ai/omnigent) | PASS | Apache-2.0 | 8.8k | 2026-08-14 | 12 SQL hits are Alembic DDL migrations with constant table names; hidden Unicode is in two test fixtures; all `pull_request_target` workflows check out base and SHA-pin `actions/checkout` |
| [getomnico/omni](https://github.com/getomnico/omni) | PASS | Apache-2.0 | 758 | 2026-08-09 | `ANY($1)` asyncpg binding — only a module constant is interpolated; ZWSP in a test text corpus |
| [rebelytics/one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all) | PASS | CC-BY-4.0 | 1.8k | 2026-08-14 | fully clean (10 files); CC-BY is a docs licence — attribute if redistributed |
| [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup) | PASS-WITH-NOTE | MIT | 2.6k | 2026-08-01 | **ships invisible-character fixtures on purpose** in `.claude/commands/security/test-examples/` for prompt-injection detection — same class as guarddog, but inert text, no executable payload, so no antivirus interaction |
| [hoangsonww/Claude-Code-Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) | PASS-WITH-NOTE | MIT | 909 | 2026-08-13 | ZWSP in `README-VN.md` (Vietnamese text) and vendored `mermaid.min.js`; npm lifecycle hooks in 3 `package.json` |
| [simple10/agents-observe](https://github.com/simple10/agents-observe) | PASS | MIT | 645 | 2026-07-22 | clean on every check |
| [YeQing17-2026/OmniAgent](https://github.com/YeQing17-2026/OmniAgent) | PASS-WITH-NOTE | NOASSERTION | 2.6k | 2026-07-27 | **licence unidentified — read it before any use.** The `wget * \| sh` hit is an entry in a `DANGEROUS_COMMANDS` blocklist, i.e. a control, not a call |

**False-positive shapes found this round**, now handled in the scanner:

- `f"...{col} FROM t WHERE id = ANY($1)"` — interpolating a *constant* beside a bound
  parameter is safe. The rule now skips a match when a bound-parameter marker is nearby.
- `U+200D` between two pictographic codepoints is an emoji sequence, not concealment.
- Hidden characters under `tests/`, `fixtures/`, `testdata/` are reported separately
  from source hits — a repo testing its own defences is not a repo attacking you.
- English prose containing "update"/"delete" no longer matches; the keyword must be
  followed by real SQL syntax.

## Round 3 — Codex CLI and portable agent skills (2026-08-14)

**Candidates:** 6 · **Accepted:** 6 · **Rejected:** 0 · **Blocking findings:** 0

`SKILL.md` and `AGENTS.md` are portable formats, so these load into Codex, Claude Code,
Gemini CLI and Cursor alike. Vetted with the same gate as round 2.

| Repo | Verdict | License | Stars | Findings triaged |
| --- | --- | --- | --- | --- |
| [openai/codex](https://github.com/openai/codex) | PASS | Apache-2.0 | 106k | 5 fetch-and-exec are install docs (`rustup`, Codex's own installer); `cla.yml` `pull_request_target` checks out base |
| [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | PASS | MIT | 87k | clean on every check |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | PASS | MIT | 30k | clean; index repo, skills live in linked sources — vet each before install |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | PASS | MIT | 24k | `enforce-pr-target.yml` checks out base |
| [NVIDIA/skills](https://github.com/NVIDIA/skills) | PASS-WITH-NOTE | Apache-2.0 | 2.9k | 5 fetch-and-exec inside skill reference docs (`ollama`, `uv` installers) — read the skill before running it |
| [RoggeOhta/awesome-codex-cli](https://github.com/RoggeOhta/awesome-codex-cli) | PASS-WITH-NOTE | CC0-1.0 | 471 | clean, but `slow` — last push 125 days ago; it is an index, so entries need individual vetting |

**Standing caveat for index repos.** `awesome-*` lists and marketplaces pass trivially —
they are two files of links. The gate says nothing about what they point at. Vet each
skill you actually install.

**Held, not rejected** — licence unidentified, so no permission to use:
`aiskillstore/marketplace`, `bradAGI/awesome-cli-coding-agents` (both NOASSERTION).

## Accepted

### 3D Reconstruction & Scene Representation

| Repo | Verdict | License | Last push | Scan summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [ByteDance-Seed/Depth-Anything-3](https://github.com/ByteDance-Seed/Depth-Anything-3) | PASS | Apache-2.0 | 2026-07-27 | gl 0 · tv 0 · osv 40 · sg 5 · hooks 0 | clean |
| [colmap/colmap](https://github.com/colmap/colmap) | PASS-WITH-NOTE | NOASSERTION | 2026-08-05 | gl 0 · tv 0 · osv 64 · sg 16 · hooks 0 | license NOASSERTION - needs manual read |
| [facebookresearch/map-anything](https://github.com/facebookresearch/map-anything) | PASS-WITH-NOTE | Apache-2.0 | 2026-07-17 | gl 1 · tv 0 · osv 0 · sg 19 · hooks 0 | gitleaks: 1 in non-test paths (e.g. data_processing/wai_processing/scripts/conversion/ase.py) |
| [facebookresearch/vggt](https://github.com/facebookresearch/vggt) | PASS-WITH-NOTE | NOASSERTION | 2026-05-19 | gl 0 · tv 1 · osv 142 · sg 0 · hooks 0 | license NOASSERTION - needs manual read; trivy 1 CRITICAL (of 1 HIGH+) |
| [MrNeRF/LichtFeld-Studio](https://github.com/MrNeRF/LichtFeld-Studio) | PASS-WITH-NOTE | GPL-3.0 | 2026-08-05 | gl 5 · tv 33 · osv 72 · sg 5 · hooks 0 | copyleft: GPL-3.0; gitleaks: 5 in non-test paths (e.g. external/OpenMesh/.gitlab-ci.yml); trivy 1 CRITICAL (of 33 HIGH+) |
| [nerfstudio-project/nerfstudio](https://github.com/nerfstudio-project/nerfstudio) | PASS-WITH-NOTE | Apache-2.0 | 2025-07-29 | gl 1 · tv 11 · osv 156 · sg 11 · hooks 0 | quiet: last push 372 days ago; gitleaks: 1 in non-test paths (e.g. nerfstudio/scripts/downloads/download_data.py) |
| [playcanvas/supersplat](https://github.com/playcanvas/supersplat) | PASS | MIT | 2026-08-05 | gl 0 · tv 0 · osv 24 · sg 0 · hooks 0 | clean |

### Spatial Reasoning VLMs & World Models

| Repo | Verdict | License | Last push | Scan summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [allenai/molmoact](https://github.com/allenai/molmoact) | PASS-WITH-NOTE | Apache-2.0 | 2026-05-11 | gl 2 · tv 9 · osv 150 · sg 42 · hooks 0 | gitleaks: 2 in non-test paths (e.g. experiments/libero/run_libero_eval_vllm.py); trivy 1 CRITICAL (of 9 HIGH+) |
| [EvolvingLMMs-Lab/lmms-eval](https://github.com/EvolvingLMMs-Lab/lmms-eval) | PASS-WITH-NOTE | NOASSERTION | 2026-08-03 | gl 3 · tv 10 · osv 492 · sg 44 · hooks 0 | license NOASSERTION - needs manual read; gitleaks: 3 in non-test paths (e.g. lmms_eval/models/simple/gemma3.py); trivy 1 CRITICAL (of 10 HIGH+) |
| [facebookresearch/vjepa2](https://github.com/facebookresearch/vjepa2) | PASS | MIT | 2026-03-23 | gl 0 · tv 0 · osv 28 · sg 0 · hooks 0 | clean |
| [FlagOpen/RoboBrain2.5](https://github.com/FlagOpen/RoboBrain2.5) | PASS-WITH-NOTE | Apache-2.0 | 2026-02-28 | gl 0 · tv 87 · osv 829 · sg 0 · hooks 0 | trivy 4 CRITICAL (of 87 HIGH+) |
| [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos) | PASS-WITH-NOTE | NOASSERTION | 2026-08-05 | gl 1 · tv 12 · osv 418 · sg 147 · hooks 0 | license NOASSERTION - needs manual read; gitleaks: 1 in non-test paths (e.g. evaluation/cosmos3/reasoner/vlmevalkit/vlmeval/api/jt_vl_chat_mini.py); trivy 1 CRITICAL (of 12 HIGH+) |
| [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi) | PASS | Apache-2.0 | 2026-06-16 | gl 0 · tv 119 · osv 483 · sg 0 · hooks 0 | clean |
| [remyxai/VQASynth](https://github.com/remyxai/VQASynth) | PASS | Apache-2.0 | 2026-08-04 | gl 0 · tv 2 · osv 38 · sg 0 · hooks 0 | clean |
| [SkyworkAI/Matrix-Game](https://github.com/SkyworkAI/Matrix-Game) | PASS-WITH-NOTE | MIT | 2026-03-30 | gl 0 · tv 32 · osv 511 · sg 12 · hooks 0 | trivy 2 CRITICAL (of 32 HIGH+) |
| [vision-x-nyu/thinking-in-space](https://github.com/vision-x-nyu/thinking-in-space) | PASS | Apache-2.0 | 2025-08-05 | gl 0 · tv 0 · osv 395 · sg 6 · hooks 0 | clean |
| [wentaoyuan/RoboPoint](https://github.com/wentaoyuan/RoboPoint) | PASS-WITH-NOTE | Apache-2.0 | 2025-07-17 | gl 0 · tv 0 · osv 0 · sg 0 · hooks 0 | quiet: last push 384 days ago |

### AR / Robotics Mapping & SLAM

| Repo | Verdict | License | Last push | Scan summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [borglab/gtsam](https://github.com/borglab/gtsam) | PASS-WITH-NOTE | NOASSERTION | 2026-08-05 | gl 0 · tv 6 · osv 38 · sg 23 · hooks 0 | license NOASSERTION - needs manual read |
| [isl-org/Open3D](https://github.com/isl-org/Open3D) | PASS-WITH-NOTE | NOASSERTION | 2026-08-04 | gl 1 · tv 1 · osv 34 · sg 16 · hooks 0 | license NOASSERTION - needs manual read; gitleaks: 1 in non-test paths (e.g. 3rdparty/glew/src/glewinfo.c); npm lifecycle hooks: 1 |
| [koide3/glim](https://github.com/koide3/glim) | PASS | MIT | 2026-08-04 | gl 0 · tv 0 · osv 0 · sg 0 · hooks 0 | clean |
| [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) | PASS | BSD-2-Clause | 2026-08-05 | gl 0 · tv 0 · osv 0 · sg 1 · hooks 0 | clean |
| [nerfstudio-project/gsplat](https://github.com/nerfstudio-project/gsplat) | PASS | Apache-2.0 | 2026-07-24 | gl 0 · tv 0 · osv 23 · sg 15 · hooks 0 | clean |
| [nvidia-isaac/nvblox](https://github.com/nvidia-isaac/nvblox) | PASS-WITH-NOTE | NOASSERTION | 2026-07-03 | gl 0 · tv 0 · osv 181 · sg 8 · hooks 0 | license NOASSERTION - needs manual read |
| [rerun-io/rerun](https://github.com/rerun-io/rerun) | PASS | Apache-2.0 | 2026-08-05 | gl 0 · tv 2 · osv 328 · sg 67 · hooks 0 | clean |
| [rmurai0610/MASt3R-SLAM](https://github.com/rmurai0610/MASt3R-SLAM) | PASS-WITH-NOTE | NOASSERTION | 2025-11-09 | gl 0 · tv 0 · osv 115 · sg 28 · hooks 0 | license NOASSERTION - needs manual read |
| [rpng/open_vins](https://github.com/rpng/open_vins) | PASS-WITH-NOTE | GPL-3.0 | 2025-11-30 | gl 1 · tv 0 · osv 0 · sg 2 · hooks 0 | copyleft: GPL-3.0; gitleaks: 1 in non-test paths (e.g. config/rpng_ironsides/mask_ironsides0.xcf) |
| [stella-cv/stella_vslam](https://github.com/stella-cv/stella_vslam) | PASS-WITH-NOTE | NOASSERTION | 2026-02-15 | gl 2 · tv 0 · osv 0 · sg 0 · hooks 0 | license NOASSERTION - needs manual read; gitleaks: 2 in non-test paths (e.g. src/stella_vslam/solve/fundamental_solver.cc) |

### Live / Streaming RAG

| Repo | Verdict | License | Last push | Scan summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [AnswerDotAI/rerankers](https://github.com/AnswerDotAI/rerankers) | PASS | Apache-2.0 | 2025-12-20 | gl 0 · tv 0 · osv 0 · sg 0 · hooks 0 | clean |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 3 · tv 49 · osv 586 · sg 8 · hooks 1 | gitleaks: 3 in non-test paths (e.g. deepeval/telemetry/client.py); install-time execution: npm-lifecycle (docs/package.json) |
| [getzep/graphiti](https://github.com/getzep/graphiti) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 1 · tv 44 · osv 137 · sg 4 · hooks 1 | gitleaks: 1 in non-test paths (e.g. graphiti_core/telemetry/telemetry.py); CI uses pull_request_target but hardened correctly (read-only token, no secrets, no PR code executed) [verified] |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 9 · tv 46 · osv 413 · sg 78 · hooks 0 | gitleaks: 9 in non-test paths (e.g. common/data_source/box_connector.py) |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | PASS | MIT | 2026-08-05 | gl 0 · tv 0 · osv 5 · sg 0 · hooks 0 | clean |
| [lightonai/pylate](https://github.com/lightonai/pylate) | PASS | MIT | 2026-07-23 | gl 0 · tv 0 · osv 0 · sg 22 · hooks 0 | clean |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | PASS-WITH-NOTE | NOASSERTION | 2026-08-05 | gl 3 · tv 27 · osv 125 · sg 48 · hooks 2 | license NOASSERTION - needs manual read; gitleaks: 3 in non-test paths (e.g. .github/workflows/pr-playwright-tests.yml); install-time execution: npm-lifecycle,shell-installer (mobile/package.json); npm lifecycle hooks: 2 |
| [paradedb/paradedb](https://github.com/paradedb/paradedb) | PASS-WITH-NOTE | AGPL-3.0 | 2026-08-05 | gl 0 · tv 0 · osv 9 · sg 51 · hooks 0 | copyleft: AGPL-3.0 |
| [pathwaycom/pathway](https://github.com/pathwaycom/pathway) | PASS-WITH-NOTE | NOASSERTION | 2026-08-05 | gl 0 · tv 7 · osv 994 · sg 14 · hooks 0 | license NOASSERTION - needs manual read |
| [vespa-engine/vespa](https://github.com/vespa-engine/vespa) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 6 · tv 0 · osv 42 · sg 27 · hooks 0 | gitleaks: 6 in non-test paths (e.g. client/go/internal/vespa/deploy_test.go); npm lifecycle hooks: 1 |

### Open-Weight LLMs & Serving

| Repo | Verdict | License | Last push | Scan summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | PASS-WITH-NOTE | MIT | 2026-07-13 | gl 1 · tv 0 · osv 0 · sg 20 · hooks 0 | gitleaks: 1 in non-test paths (e.g. lm_eval/models/megatron_lm.py) |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | PASS-WITH-NOTE | MIT | 2026-08-05 | gl 1 · tv 4 · osv 1240 · sg 16 · hooks 0 | gitleaks: 1 in non-test paths (e.g. tools/server/README.md); npm lifecycle hooks: 1 |
| [QwenLM/Qwen3.6](https://github.com/QwenLM/Qwen3.6) | PASS | Apache-2.0 | 2026-06-03 | gl 0 · tv 0 · osv 0 · sg 0 · hooks 0 | clean |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 9 · tv 14 · osv 8 · sg 381 · hooks 0 | gitleaks: 9 in non-test paths (e.g. .github/workflows/pr-test-sgl-router.yml); trivy 2 CRITICAL (of 14 HIGH+) |
| [vllm-project/llm-compressor](https://github.com/vllm-project/llm-compressor) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 1 · tv 0 · osv 0 · sg 5 · hooks 0 | gitleaks: 1 in non-test paths (e.g. src/llmcompressor/modeling/deepseekv32/model.py) |
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 20 · tv 2 · osv 33 · sg 64 · hooks 0 | gitleaks: 20 in non-test paths (e.g. .buildkite/test_areas/fault_tolerance.yaml) |
| [zai-org/GLM-5](https://github.com/zai-org/GLM-5) | PASS | Apache-2.0 | 2026-07-15 | gl 0 · tv 0 · osv 10 · sg 0 · hooks 0 | clean |

### Security Scanning Tools

| Repo | Verdict | License | Last push | Scan summary | Notes |
| --- | --- | --- | --- | --- | --- |
| [anchore/syft](https://github.com/anchore/syft) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 1 · tv 0 · osv 942 · sg 14 · hooks 0 | gitleaks: 1 in non-test paths (e.g. internal/spdxlicense/generate/testdata/licenses.json); npm lifecycle hooks: 1 |
| [aquasecurity/trivy](https://github.com/aquasecurity/trivy) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 15 · tv 0 · osv 1188 · sg 12 · hooks 1 | gitleaks: 15 in non-test paths (e.g. .github/actions/trivy-triage/config.json); install-time execution: shell-installer (contrib/install.sh) |
| [bridgecrewio/checkov](https://github.com/bridgecrewio/checkov) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-02 | gl 1 · tv 0 · osv 423 · sg 7 · hooks 0 | gitleaks: 1 in non-test paths (e.g. integration_tests/run_integration_tests.sh) |
| [cisco-ai-defense/mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 5 · tv 19 · osv 116 · sg 37 · hooks 0 | gitleaks: 5 in non-test paths (e.g. evals/remote/benign/azure_tools.py) |
| [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks) | PASS-WITH-NOTE | MIT | 2026-07-29 | gl 2 · tv 11 · osv 35 · sg 34 · hooks 0 | self-match against its own rule fixtures [verified] |
| [google/osv-scanner](https://github.com/google/osv-scanner) | PASS | Apache-2.0 | 2026-08-05 | gl 0 · tv 0 · osv 6 · sg 39 · hooks 0 | clean |
| [NVIDIA/garak](https://github.com/NVIDIA/garak) | PASS | Apache-2.0 | 2026-08-04 | gl 0 · tv 0 · osv 105 · sg 2 · hooks 0 | clean |
| [opengrep/opengrep](https://github.com/opengrep/opengrep) | PASS | LGPL-2.1 | 2026-08-05 | gl 0 · tv 0 · osv 1903 · sg 7 · hooks 0 | clean |
| [ossf/scorecard](https://github.com/ossf/scorecard) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-05 | gl 0 · tv 40 · osv 143 · sg 51 · hooks 1 | scanner test fixtures contain deliberately vulnerable workflow samples by design [verified] |
| [semgrep/semgrep](https://github.com/semgrep/semgrep) | PASS-WITH-NOTE | LGPL-2.1 | 2026-08-05 | gl 4 · tv 0 · osv 2477 · sg 3 · hooks 0 | gitleaks hits are rule test fixtures [verified] |
| [sigstore/cosign](https://github.com/sigstore/cosign) | PASS-WITH-NOTE | Apache-2.0 | 2026-08-03 | gl 22 · tv 2 · osv 5 · sg 0 · hooks 0 | gitleaks hits are signing test fixtures, inherent to a signing tool [verified] |
| [snyk/cli](https://github.com/snyk/cli) | PASS-WITH-NOTE | NOASSERTION | 2026-08-05 | gl 0 · tv 0 · osv 6068 · sg 14 · hooks 4 | license NOASSERTION - needs manual read; install-time execution: make-pipe-exec,npm-lifecycle (cliv2/Makefile); npm lifecycle hooks: 3 |
| [trufflesecurity/trufflehog](https://github.com/trufflesecurity/trufflehog) | PASS-WITH-NOTE | AGPL-3.0 | 2026-08-05 | gl 25 · tv 5 · osv 22 · sg 11 · hooks 1 | copyleft: AGPL-3.0; install-time execution: shell-installer (scripts/install.sh); gitleaks hits are detector example credentials, inherent to a secret-scanning tool [verified] |

## Coverage gap that caused rejection

The repository below completed Stage A and the rest of Stage B, but **Semgrep returned zero scanned files** — its per-file timeout was exceeded on a large tree. Secrets, dependency CVEs, and the run-code audit still ran; the missing code-pattern layer is why it is rejected rather than accepted with a note.

| Repo | Files in repo | Semgrep files scanned |
| --- | --- | --- |
| `BerriAI/litellm` | 9385 | 0 |

## Reading the scan summary

`gl` gitleaks secrets outside test/example paths · `tv` Trivy HIGH+CRITICAL · `osv` OSV-Scanner lockfile vulns · `sg` Semgrep ERROR+WARNING · `hooks` code that executes at install or build time

Non-zero counts are not disqualifying on their own. Large actively-developed repos routinely carry transitive CVEs in dev and example dependencies. What matters is whether a finding sits in a path you will actually execute. Counts are recorded so the judgement is auditable rather than implied.

## Limits

A clean scan is the absence of evidence from four tools, not proof of safety. None of this detects a deliberate backdoor written to look like ordinary code. Re-audit on major version bumps — a repo that passed at one version is not a repo that passed at the next.

## Addendum — replacements for removed repos (2026-08-06)

Two repos removed as unmaintained had maintained successors. Both were vetted before
being added. GitHub's REST API was rate-limited at the time, so Stage A metadata was
confirmed directly from the repository page and raw `LICENSE` instead — the checks
performed are the same, only the source differs.

| Repo | Replaces | License | Last push | Archived | Canonical name | Scan summary |
| --- | --- | --- | --- | --- | --- | --- |
| [alpacahq/alpaca-py](https://github.com/alpacahq/alpaca-py) | `alpacahq/alpaca-trade-api-python` | Apache-2.0 | 2026-08-04 | no | matches | gl 11 · tv 2 · osv 55 · sg 5 · hooks 1 |
| [ib-api-reloaded/ib_async](https://github.com/ib-api-reloaded/ib_async) | `erdewit/ib_insync` | BSD-2-Clause | 2025-12-06 | no | matches | gl 0 · tv 0 · osv 0 · sg 7 · hooks 0 |

`ib_async` is the community continuation of `ib_insync`, which stopped after its author's
death. Confirm the fork's provenance yourself before depending on it — a successor fork is
exactly the shape a supply-chain attack imitates, and "the community moved here" is a claim
worth checking rather than assuming.
