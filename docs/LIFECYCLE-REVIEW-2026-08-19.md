# Lifecycle Review — 2026-08-19

This review covers the repositories previously flagged as archived or stale by the Master Repo health report. It distinguishes **GitHub page activity (`updated_at`)** from **actual code pushes (`pushed_at`)**. Stars, issues, metadata, and other activity can change `updated_at` even when source code has not been pushed.

## Policy used

- 0–120 days since last push: healthy from a freshness perspective.
- 121–269 days: stale warning.
- 270–365 days: replacement/managed-adoption review.
- >365 days: remove from the active/runtime catalog unless a stability/reference exception applies.
- Archived is a **review signal**, not an automatic delete signal.
- Explicit upstream sunset/deprecation/support statements override raw recency.
- Static research/challenge/survey repositories can remain as reference-only artifacts when quietness is expected.

## Decisions

| Repository | Current evidence checked | Decision | Master Repo action |
|---|---|---|---|
| `FlowiseAI/Flowise` | Archived; recent 3.1.4 release line and recent 2026-08 code activity, but upstream explicitly says Flowise is archived and points to its future/sunset transition. | **REFERENCE / TRANSITION** | Keep temporarily with `archived-active` override. Do not recommend as a new long-lived production dependency. Added managed-adoption candidate for owner review. |
| `qiskit-community/qiskit-optimization` | Archived, last push 2026-07-12. Upstream README says IBM no longer supports Qiskit Optimization and points users to `Qiskit/qiskit-addon-opt-mapper`. | **REPLACE** | Removed from active catalog and replaced by `Qiskit/qiskit-addon-opt-mapper`. |
| `tastytrade/tastytrade-sdk-python` | Archived, last push 2026-03-13. README explicitly says the project is archived and directs users to the tastytrade SDK page for alternatives. | **REPLACE** | Removed from active broker list. `tastyware/tastytrade` remains as an active **unofficial** Python SDK alternative and was pushed 2026-08-07. |
| `YuhaoLin2005/compact-counter-concept` | Archived but recently pushed in 2026; MIT research/measurement utility about Claude context compaction. | **REFERENCE** | Keep with a `reference` override. Do not treat it as an actively maintained runtime dependency. |
| `ZongqianLi/Prompt-Compression-Survey` | Not archived; last source push 2025-05-18. It is the repository for a NAACL 2025 survey and GitHub reports no repository license. | **REFERENCE** | Keep as a static academic reference via lifecycle override. Do not fork/copy content into a managed repo without permission/license clarity. |
| `aarora79/aws-cost-explorer-mcp-server` | Not archived; last push 2025-04-14. | **REPLACE** | Removed from active catalog. `awslabs/mcp` is actively maintained and contains an AWS billing/cost-management MCP server, making it the preferred replacement. |
| `alexgolec/schwab-py` | Not archived; last push 2025-08-04. | **REPLACE** | Removed from active broker list because `tylerebowers/Schwabdev` covers the same Schwab API lane and was pushed 2026-08-11. |
| `financial-datasets/mcp-server` | Not archived; last source push 2025-06-05, although repository page metadata continued changing in 2026. MIT licensed and still conceptually useful. | **MANAGED-ADOPTION REVIEW** | Removed from active runtime list under the >365d rule. Added `managed-repos/candidates/financial-datasets__mcp-server.md` for possible modernization after owner approval. |
| `nerfstudio-project/nerfstudio` | Not archived; last source push 2025-07-29. Apache-2.0 and still highly useful, but source inactivity crossed the active-runtime threshold. | **MANAGED-ADOPTION REVIEW / REPLACE** | Removed from active 3D runtime list; added managed-adoption candidate. The active lane retains newer maintained tooling including `MrNeRF/LichtFeld-Studio` and `nerfstudio-project/gsplat`. |
| `oyi77/Crypto-RL-Trading-Bot` | Not archived; last push 2025-04-08; no detected repository license. Small experimental trading bot. | **REMOVE** | Removed from active catalog. No managed adoption because no license was detected; copying/forking is not appropriate without permission. |
| `qiskit-community/ibm-quantum-challenge-fall-2021` | Not archived; last push 2025-02-14. This is explicitly a historical 2021 IBM Quantum Challenge artifact, Apache-2.0. | **REFERENCE** | Keep as historical/educational reference through a lifecycle override, not as an active dependency. |
| `vision-x-nyu/thinking-in-space` | Not archived; last push 2025-08-05. Official VSI-Bench research/evaluation implementation, Apache-2.0. | **REFERENCE** | Keep as a research/evaluation artifact through a lifecycle override. Re-evaluate if a newer official VSI-Bench implementation supersedes it. |
| `wentaoyuan/RoboPoint` | Not archived; last push 2025-07-17. Research artifact for spatial affordance prediction, Apache-2.0. | **REFERENCE** | Keep as a research artifact through a lifecycle override. Do not classify paper-code quietness the same as an abandoned production package. |

## Important Flowise conclusion

The recent `flowise@3.1.4` release does **not** mean the repository should be classified as normally healthy. The correct classification is **recent final/transition activity plus an explicit upstream sunset/archive signal**. The Master Repo therefore preserves it as transition/reference material and creates a managed-adoption candidate instead of deleting it immediately or pretending the upstream will continue normally.

## Replacements added/retained

- `Qiskit/qiskit-addon-opt-mapper` — supported replacement path for Qiskit optimization mapping.
- `awslabs/mcp` — active AWS MCP monorepo with billing/cost-management tooling.
- `tylerebowers/Schwabdev` — active Schwab API wrapper.
- `tastyware/tastytrade` — active unofficial typed async Python Tastytrade SDK; verify against Tastytrade's current official SDK guidance before production use.
- `MrNeRF/LichtFeld-Studio` / `nerfstudio-project/gsplat` — active 3D/Gaussian-splatting lane while unique Nerfstudio functionality is evaluated for managed maintenance.

## Managed candidates created

- `managed-repos/candidates/FlowiseAI__Flowise.md`
- `managed-repos/candidates/financial-datasets__mcp-server.md`
- `managed-repos/candidates/nerfstudio-project__nerfstudio.md`

Managed candidates are plans only. They do not copy third-party source or create forks. Charles must approve scope and licensing before a maintained repository is created.

## Next review behavior

Routine follow-up now uses the GitHub-first `Catalog Guardian` workflow. It performs lightweight metadata audits weekly and on relevant catalog/security changes without calling GPT, Claude, Copilot, or Codex. If attention is needed, it creates or refreshes one `[Catalog Audit]` issue.

Charles must comment the exact phrase `APPROVE CATALOG MAINTENANCE` before the deeper deterministic scan/removal/adoption proposal runs. That approved run creates or updates an automation branch and PR; it never merges `main` automatically.

`scripts/maintenance_request.py` remains available only for the separate optional path when deterministic tooling leaves a modernization/adoption decision that genuinely needs model judgment. That AI-assisted path requires the separate `APPROVE AI MAINTENANCE` approval.

## Update 2026-09-16

`qiskit-community/ibm-quantum-challenge-fall-2021`: the evidence column above says "Not archived".
It has since been archived upstream (GitHub API, confirmed 2026-09-16). The REFERENCE decision
stands, since a historical challenge artifact was already static, and the override now records
`acknowledged_archived`. See `docs/CATALOG-TRIAGE-2026-08-25.md` §7.
