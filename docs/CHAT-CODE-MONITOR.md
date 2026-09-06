# Chat and Code Activity Monitoring

Charles asked for a lane that watches the chat and the current window, transcribes what is on
screen, checks what everyone on a team has been doing in their own windows, and turns that into a
summary somebody else can read. This document is how that gets built, what it costs, and the two
places where the obvious design is the wrong one.

Related:
- [repo-lists/chat-code-monitor.txt](../repo-lists/chat-code-monitor.txt) — the vetted pieces
- [repo-lists/document-store-indexing.txt](../repo-lists/document-store-indexing.txt) — the store
- [repo-lists/media-transcription-ocr.txt](../repo-lists/media-transcription-ocr.txt) — speech and OCR
- [docs/SECURITY.md](SECURITY.md) — scanning and secret rules that apply to the captured text
- [docs/TOKEN-BUDGET.md](TOKEN-BUDGET.md) — the summariser is the expensive stage; budget it there

---

## The honest finding first

This is two mature problems and one immature one.

| Piece | State of the art | Verdict |
|---|---|---|
| Capturing a screen continuously, locally | Solved. `screenpipe/screenpipe`, `openrecall/openrecall` | Use one |
| Tracking which app and window had focus | Solved. `ActivityWatch/activitywatch` | Use it |
| OCR and speech-to-text over the capture | Solved. See the media lane | Use it |
| Storing and searching the result | Solved. MongoDB, below | Use it |
| Turning a session into a summary a team reads | **Not solved.** Every dedicated project found on 2026-09-04 had 0 to 1 stars | Assemble it |

The summariser is the part you write. `danielmiessler/Fabric` gives you composable prompt patterns
for it, and `nilbuild/git-standup` gives you the git half for free, but nothing off the shelf turns
"here is nine hours of screen text" into "here is what the team shipped". Plan for that, rather than
expecting to install it.

---

## The consent problem, once

Everything in the capture section records a person's screen and keyboard. On a shared or work
machine that is a decision about other people, not only about you.

The specific thing that does not work: you cannot point this at a colleague's machine and read what
they have been doing. Not because of a missing feature, but because remote silent monitoring of
another person's screen is the definition of the thing that gets a tool classified as spyware, and
because in a two-party-consent jurisdiction capturing a call transcript without the other side
agreeing is unlawful regardless of intent.

The design that works instead, and gives you the same answer:

> Each person runs their own capture agent locally. Each agent publishes **summaries** into a shared
> store. Nobody's raw screen text leaves their machine. The team view reads summaries, not frames.

That is not a compromise made for politeness. It is also the cheaper architecture: raw capture is
gigabytes per person per day and summaries are kilobytes, so the thing you actually want to
replicate across a team is the small one.

Record consent as data, not as an assumption. The `consent` collection below exists so that "who
agreed to be captured, when, and to what retention" is a query rather than a memory.

---

## Four decisions before any of it

| Decision | Question | What it settles |
|---|---|---|
| Granularity | Do you need the words on screen, or only which app and file had focus? | Focus-only removes OCR, the GPU, and most of the privacy surface. It answers "what were you working on" but not "what did it say". |
| Audience | Does the summary go to you, or to other people? | A private recall index needs no consent machinery and no redaction. A team summary needs both. |
| Retention | How long is a raw frame worth keeping? | Sets the TTL. This is the single most effective privacy and cost control in the design. |
| Latency | Is a daily rollup enough, or does someone need "what is happening now"? | Daily means one batch summariser call per person. Live means a streaming pipeline and roughly two orders of magnitude more model spend. |

If the answers are "focus-only", "just me", "a week", and "daily", the whole lane is ActivityWatch
plus a cron job and you can stop reading here. That is a real answer, and it is the right one more
often than the full build.

---

## Architecture

Five stages. Each is separately replaceable, which matters because the fifth one is the one you will
rewrite.

```
capture  ->  extract  ->  store  ->  index  ->  summarise  ->  deliver
screenpipe   OCR/ASR      MongoDB   mongot     Fabric/model   the team view
ActivityWatch                       $search                   (summaries only)
```

### 1. Capture

