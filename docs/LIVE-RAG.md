# Live RAG

The general RAG lane in [REPO-CATALOG.md](REPO-CATALOG.md#rag-knowledge-and-memory) covers
retrieval quality: chunking, embedding, hybrid search, top-k. This lane covers one dimension that
lane ignores — **freshness**: how new and changed data reaches the index, how fast, and what
happens to deleted data. A retrieval stack can be excellent at finding the right chunk and still
be wrong, because the chunk is four hours old. Everything below is about closing that gap, or
deciding you do not need to.

Related:
- [agents/rag-stream.md](../agents/rag-stream.md) — Stream, the agent this doc is written for
- [agents/rag-vector.md](../agents/rag-vector.md) — Vector owns general retrieval design; do not duplicate it
- [repo-lists/live-rag.txt](../repo-lists/live-rag.txt) — flat list of this lane
- [VETTING-REPORT.md](VETTING-REPORT.md) — vetting verdicts for every repo below

---

## The four inputs

Nothing in this document is answerable without these. Stream asks them first, in this order,
and refuses to design until they are answered.

| Input | Question | Why it decides the architecture |
|---|---|---|
| Freshness SLA | How out of date can a retrieved answer be before it is wrong? | Sets the floor on pipeline latency. Everything else follows from it. |
| Change rate | Documents per hour, and what fraction are edits vs new? | Sets embedding cost. Cost scales with churn, not corpus size. |
| Change granularity | Whole documents replaced, or small edits inside large documents? | Decides whether chunk-level incremental update is worth building at all. |
| Consequence of staleness | Mildly outdated answer, or a wrong trade? | Decides whether you need staleness gating and fail-closed behaviour. |

If the answer to the first is "a day is fine", stop reading at the next section.

---

## First, decide if you need this

A nightly full rebuild is the right answer more often than teams expect. It has one moving part,
it deletes correctly by construction, it is trivially reproducible, and its failure mode is
loud. An incremental pipeline has a queue, a change-detection mechanism, a delete path, and a
silent failure mode where recall degrades and nobody notices for a month.

Build streaming infrastructure only when the freshness SLA genuinely requires it.

| Freshness SLA | Change rate | Do this |
|---|---|---|
| Days | Any | Nightly full rebuild. Nothing in this lane applies. |
| Hours | Low (corpus rebuilds inside the SLA) | Scheduled full rebuild every N hours. Still not incremental. |
| Hours | High (rebuild no longer fits the window) | Incremental upsert, batched. First real reason to be here. |
| Minutes | Low | Incremental upsert driven off a change feed or webhook. |
| Minutes | High | Streaming pipeline with an index that accepts live writes. |
| Seconds | Any | Streaming index, plus accept that some data should not be indexed at all. |

Three cases where the honest answer is "do not index this":

- **Values that change continuously.** Prices, inventory counts, order status. These belong in a
  tool call against the source of truth at answer time, not in a vector index. An embedding of a
  number is a bad representation of that number and a worse one a minute later.
- **Small corpora.** If the whole corpus re-embeds in minutes, rebuild it. Incremental machinery
  costs more engineering than it saves in compute.
- **Corpora that change by full replacement.** If documents are replaced wholesale rather than
  edited, incremental update degenerates into a rebuild with extra bookkeeping.

---

## Incremental vs rebuild

| Dimension | Full rebuild | Incremental |
|---|---|---|
| Staleness floor | The rebuild interval | Pipeline latency, typically seconds to minutes |
| Delete correctness | Correct by construction — the old index is discarded | Must be explicitly designed and tested. The usual bug. |
| Embedding cost driver | Corpus size, every run | Change rate |
| Moving parts | One scheduled job | Change detection, queue, upsert path, delete path, dead-letter handling |
| Failure mode | Loud — the job fails, you get paged | Silent — recall drifts down, deleted content lingers |
| Reproducibility | Byte-identical rebuild from source | Index state is a function of event history, not just source |
| Recovery | Re-run the job | Re-run the job (you still need the rebuild path as a fallback) |
| Evaluation | Compare rebuild to rebuild | Requires a fixed eval set run continuously, not once |

Keep the full rebuild path even after you build an incremental one. It is your recovery
mechanism, your correctness reference, and the only way to prove the incremental pipeline has
not drifted.

---

## The lane

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [getzep/graphiti](https://github.com/getzep/graphiti) | You need a knowledge graph that accepts incremental inserts and where every edge carries a validity interval, so "what was true then" is answerable. | `pip install graphiti-core` | Apache-2.0 |
| [pathwaycom/pathway](https://github.com/pathwaycom/pathway) | You need streaming ETL with incremental computation and a live in-memory vector index that updates as sources change. | `pip install pathway` | **FLAG — BUSL-1.1.** Source-available, **not** OSI-approved; GitHub reports `NOASSERTION`. See license notes. |
| [infiniflow/ragflow](https://github.com/infiniflow/ragflow) | You want a RAG serving platform with live document ingest and deep document understanding (OCR, table and layout recognition) rather than plain text extraction. | `git clone https://github.com/infiniflow/ragflow.git && cd ragflow/docker && docker compose up -d` | Apache-2.0 |
| [onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | Your corpus lives in SaaS tools and you want connector-driven polling re-index rather than writing sync code for Slack, Drive, Confluence and Jira yourself. | `cd deployment/docker_compose && docker compose -p onyx-stack up -d` | **FLAG — mixed.** Community Edition is MIT; `backend/ee` ships under a separate commercial licence. See license notes. |
| [vespa-engine/vespa](https://github.com/vespa-engine/vespa) | You need true in-place partial updates — changing one field without re-indexing the document — combined with vector, lexical and structured retrieval. | `docker run -d --name vespa -p 8080:8080 -p 19071:19071 vespaengine/vespa` | Apache-2.0 |
| [paradedb/paradedb](https://github.com/paradedb/paradedb) | Your source of truth is already Postgres and you would rather keep the index inside the database than run a CDC pipeline to a separate store. | `docker run -p 5432:5432 -e POSTGRES_PASSWORD=pw paradedb/paradedb` | **FLAG — AGPL-3.0.** Strong copyleft; network use triggers source obligations. See license notes. |
| [lightonai/pylate](https://github.com/lightonai/pylate) | You need late-interaction (ColBERT-family) multi-vector retrieval, where per-token vectors survive small document edits better than a single pooled embedding. | `pip install pylate` | MIT |
| [AnswerDotAI/rerankers](https://github.com/AnswerDotAI/rerankers) | You want second-stage precision without committing to one cross-encoder, so a stale-but-plausible chunk can be demoted at query time. | `pip install "rerankers[all]"` | Apache-2.0 (code). **Wrapped model weights carry their own licences, some non-commercial.** |
| [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) | The answer needs live retrieval loops — a supervisor spawning parallel isolated-context researchers — rather than one shot against a static index. | Clone, `uv sync`, then `langgraph dev` | MIT |
| [confident-ai/deepeval](https://github.com/confident-ai/deepeval) | You need to prove an incremental pipeline has not degraded recall — faithfulness and contextual precision/recall as pytest assertions in CI. | `pip install -U deepeval` | Apache-2.0 |

### License notes

The point of this column is that "open source" is not one thing. Four entries need reading
before you deploy them.

| Repo | What the licence actually restricts |
|---|---|
| pathwaycom/pathway | Business Source License 1.1 is source-available, not open source. BUSL grants limited free use through an **Additional Use Grant** and converts to an open licence on a **Change Date**. Both fields are set per-project in the repo's `LICENSE` file. Read them before any commercial deployment — do not assume the grant covers your case. |
| onyx-dot-app/onyx | Two licences in one tree. The Community Edition is MIT; the `backend/ee` directory is commercially licensed. If you fork, vendor, or redistribute, you must know which directories you shipped. |
| paradedb/paradedb | AGPL-3.0. Offering it as a network service to third parties triggers the source-disclosure obligation for your modifications. Fine for internal use; a legal decision for a hosted product. The vendor offers a separate commercial arrangement if AGPL is unworkable. |
| AnswerDotAI/rerankers | The library is Apache-2.0. The reranker checkpoints it downloads are not — several are non-commercial. The permissive library licence tells you nothing about the weights you pull through it. |

General rule for anything in this lane that serves models: the licence on the Python package and
the licence on the checkpoint are separate documents. Check both. `Apache-2.0 code, non-commercial
weights` is a real and common combination, and flattening it to "Apache-2.0" is how teams end up
shipping something they cannot ship.

Before adding any retrieval dependency not listed above, run it through
[SECURITY-SCANNING.md](SECURITY-SCANNING.md) or the portable version in
[skills/dep-audit](../skills/dep-audit/SKILL.md), and record the verdict in
[VETTING-REPORT.md](VETTING-REPORT.md).

---

## How to choose

```text
What is the freshness SLA?
├── Days ─────────────► Nightly full rebuild. Use the general RAG lane. Stop.
├── Hours
│   └── Does a full rebuild fit inside the SLA window?
│       ├── Yes ──────► Scheduled rebuild every N hours. Stop.
│       └── No ───────► Incremental. Continue.
└── Minutes / seconds ► Incremental or streaming. Continue.

Where does the data live?
├── Already in Postgres ──────► paradedb  (check AGPL first)
├── SaaS tools (Slack, Drive,
│   Confluence, Jira, GitHub) ► onyx      (check the MIT / ee split)
├── A stream or changing files ► pathway  (check BUSL before commercial use)
└── Documents you ingest ─────► ragflow

What shape is the retrieval?
├── Flat chunks ───────────────► vespa (in-place partial updates)
├── Entities and relations
│   that change over time ─────► graphiti (edges carry validity intervals)
└── Edits inside long documents ► pylate (late interaction is more edit-tolerant)

Always, regardless of branch:
├── Precision at query time ───► rerankers
├── Live multi-step answers ───► open_deep_research
└── Proof it did not regress ──► deepeval, on a fixed eval set, in CI
```

---

## The hard parts

These are the four things that actually break. Design each one explicitly, before writing the
ingest path.

### Deletes leak

Almost every incremental pipeline handles inserts correctly and leaks deletes indefinitely. A
document is removed at the source, the pipeline sees no event for it, and its chunks stay
retrievable forever. The system then answers confidently from content that no longer exists.

- Specify the delete path before the insert path. Soft-delete with a tombstone and a filter at
  query time, or hard-delete by stable chunk ID — but pick one and write it down.
- Deletion by absence (reconcile the index against a full source manifest) catches what event
  streams miss. Run it on a schedule even if events are reliable.
- Test it. The test is: delete a source document, then query for a phrase unique to it. That
  assertion belongs in CI, not in a runbook.

Deleted-source data still retrievable after an update is a correctness bug, not a backlog item.

### Chunk identity has to survive edits

Incremental means chunk-level. Re-embedding a 400-page manual because one paragraph changed is a
full rebuild wearing a costume, and it makes your cost scale with corpus size again.

That requires chunk IDs that are stable under unrelated edits. If chunk IDs are positional
(`doc42#chunk7`), inserting a paragraph on page 3 renumbers everything after it and the whole
document re-embeds. Derive IDs from content or from stable structural anchors (heading path,
section ID, block ID from the source system) so an edit invalidates only the chunks it touched.

Late-interaction retrieval ([pylate](https://github.com/lightonai/pylate)) is more tolerant here
than single-vector embedding, because per-token vectors degrade gracefully when surrounding text
shifts. It is not a substitute for stable identity, only a softer failure.

### Graph RAG has an insert cost flat retrieval does not

[graphiti](https://github.com/getzep/graphiti) gives you temporal edges and multi-hop queries.
The price is that ingest is not "embed and store" — entity and relation extraction runs per
document, typically as model calls. That cost is per change, so it lands directly on the
dimension this lane cares about.

Before choosing graph RAG for a live corpus, work out the extraction cost at your stated change
rate, not at your corpus size. A corpus that changes 50 times an hour pays for 50 extractions an
hour, forever. Budget it as a running cost, and confirm the retrieval quality gain is worth it on
your eval set before committing.

### Staleness must be visible, and sometimes must fail closed

Two separate requirements.

**Visible:** every retrieved chunk carries an as-of timestamp into the prompt. The generating
model cannot caveat what it cannot see. If a chunk was indexed six hours ago, the model should be
able to say so.

**Fail closed:** for any decision with financial or safety consequence, define a staleness
threshold past which the system refuses to answer rather than answering from old data. Refusing
is a correct output. Answering a trading question from a stale index is not.

| Consequence of staleness | Behaviour past the threshold |
|---|---|
| Mildly outdated answer | Answer, with the as-of timestamp stated |
| Wrong answer, recoverable | Answer, flagged, plus a refresh trigger |
| Financial or safety decision | Refuse. Return the staleness reason, not a guess. |

The threshold and the fail-closed behaviour for the last row need explicit human sign-off before
deployment. That is an escalation rule in [rag-stream.md](../agents/rag-stream.md), not a
preference.

---

## Limitations — what this lane will not do for you

- **It will not fix bad retrieval.** If the wrong chunk comes back, making it come back faster
  does not help. Fix chunking, embedding and ranking first, in the general RAG lane.
- **It will not make a chosen SLA achievable.** If the requested freshness is not reachable at
  the stated change rate and budget, no repo here changes that. Say so rather than shipping
  something that silently misses it.
- **No performance or benchmark claims are made here.** Ingest throughput, index latency and
  recall depend on your corpus, hardware and configuration. Measure on your own data; treat
  vendor numbers as marketing until reproduced.
- **The delete path is yours.** Every tool above can delete. None of them will notice that your
  source system removed a document and you never told it.
- **Nothing here decides consistency for you.** Read-your-writes across an incremental index is a
  system design question, not a library feature. If a user edits a document and immediately
  queries it, you must have designed for that.
- **Licences change between releases.** The flags above were researched at catalog time and
  recorded in [VETTING-REPORT.md](VETTING-REPORT.md). Re-check on major version bumps —
  BUSL Change Dates move, and relicensing to or from AGPL is common in this category.
- **Evaluation is not optional and is not included.** [deepeval](https://github.com/confident-ai/deepeval)
  gives you the harness; the fixed eval set that catches silent recall regression is work you
  have to do, and it has to run continuously rather than once.
