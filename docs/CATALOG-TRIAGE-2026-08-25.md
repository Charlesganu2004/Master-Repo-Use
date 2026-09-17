# Catalog triage — 2026-08-25

Resolves the open `[Catalog Audit]` issue (#2). Guardian counts at time of triage:

**Healthy 187 · Stale 27 · Review 16 · Remove 1** across 231 catalogued repositories.

Every claim below was checked against the GitHub API on 2026-08-25, not inferred from the
Guardian note. Where the API contradicted the audit, the API wins and the difference is stated.

---

## 1. Removals (act now)

| Repo | Evidence | Action |
|---|---|---|
| `marcozanetti-dev/intraday-mean-reversion-costs-aware` | `GET /repos/...` → **404**. Repository deleted or made private. | **Remove** from `day-trading-bots.txt` and `all-curated.txt`. |
| `phildougherty/infracost_mcp` | 2 stars, no push for 291d. `infracost/agent-skills` (official, already catalogued) covers the same job. | **Remove**; superseded by a first-party entry already in the catalog. |
| `bradygaster/CustomAgent` | 2 stars, 305d. Conference demo scaffold, not a library. | **Remove**; superseded by `microsoft/agent-framework`. |

## 2. Transfers — slug is wrong, project is fine

| Old slug | New slug | Evidence |
|---|---|---|
| `geekan/MetaGPT` | `FoundationAgents/MetaGPT` | The API redirects `geekan/MetaGPT` → `FoundationAgents/MetaGPT` (70,018 stars). The project moved to an org; the catalog was still pointing at the personal namespace. |

This is the finding the age-based audit could not have made on its own: MetaGPT looked "216d
stale" only because the redirect target was being measured under the old name.

## 3. Supersessions — keep the old entry, point at the successor

### `microsoft/autogen` → `microsoft/agent-framework`

- AutoGen: last release `python-v0.7.5` on **2025-09-30**, last push 2026-04-15.
- Agent Framework: `dotnet-1.19.0` on **2026-08-22**, releasing roughly weekly.
- `agent-framework` is the announced merger of AutoGen and Semantic Kernel.

**Decision:** keep AutoGen as a `superseded` reference entry. Existing AutoGen code is not
broken and needs no emergency migration; new work starts on `agent-framework`. Both are now in
`repo-lists/adk-agent-kits.txt` with the relationship documented in `docs/ADK-GUIDE.md`.

### `coinbase/cdp-sdk-python` → `coinbase/cdp-sdk`

- Python-only repo: 95 stars, no push for 301d.
- `coinbase/cdp-sdk` monorepo: pushed **2026-08-25**.

**Decision:** add `coinbase/cdp-sdk`, mark the Python-only repo `superseded`.

### `FlowiseAI/Flowise` → `langflow-ai/langflow`

This one deserves care because the surface signal is misleading.

**Flowise shipped release 3.1.4 on 2026-07-29 — last month. That is not evidence of life.**
It was the *final sunset release*. The full timeline:

- 2026-07-27 — feature freeze
- 2026-07-29 — `flowise@3.1.4`, the last release
- 2026-08-10 — repository archived (`"archived": true` confirmed via API)
- **2026-08-31 — EOL**, six days after this triage

A recent release is normally a strong freshness signal, and the catalog policy is right to weigh
it. This is the exception: sunset releases look identical to healthy ones from the outside. The
`archived` flag is the tiebreaker, and Guardian read it correctly.

**Decision:** keep Flowise as `archived-active` reference material through EOL, then drop it from
the runtime catalog. Successor for the visual-LLM-flow-builder slot is `langflow-ai/langflow`
(153,669 stars, pushed 2026-08-25). `n8n-io/n8n` and `langgenius/dify` are viable alternatives
if the requirement is broader workflow automation rather than LLM flows specifically.

### `langchain-ai/open_deep_research`

Archived 2026-08-10, but pushed 15 days ago. **Decision:** `reference` override. The technique
is still worth reading; it is not a maintained dependency. `langchain-ai/langgraph` (40,437
stars, active) is where that work continues.

## 4. Reference overrides — quiet by design, not abandoned

These are research artifacts, official course material, or vendor SDKs with genuinely low churn.
Age is the wrong metric for all of them, so each gets a `reference` override so it stops
generating audit noise every week.

| Repo | Age | Why age is the wrong signal |
|---|---:|---|
| `rmurai0610/MASt3R-SLAM` | 289d | Paper-code for a published SLAM method. 3,166 stars. Research artifacts are finished, not stale. |
| `facebookresearch/vjepa2` | 155d | Meta research release. Same reasoning. |
| `rpng/open_vins` | 268d | Mature, widely-cited VIO library. Stability is the feature. |
| `microsoft/lets-learn-mcp-python` | 335d | Official Microsoft *course* material pinned to a teaching moment. |
| `bradygaster/MultiAgent`, `bradygaster/dotnet-cloud-native-build-2023`, `bradygaster/Squad-IRL` | 165–308d | Microsoft dev-advocate conference demos. Point-in-time by construction. Reference only — do not depend on them. |
| `passiv/snaptrade-react` | 281d | Official vendor SDK for a stable API. Low churn is expected. |
| `bukosabino/ta` | 160d | Technical-analysis maths. The formulas do not change. |
| `microsoft/LLMLingua` | 138d | Still the reference prompt-compression implementation with a paper behind it. |

## 5. Genuine stale-watch — no action yet, re-check next audit

Active projects that have simply had a quiet quarter. The 120-day warning is doing exactly what
it was designed to do: flag early without deleting.

`AnswerDotAI/rerankers` (248d) · `upstash/rag-chat` (253d) · `upstash/vector-js` (169d) ·
`qiskit-community/qiskit-finance` (255d) · `jmfernandes/robin_stocks` (195d) ·
`Lumiwealth/lumiwealth-tradier` (232d) · `thammo4/uvatradier` (128d) · `mlabouardy/komiser` (135d) ·
`FlagOpen/RoboBrain2.5` (177d) · `SkyworkAI/Matrix-Game` (148d) · `D-Ogi/WatermarkRemover-AI` (148d) ·
`RoggeOhta/awesome-codex-cli` (136d) · `TradingGoose/TradingGoose.github.io` (124d)

Personal/small research projects in the same bucket, lower confidence of return:
`MrDecryptDecipher/Sentinel` (261d) · `padmarajkore/Ai-crypto-trading-system` (219d) ·
`VarunRathore137/The-Hybrid-Quantum-Portfolio-Optimizer` (216d) · `ebrahimpichka/DeepRL-trade` (193d) ·
`fsaavedra0003/Agentic-AI-Trading-Bot-...` (168d) · `dkorobtsov/pitch-deck` (155d) ·
`VictorVVedtion/trading-skills` (140d) · `aitrados/finance-trading-ai-agents-mcp` (279d)

## 6. Policy observation

The one policy gap this triage exposed: **archived-with-a-recent-release** is a distinct state
that neither "healthy" nor "stale" describes, and it is the state most likely to fool a
freshness check. Flowise and `open_deep_research` both hit it in the same month.

Guardian already handles it via the `archived` flag. The lesson worth keeping is the one in §3:
*a recent release does not imply a maintained project* — check `archived`, and check whether the
release notes announce a sunset.

## 7. Update 2026-09-16: after the #21 audit

Recorded after checking every row of the 2026-09-14 audit (issue #21) against the repository
and against the GitHub API. The rows above are left as written on 2026-08-25.

**Archivals now acknowledged.** `microsoft/lets-learn-mcp-python` (§4 above) and
`qiskit-community/ibm-quantum-challenge-fall-2021` were archived upstream after their decisions
were recorded; the API confirmed `archived: true` for both on 2026-09-16. Both were already
reference-only, which archival does not change, so their overrides now carry
`acknowledged_archived`, as do `Chalarangelo/30-seconds-of-css` and
`langchain-ai/open_deep_research`, whose notes already recorded the archival. Guardian holds an
acknowledged archival HEALTHY; before this, each of the four showed as REVIEW every week.

**Two stale warnings were reference material.** `kk7nc/RMDL` is listed under "Research reference
(read for the ideas; not proposed as a dependency)" in `repo-lists/multi-model-data.txt`, and
`openai/parameter-golf` is a fixed-duration challenge. Both now have `reference` overrides.

**`CartographAI/mcp-server-codegraph` needs an owner decision by 2026-10-04.** MIT, not archived,
last push 2025-10-03. It crosses the 365-day removal threshold on 2026-10-04, after which an
approved maintenance run will propose removing it. No decision has been recorded, and a reference
override would be the wrong tool: it is a runtime MCP server, which is exactly what the threshold
exists for. The catalog already carries a maintained tool for the same job,
`Graphify-Labs/graphify` (`repo-lists/all-curated.txt`), installed locally and wrapped by
`skills/master-graphify`. Removal remains the owner's decision.

**The other five STALE rows need nothing yet.** `HappyHackingSpace/awesome-hackathon`,
`LQF-dev/Zero-code`, `allenai/molmoact`, `skytable/skytable` and
`wangcangshu/codex-desktop-thread-rescue` are 126 to 145 days quiet: warnings, not decisions.
Re-check at the 270-day review. Two more crossed 120 days between the audit and the status
regenerated on 2026-09-17: `tastytrade/tastytrade-api-js` (122d) and
`LottieFiles/motion-design-skill` (121d), in the same position.

Status after these records, regenerated 2026-09-17 00:30 UTC with a metadata pass that removes
nothing: healthy 296, stale 7, review 1 (CartographAI), remove 0, all 304 catalogued repositories
present. The previous `docs/CATALOG-STATUS.md` dated from 2026-08-27 and was missing 11 of them.
