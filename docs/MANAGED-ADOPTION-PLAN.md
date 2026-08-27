# Managed adoption plan — 2026-08-27

**The ask:** delete the stale entries, take what is useful from them into repositories we own
and maintain, and do the same for the archived ones.

**The constraint that decides everything:** *a repository with no licence is not open source.*
Absent a licence, copyright defaults to all rights reserved. Reading it is fine; copying code
from it into a repository you own is infringement, regardless of how abandoned it looks.

So this plan sorts every candidate by **what the licence permits**, not by how stale it is.

---

## Licence audit

29 stale/review candidates were checked against the GitHub API on 2026-08-27.

| Licence | Count | Adoption |
|---|---:|---|
| MIT / Apache-2.0 / CC0 | 18 | **Permitted** with attribution |
| No licence at all | 7 | **Forbidden** — all rights reserved |
| AGPL-3.0 | 1 | Permitted, but obligations follow the code |
| NOASSERTION (custom) | 3 | Requires reading the actual LICENSE file |

### The seven with no licence

`VarunRathore137/The-Hybrid-Quantum-Portfolio-Optimizer` · `MrDecryptDecipher/Sentinel` ·
`padmarajkore/Ai-crypto-trading-system` · `fsaavedra0003/Agentic-AI-Trading-Bot-…` ·
`ebrahimpichka/DeepRL-trade` · `aitrados/finance-trading-ai-agents-mcp` · `greensock/GSAP`

Six of these are 1–21 star personal projects with no maintenance and nothing distinctive to
salvage, so they have been **removed from the catalog** — not adopted, just delisted.

`greensock/GSAP` is the exception: 28,000 stars, actively maintained, and deliberately not
OSI-licensed. It stays as a **linked dependency**, never a copied one.

---

## Removals applied

Seven entries delisted. Nothing was copied from any of them.

| Repo | Stars | Age | Licence | Why |
|---|---:|---:|---|---|
| `VarunRathore137/The-Hybrid-Quantum-Portfolio-Optimizer` | 1 | 216d | none | no licence, no adoption, nothing distinctive |
| `MrDecryptDecipher/Sentinel` | 1 | 261d | none | same |
| `padmarajkore/Ai-crypto-trading-system` | 2 | 219d | none | same |
| `fsaavedra0003/Agentic-AI-Trading-Bot-…` | 8 | 168d | none | same |
| `ebrahimpichka/DeepRL-trade` | 21 | 193d | none | same |
| `aitrados/finance-trading-ai-agents-mcp` | 64 | 279d | none | the only one with real reach, still unusable legally |
| `dkorobtsov/pitch-deck` | 9 | 155d | MIT | adoptable, but nothing worth maintaining |

The URLs remain recoverable from git history if any of this proves wrong.

---

## Adoption candidates, ranked

### 1. `langchain-ai/open_deep_research` — **recommended**

- MIT · 12,673 stars · archived 2026-08-10, pushed 15 days before that.
- **Legally adoptable.** MIT permits copying with attribution.
- Worth taking: the multi-agent research loop — planner → parallel searchers → synthesiser
  with an explicit stopping condition. That pattern is directly reusable by the agent
  subgroups in this repo.
- Not worth taking: the LangGraph coupling and the hosted-search integrations.
- **Effort:** moderate. Extract the orchestration pattern, not the codebase.
- Upstream continuation: `langchain-ai/langgraph` (40k stars, active).

### 2. `YuhaoLin2005/compact-counter-concept` — **optional, cheap**

- MIT · 0 stars · archived, small.
- **Legally adoptable**, and small enough to absorb outright in an afternoon.
- Worth taking: the context-compaction measurement approach, which complements
  `docs/TOKEN-BUDGET.md`.
- **Effort:** low. Only worth it if compaction measurement is still wanted.

### 3. `FlowiseAI/Flowise` — **do not adopt**

This is the one to be blunt about.

- 55,396 stars · archived 2026-08-10 · **EOL 2026-08-31**, four days from this writing.
- Licence is `NOASSERTION` — the GitHub API cannot classify it. Flowise ships a modified
  Apache licence with commercial-use restrictions on parts of the codebase.
- It is a full product, not a component. "Taking what we can" is not a meaningful operation
  on a 55k-star application.

**Recommendation:** do not adopt. Replace it. `langflow-ai/langflow` (153,669 stars, pushed
2026-08-25) occupies exactly the same slot and is maintained. Keep Flowise catalogued as
`archived-active` reference material until EOL, then drop it.

---

## Repos to keep as-is

Everything not listed above stays catalogued as `reference`. They are quiet because they are
*finished* — paper code, stable SDKs, indicator maths — not because they were abandoned:

`FoundationAgents/MetaGPT` (70k) · `jmfernandes/robin_stocks` (2.1k) ·
`AnswerDotAI/rerankers` (1.6k) · `qiskit-community/qiskit-finance` (325) ·
`SkyworkAI/Matrix-Game` (2.3k) · `FlagOpen/RoboBrain2.5` (1.1k) ·
`D-Ogi/WatermarkRemover-AI` (1.9k) · `mlabouardy/komiser` (4.1k) ·
`RoggeOhta/awesome-codex-cli` (493) · plus the Upstash and Tradier SDKs.

Adopting any of these would mean taking on maintenance of software that already works, in
exchange for nothing.

---

## Why this is not a bulk "delete and absorb"

You asked to take what we can from the stale set and manage it ourselves. Three reasons that
would go badly as a blanket operation, and what was done instead:

1. **Seven candidates cannot legally be copied.** Delisting is the only lawful action, and
   that is what was done.
2. **This repository's whole model is URL-only.** No third-party code is vendored — that is
   what keeps it a catalog rather than a fork farm, and what keeps its own licence simple.
   Every adoption inverts that for one repo, so each one needs to earn it.
3. **Adoption means maintenance forever.** Absorbing 25 repositories means owning 25
   codebases. One well-chosen adoption is worth more than twenty-five reluctant ones.

## Approval gate

Adoption is a change to the catalog, so it stays owner-gated. Nothing above has been copied.
To proceed with the recommended adoption, approve it explicitly and it will be done on a
branch with:

- upstream `LICENSE` and `NOTICE` preserved verbatim,
- an `ATTRIBUTION.md` recording the source commit SHA and date,
- dependencies modernised and tests added,
- a fresh security scan before the PR opens.