| Tool | Licence | What it gives you | The catch |
|---|---|---|---|
| `screenpipe/screenpipe` | NOASSERTION on the API. **Read `LICENSE` before building on it** | Continuous local screen and audio with search | Licence is "Other"; treat the field as unknown until read |
| `openrecall/openrecall` | AGPL-3.0 | Fully local recall, no vendor | AGPL is viral. Fine to run, expensive to link into a product |
| `ActivityWatch/activitywatch` | MPL-2.0 | Focus, window title, app, per-second | No screen text. MPL is file-level copyleft and easy to live with |

Start with ActivityWatch. It answers the granularity question cheaply and tells you whether you
actually need frames before you commit to storing them.

### 2. Extract

Not duplicated here. The OCR and speech pieces live in
[repo-lists/media-transcription-ocr.txt](../repo-lists/media-transcription-ocr.txt), which owns them.

One rule that belongs here rather than there: **redact before storing, not before reading.** Screen
capture will photograph a `.env` file, an auth header in a devtools panel, and a password manager
mid-unlock. Run the secret patterns from [docs/SECURITY.md](SECURITY.md) over extracted text on the
way into the store. A secret that reaches the database has already leaked into every backup of it.

### 3. Store: MongoDB

The engine and its drivers are in
[repo-lists/document-store-indexing.txt](../repo-lists/document-store-indexing.txt). The licence
point in one line: the **server** is SSPL, which is not OSI open source and which attaches if you
offer MongoDB itself as a service. Using it as the database inside your own tool is fine. The
drivers are Apache-2.0 and carry none of it.

Four collections. The split is not cosmetic: it is what lets raw capture expire on a short clock
while the summaries built from it survive.

```js
// events - one document per captured moment. High volume, short life.
{
  _id:        ObjectId(),
  source_id:  "screenpipe:2026-09-04T09:14:22Z:1",  // idempotent ingest key
  actor:      "charles",          // who was captured
  machine:    "charl-desktop",
  ts:         ISODate("2026-09-04T09:14:22Z"),
  app:        "Code",
  window:     "build_atlas_data.py - Master-Repo-Use",
  project:    "Master-Repo-Use",  // derived from window/cwd, not guessed
  kind:       "screen",           // screen | audio | focus | agent-session
  text:       "def antigravity_recipes() -> list[dict]: ...",
  redacted:   ["aws-access-key"], // what was stripped, never what it was
  expires_at: ISODate("2026-09-11T09:14:22Z")
}

// summaries - one per rollup. Low volume, long life. This is the shareable artifact.
{
  _id:          ObjectId(),
  scope:        "charles",        // or a team id
  period_start: ISODate("2026-09-04T00:00:00Z"),
  period_end:   ISODate("2026-09-05T00:00:00Z"),
  body:         "Rebuilt the atlas data layer; added the Antigravity surface node...",
  projects:     ["Master-Repo-Use"],
  evidence:     [ObjectId(), ObjectId()],   // the events it was built from
  model:        "llama3.1:8b",
  generated_at: ISODate("2026-09-05T00:05:00Z")
}

// sessions - one per capture run, so a gap in the data is visible as a gap
{ _id, actor, machine, client, started_at, ended_at, tool, tool_version }

// consent - who agreed to what. An audit record, not a checkbox.
{ _id, actor, scope, granted_at, revoked_at, retention_days, granted_by }
```

### 4. Index

The indexes, and what each one is for. Create them before the first large ingest, not after.

```js
db.events.createIndex({ actor: 1, ts: -1 })                    // "what did X do recently"
db.events.createIndex({ project: 1, ts: -1 })                  // "what happened on this repo"
db.events.createIndex({ source_id: 1 }, { unique: true })      // re-ingest is a no-op
db.events.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })

db.summaries.createIndex({ scope: 1, period_start: -1 })   // no TTL here, on purpose
db.summaries.createIndex({ projects: 1, period_start: -1 })

db.consent.createIndex({ actor: 1, scope: 1, granted_at: -1 })  // permitted? one query
```

These live in [scripts/monitor-indexes.js](../scripts/monitor-indexes.js) so they can be re-run on
each new machine without being retyped.

Three things about that TTL index that cost people a day each:

- The field must hold a **Date**. A string that looks like a date is ignored silently.
- A TTL index is **single-field only**. Compound indexes accept `expireAfterSeconds` and then ignore
  it, which is the worst of both.
