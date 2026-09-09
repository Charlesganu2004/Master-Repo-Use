# Private capability library: MongoDB plan

Status: proposal and offline preview. No cluster is created and no data is uploaded by the UI, a build, or an offline check. Charles approves this plan and creates the cluster before a first upload.

## What someone will see

In Atlas Data Explorer or Compass, open database `atlas`. There are nine named collections, including `skills`, `agents`, `tools` and `mcp`. A skill opens as a record with its description, source, full owned definition and content checksum. The same Family, Kind, Sub-category and lane relationships used in the website can be queried here.

The website's **Store** tab and **D36 MongoDB** design preview these records and indexes using local generated metadata. This is not a live database connection. GitHub Pages remains a static, privacy-filtered site.

## Data to store

| Collection | Contents |
|---|---|
| `skills` | Names, descriptions, categories, source references, commands and complete repo-owned `SKILL.md` text with SHA-256. Referenced third-party skill packs remain records, not copied source. |
| `agents` | Owned specialist role contracts in full, declared jobs, categories, scope and tool/approval instructions. Upstream frameworks carry their source and recorded health instead of copied code. |
| `tools` | Tool and script metadata, purpose, source path, commands and recipe references. Not executable binaries. |
| `mcp` | Connector metadata, source and setup references. No server credentials or tokens. |
| `components` | Cross-category records and relationships. Some data deliberately duplicates the four capability collections for unified search. |
| `lanes` | Categories, descriptions, source files and counts. |
| `routes` | Named agent/model handoff plans, participants, use cases and hardware requirements. A route record does not start an agent. |
| `surfaces` | Supported clients, modes, local-model requirements and setup mechanisms. |
| `recipes` | Reviewed setup commands and prerequisite metadata. Commands are data, not automatically executed from the database. |

Every record has a stable natural `_id`. Reloads update matching catalog IDs without dropping collections. Use a dedicated catalog database: edit canonical definitions in Git rather than making conflicting same-ID edits in MongoDB. Capability records have no automatic TTL expiry. Git remains the source of truth and version history.

Run `python scripts/load_catalog_mongo.py --collections` for current counts and JSON payload bytes. This estimate excludes BSON overhead, indexes and backups; it is not a cluster bill or capacity guarantee.

## Data not included

No model weights, third-party repository source bundles, passwords, API keys, connection credentials, cookies, screenshots, clipboard contents, browser history, prompts or transcripts are collected by this loader. Authored capability definitions can include owner names and policy text, so treat the catalog as private. A pre-upload scan rejects recognized credential patterns, but cannot prove arbitrary text contains no secrets; review the owned definitions before upload.

The activity-monitor design is separate. Capturing activity would need a new explicit decision about consent, redaction, access and retention. Do not enable monitoring as part of the capability-library setup.

## Architecture and access

1. Repo build produces catalog metadata. The local importer adds full owned skill and agent definitions only on the backend.
2. A dedicated import identity writes the private `atlas` database after approval. Store `MONGODB_URI` in the server's environment or secret manager, not a copied command, repository file or browser.
3. A future authenticated API uses a separate read-only database identity. It exposes bounded search/detail endpoints, parameter validation, explicit projections and authorization. It never accepts arbitrary MongoDB operators or shell commands from the browser.
4. Web pages call that API. Only approved fields are returned; direct database access and credentials stay off the frontend.

Restrict the Atlas network access list to the backend or use private networking. Use TLS, scoped database users and an appropriate backup policy. MongoDB documents these requirements in [cluster security](https://www.mongodb.com/docs/atlas/setup-cluster-security/).

## Indexes and verification

The repo defines ordinary compound/text indexes for family/kind, lane/order, source, recipe, route participants and model memory requirements. Full-text skill search includes the complete owned definition. These are standard database indexes, not embeddings or a paid search service. See [compound-index prefixes](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-compound/).

The unique source index includes only lanes marked `isFileSource: true`, avoiding duplicate `runtime` sentinels. Queries must include that predicate to use the [partial index](https://www.mongodb.com/docs/manual/core/index-partial/). The earlier `$ne` partial-filter draft was invalid and has been corrected to supported boolean equality.

`--check` validates documents, field coverage and expected index relationships offline. `--explain` is an illustrative plan, not a database query planner result. After cluster creation, use real `explain('executionStats')`, inspect `getIndexes()`, verify representative searches and compare stored definition checksums before calling the live integration verified.

## After Charles approves

1. Charles creates a private Atlas project/cluster and supplies access through a secret manager, never in chat.
2. Configure a narrowly scoped importer user and network access. Choose a reviewed PyMongo version for an isolated backend environment.
3. Run `python scripts/load_catalog_mongo.py --check` and review `--collections` locally.
4. With `MONGODB_URI` set privately, run `python scripts/load_catalog_mongo.py --load --db atlas`.
5. Connect `mongosh` securely to that same cluster and database, then run `load('scripts/catalog-indexes.js')`. Do not paste credentials into command history.
6. Check live indexes, counts, definitions and query plans. Only then connect an authenticated read-only API and the UI.

Creating the cluster, uploading data and deploying the authenticated API remain separate approval-gated steps, not side effects of the static preview.
