---
name: master-graphify
description: Build and query a knowledge graph of a codebase with its docs, SQL schemas, configs and PDFs instead of grepping file by file. Use when orienting in an unfamiliar or large repository, tracing how two things connect, finding what everything flows through, or checking blast radius before a change. Wraps the catalogued graphify CLI and its /graphify skill, local and deterministic for code, with the one pass that can leave the machine named explicitly.
---

# Graphify

Grep answers "where does this string appear". It cannot answer "how do these two
things connect" or "what does everything here flow through", so those questions
get answered by reading twenty files into context and guessing. Graphify parses
the repository into a graph once, then those questions become one query against
a file that already holds the answer.

This skill grants nothing and installs nothing on its own. It says when the
graph is the cheaper tool, how to get one, and which parts of the output are
safe to repeat without checking.

## Reach for it when

- Landing in a repository nobody on the call has read end to end.
- Tracing a path: how does the request handler reach the schema it writes.
- Finding the concepts everything depends on, before choosing where to change.
- Blast radius: what touches this function, including through imports it does
  not name directly.
- A question spanning code and prose at once, where the answer lives partly in
  an ADR, a PDF or a SQL schema rather than in the source.

Skip it for a single known symbol in a repository you already know. One search
beats building a graph.

## Install and run

Published package, installed from PyPI. No clone is executed, which is what the
catalog gate in `AGENTS.md` requires of a third-party entry.

```bash
uv tool install graphifyy      # or: pipx install graphifyy
graphify install               # registers the /graphify skill with the assistant
```

Then, inside the assistant:

```
/graphify .
```

Three files land in `graphify-out/`: `graph.html` to click through,
`GRAPH_REPORT.md` for the written highlights, and `graph.json`, which is the one
that matters here because every later query reads it without re-reading the
repository.

```bash
graphify explain "APIRouter"          # one concept, its neighbours, its degree
graphify path "FastAPI" "ModelField"  # shortest path between two things
graphify query "how does auth work"   # scoped subgraph for a plain question
```

Requires Python 3.10 or newer. Registers for Claude Code, Cursor, Codex, Gemini
CLI, GitHub Copilot and others through `graphify install`.

## Many projects on one machine

One graph per folder answers questions inside that folder. A question that
crosses repositories ("where else did I implement this", "which project already
solves that") needs them connected, which is a separate step and the reason
`scripts/graphify_local.py` exists:

```bash
python scripts/graphify_local.py --discover      # find the code projects here
python scripts/graphify_local.py --index all     # index each, then merge
python scripts/graphify_local.py --status        # what is indexed, how fresh
python scripts/graphify_local.py --query "where is a rate limiter implemented"
```

Indexing is `graphify extract --code-only`: local AST parsing, no API key, and
the model-backed pass over docs and media is never reached from here. Each
project keeps its own `graphify-out/graph.json`, so `graphify query` works from
inside that folder with no arguments, and every graph is also merged into
`~/.graphify/global-graph.json`, which is what `--query` reads.

The registry of folders lives at `~/.graphify/projects.json`, outside this
repository, because it is this machine's layout rather than a project fact.
Re-run `--index all` after real changes; on one machine ten projects took about
thirty seconds in total.

## Read the edge tag before repeating the answer

Every edge carries its provenance, and the two are not equally trustworthy:

    EXTRACTED    explicit in the source. An import, a call, a declared base
                 class. Quote it.
    INFERRED     graphify resolved it. A good lead, not a citation. Open the
                 file before stating it as fact.

An inferred edge repeated as if it were read is exactly the failure
`cite-or-abstain` exists to stop. The tag is right there in the output, so
there is no excuse for dropping it on the way to the answer.

## The one pass that can leave the machine

Code is parsed locally with tree-sitter AST. Deterministic, no model involved,
nothing transmitted. That part is free and private, and it is most of the value.

The semantic pass over docs, PDFs, images and video is different: it uses the
assistant's model or a configured API key, so that content goes wherever that
model runs. Before pointing it at a directory, know what is in there. Customer
data, credentials in a runbook, anything under an NDA or a regulation: ask
Charles first, or scope the run to the code and leave the media out. Vendoring
nothing and sending nothing are separate promises, and this is the pass that
breaks the second one.

## Pin the branch, not the name

The upstream entry lives in `repo-lists/design-agent-skills.txt`, Apache-2.0,
renamed from its original owner.

Its default branch is `v8`, not `main`. Measured 2026-09-14: `main` sits 1,734
commits behind `v8` and carries 36 commits `v8` does not have. Reading `main`
gives a stale repository that still looks current, and a raw URL built by habit
lands there. Build documentation links and any pinned reference from `v8`, or
from the release the package was cut from.

The upstream also markets a hosted platform. The CLI and the graph are the
catalogued part. Early access to the service is not, and nothing here depends on
an account.

## How it composes

Feed the graph, not the tree. `master-token-reducer` wants a narrow question and
cited paths, and `graphify query` returns exactly that, so the graph becomes the
retrieval step rather than another thing to summarise. `master-architect` reads
the god nodes and communities as the real structure, which is worth more than a
diagram drawn from the folder layout. `master-plan` uses the path query to state
blast radius before touching anything.

Keep `graph.json` out of commits unless Charles asks for it. It is a derived
artifact, it goes stale the moment the code moves, and a stale graph asserted
confidently is worse than no graph.