- `expireAfterSeconds: 0` means "expire at the moment in the field", which is why `expires_at` is
  written per document. Retention then becomes a property of the writer, so a shorter retention for
  one person or one project needs no index change. The remover runs every 60 seconds, so deletion is
  prompt, not instant.

**Full-text and vector search, checked on 2026-09-04 rather than assumed.** `$search`, `$searchMeta`
and `$vectorSearch` are no longer Atlas-only: they run on self-managed Community and Enterprise
deployments from MongoDB **8.2** onward, at functional parity with Atlas apart from preview features.
The catch is operational rather than commercial. They are served by a **separate `mongot` binary**,
not by `mongod`: a self-managed deployment runs two `mongot` processes per replica set and `mongod`
routes the search stages to them over gRPC. So the requirement this creates is a **replica set**. A
bare standalone `mongod` on a laptop cannot serve `$search` at all, and that is the configuration
most people start with.

Two honest paths:

| You have | Use | Why |
|---|---|---|
| A laptop, standalone `mongod`, one person | `$text` index and regex | No mongot, no replica set, no extra process to babysit |
| MongoDB 8.2+ as a replica set, or Atlas | `$search`, and `$vectorSearch` for "find the day I was fighting this bug" | Fuzzy matching, relevance scoring, highlighting, synonyms |

Do not put a `$search` call in the code path before the replica set exists. It fails at query time,
not at startup, which means it fails in front of whoever asked for the summary.

### 5. Summarise and deliver

This is the stage you write, and the only stage that spends model tokens. Three properties worth
building in from the start:

- **Summarise per person, locally, then share the summary.** Keeps raw text on the machine that made
  it, and keeps the cross-team payload small.
- **Cite the evidence.** The `evidence` array of event ids is what makes a summary checkable. A
  standup summary nobody can verify is a rumour with a timestamp.
- **Run it on a local model.** This is bulk, low-stakes, high-volume text. Check
  [docs/LOCAL-MODEL-HARDWARE.md](LOCAL-MODEL-HARDWARE.md) for what the machine can host. Sending a
  day of screen text to a hosted model is the easiest way to make this lane expensive, and also the
  easiest way to send a captured secret to a third party.

For the git half, `nilbuild/git-standup` already answers "what did this person commit yesterday"
from history alone, with no capture at all. Run it first. On many days it is the whole summary, and
it costs nothing and records nobody.

---

## Setup

Ordered. Each step is checkable before the next one matters.

```bash
mongosh --eval 'db.runCommand({ ping: 1 })'
```

Install first if that fails. Windows: `winget install --id MongoDB.Server` then
`winget install --id MongoDB.Shell`. macOS: `brew tap mongodb/brew && brew install mongodb-community mongosh`.
Debian and Ubuntu: follow the vendor apt instructions rather than a distro-packaged `mongod`, which
is usually several major versions behind and will not have 8.2.

```bash
mongosh monitor --file scripts/monitor-indexes.js
```

That file holds the `createIndex` calls above and prints what exists afterwards. Keeping them in a
file rather than a shell one-liner matters: index creation is the step you re-run on every new
machine, and a quoted-inside-quoted `--eval` is how it silently half-runs, leaving the unique index
missing after duplicates have already been ingested.

```bash
curl -s http://127.0.0.1:5600/api/0/buckets
```

ActivityWatch serves on `127.0.0.1:5600`. An empty bucket list means it is running but has not
attached a watcher yet; a connection refused means it is not running.

```bash
npx -y mongodb-mcp-server --connectionString "mongodb://127.0.0.1:27017/monitor" --readOnly
```

Register that MCP server read-only first. The summariser needs to read events and write summaries;
nothing in this lane needs an assistant holding delete rights over the capture history.

---

## What not to build

- **A central raw-capture store.** Every frame from every teammate in one database is a breach with a
  schedule. Summaries replicate; frames stay home.
- **A live "what is everyone doing right now" wall.** It is technically the same pipeline with the
  batch window set to zero, it costs roughly a hundred times more in model calls, and the thing it
  produces is surveillance rather than a standup.
- **Vector search before text search.** `$text` or `$search` answers "when did I touch this file"
  well. Embeddings are for "the day I was fighting that weird TLS thing", which is a real query, but
  a second one.
- **Storing the redacted value "just in case".** Store the *name* of what was stripped. The moment
  the original is kept anywhere, every retention and consent guarantee above becomes decorative.
