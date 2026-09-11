# Managed capability registry: proposal

Status: architecture for Charles to review, not a deployed service. No database,
GitHub App, client watcher, telemetry upload, automatic update or deletion is
enabled by this document. The existing [MongoDB catalog plan](MONGODB-PLAN.md)
is a smaller, separate offline catalog import. It is not already this registry.

## Decision

The idea is viable: distribute versioned skills, agents, tools, plugins and MCP
connectors, review their provenance and security, watch upstream changes, notify
users, and require human approval for retirement or managed adoption.

Use a metadata database plus immutable package storage, not one database full of
mutable installations. Keep authored source, packaging recipes and policy in Git.
Do not move the only copy of capability definitions out of version control.

For this expanded multi-user service, the recommendation is PostgreSQL with
JSONB metadata and object storage for archives. Versions, dependencies, tenant
access, approvals and installation records are naturally related. JSONB can hold
varying manifests and supports indexing. This is a design recommendation, not a
claim that MongoDB cannot implement the workflow. JSONB does not preserve JSON
formatting or duplicate keys, so exact package and definition bytes belong in
the artifact, not a reconstructed JSONB document.
[PostgreSQL JSON documentation](https://www.postgresql.org/docs/current/datatype-json.html).

MongoDB plus the same object storage is also viable and reuses the current
catalog importer. Do not operate both databases in the first version. MongoDB
has a 16 MiB document limit and GridFS for larger files; the proposed separation
is an operational choice, not a claim that MongoDB cannot store files.
[MongoDB GridFS](https://www.mongodb.com/docs/manual/core/gridfs/).

## Architecture

```mermaid
flowchart TD
    C[Opt-in client inventory agent] -->|Approved metadata only| I[Authenticated intake API]
    W[Upstream release and advisory watcher] --> I
    I --> Q[Private quarantine and job queue]
    Q --> S[Isolated static review and controlled build workers]
    S --> R[GitHub issue or PR with digest-bound human review]
    R -->|Approved candidate| P[Trusted publication worker]
    P --> D[(Registry metadata database)]
    P --> O[(Immutable package storage)]
    P --> G[Approved Git catalog projection]
    D --> A[Authenticated catalog and resolution API]
    O -->|Authorized package download| V[Client signature and digest verification]
    A --> V
    V --> L[Local cache, install and harness adapters]
    D --> N[Update and security notifications]
    W -->|Stale or archived| H[Human lifecycle decision]
    H -->|Maintain a fork| Q
    H -->|Approve exact retirement scope| T[Tombstone and durable cleanup jobs]
    T --> D
    T --> O
    T --> G
    T --> N
```

The ordinary website never receives database credentials, registry signing keys
or private package inventories. GitHub is the review interface and source host,
not the destination for unreviewed user files or malware specimens.

## Ownership and boundaries

| Component | Owns | Depends on; changes when |
| --- | --- | --- |
| Local agent and adapters | User consent, local discovery scope, installation receipts and cache | Registry API; supported client interfaces change |
| Intake service | Candidate identities, submission consent and quarantine admission | Auth and bounded fetcher; supported submission formats change |
| Review workers | Reproducible scan/build evidence for exact bytes | Quarantine objects and reviewed scanner images; security policy changes |
| Registry service | Package lifecycle, immutable version records, approvals, channels and durable jobs | Verified review evidence and artifact digests; publication/lifecycle rules change |
| Artifact storage | Exact immutable package bytes keyed by digest | Publication and cleanup identities; storage implementation changes |
| GitHub integration | Sanitized review presentation and approved catalog projection | Registry events and GitHub API; review integration changes |
| Client resolver | Authorized, compatible, non-revoked version selection | Registry state; client/runtime compatibility rules change |

Git owns authored source and policy revisions. The registry database owns
publication and retirement state. Git catalog files and website indexes are
generated projections of approved registry state, not competing editable copies.
Object hashes identify the only authoritative bytes for each published artifact.

Start with one backend application and a bounded worker pool. A database-backed
job table and transactional outbox are enough initially; separate microservices,
another search database and a distributed event platform are not prerequisites.

## What is stored

| Location | Data |
| --- | --- |
| Metadata database | Stable namespace/package ID, kind/family/subcategory, descriptions, upstream URL and exact commit, version, artifact digest/size/location, license and notices, dependencies, permissions, client/OS/architecture compatibility, review status, source health, channels and revocations |
| Private operational tables or collections | Consent, tenant access, minimal installation/version receipts, scan jobs and reports, approval identity and scope, audit events, tombstones and retryable publication/deletion jobs |
| Immutable artifact storage | Complete permitted skill/agent definitions, scripts, manifests, lockfiles, notices and redistribution-approved archives; containers may use an OCI container registry |
| Git | Owned source, packaging recipes, policies, approved manifest changes and sanitized review history |
| Secret manager | Backend credentials, signing credentials and scoped GitHub integration credentials, never package manifests or frontend JavaScript |

Small owned definitions may also have exact full-text database copies for
authenticated inspection and search, with checksums back to the artifact. No
capability definition is shortened, substituted with a summary, or dropped to
reduce tokens. A search result is a retrieval aid, not a replacement definition.

Index stable package IDs, namespace/version, digest, kind/family/subcategory,
dependency edges, lifecycle status, and tenant/installed version. Add full-text
description search. Add vector search only if measured search needs justify it.
Indexes make those lookups efficient; they do not make a capability executable.

Do not collect prompts, transcripts, environment values, secrets, browser data,
screenshots, private file paths or entire working directories by default.
Installed-version receipts identify pseudonymous tenant/device IDs only where
the user consented. Even package names can reveal private work, so allow
local-only comparison against a signed public catalog without uploading inventory.

Hosted services cannot necessarily be repackaged. A remote MCP service usually
needs a reviewed connector descriptor, endpoint identity, permission/tool schema
and credential references, not a copy of the service. Proprietary plugins and
unlicensed code remain reference-only unless redistribution rights are verified.
Public availability on GitHub is not permission to redistribute arbitrary code.
[GitHub licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

## Intake and publication

1. The user enables specific discovery adapters and roots. A real local service
   or CLI observes supported installs/configuration changes; a skill alone is not
   an always-running watcher and cannot observe every hosted chat product.
2. Send only approved source coordinates, version and digest first. Unknown
   private/custom content requires separate upload consent and ownership review.
   Upload it to private quarantine, not the main repo or a public issue.
3. Resolve canonical source identity and an exact immutable commit/artifact.
   Limit download size, unpacked size, time and file count. Reject path traversal,
   unsafe links and archive bombs. Restrict schemes and destinations, block
   private/metadata IP ranges and validate every redirect to prevent SSRF.
4. Run static provenance, license, malware, secret, dependency/advisory, hidden
   Unicode, injection, install-hook and workflow checks. Flag suspicious invisible
   text for review; legitimate language/emoji sequences are not automatically
   malware. Preserve original bytes and report scanner coverage and errors.
5. Do not execute candidates during initial intake. If later testing needs code
   execution, use disposable isolated workers without production secrets, with
   explicit network policy and resource limits. Never run candidate installers
   on Charles's workstation or a persistent privileged runner.
6. Scan both source and the final artifact, including bundled dependencies. Record
   hashes, scanner/rule versions, license results, a software bill of materials
   and provenance. A missing/failed scanner means incomplete review, not pass.
7. Human review binds approval to package ID, source commit, artifact digest,
   permissions and policy revision. Editing any bound item invalidates approval.
   The publication identity is separate from the untrusted build worker.
8. Publish an immutable artifact and approved version record. Clients verify the
   trusted signer, digest, supported platform, dependency lock and revocation
   state before installing. An interrupted install must leave the previous
   working version or a recoverable state.

No finite scan proves software harmless. Provenance demonstrates origin and
build identity, not freedom from vulnerabilities.
[GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations).
Treat AI-assisted reviewers as advisory: they cannot authorize publication or
execute instructions from scanned files. Sanitize rendered reports and tool
descriptions; scan text remains untrusted data after it is stored.

Use parameterized SQL and validated, allowlisted NoSQL query construction in
the service itself. Scanning a package for injection is not a substitute for
protecting our database API. Enforce tenant authorization on every read/write.
[OWASP SQL injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html),
[OWASP NoSQL security](https://cheatsheetseries.owasp.org/cheatsheets/NoSQL_Security_Cheat_Sheet.html).

## Updates and notifications

Use authenticated GitHub App webhooks where the app has access. For arbitrary
upstream repositories, use rate-limited conditional polling; creating a repo
webhook requires owner/admin access. Verify webhook signatures, deduplicate event
IDs, retry with backoff and periodically reconcile missed events.
[GitHub webhook permissions](https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks),
[GitHub API best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api),
[Webhook validation](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries).

Watch release assets, commits and security advisories, not just version labels.
A moved tag or changed artifact digest is a new review candidate. Reassess
already published versions when new advisories or scanner rules arrive.

Every candidate update passes intake again. Distinguish `upstream available`,
`approved update`, `incompatible`, `unsupported` and `revoked` in the UI. Compare
against the newest approved version compatible with that client's lock and
channel, not merely the numerically newest upstream release.

Notify by default. Automatic installation is a separate opt-in policy, limited
to pre-approved risk classes after compatibility tests and staged rollout.
New permissions, major changes and license changes require fresh approval.
Keep rollback artifacts unless the version has been revoked. A locally modified
installation is not overwritten silently; show the diff or install side by side.

Cache signed approved packages for availability, but give revocation/catalog
metadata an expiry. On expired security metadata, block new installs and updates;
the tenant explicitly decides whether existing offline execution may continue.
Do not promise an offline machine can receive immediate revocation.

## Stale projects, forks and human-approved removal

Inactivity is a review signal, not proof of abandonment. Check archive reason,
release cadence, vulnerabilities, current users, dependency impact, alternatives,
license rights, tests and realistic maintenance cost. Adopt in house only with a
named owner, patch/support budget, test/build coverage and an exit plan. A fork
gets a new namespace and recorded upstream lineage; do not impersonate upstream.

Removal is not one `DELETE` statement:

1. Open or refresh one review issue with exact IDs/digests, reasons, reverse
   dependencies, affected installs, replacement options and proposed scope.
2. Verify the approver's GitHub identity and current authority. Bind approval to
   that issue's exact deletion plan digest; a label or arbitrary comment is not
   authorization. New scope requires new approval.
3. Record a tombstone and stop new installs once the approved retirement takes
   effect. Notify affected users and provide migration instructions.
4. Commit the lifecycle change and cleanup jobs together in the registry's
   transaction. Idempotent workers update the Git catalog, database search
   projections, artifact storage and caches, retrying partial failures. Record a
   receipt per target and verify convergence before closing the issue.
5. Purge only approved, unreferenced artifact versions after the chosen retention
   or hold period. Preserve a minimal audit/tombstone record so a watcher cannot
   silently reimport the same rejected package.

Git history, storage backups and users' downloaded copies are separate retention
domains. Deleting the live catalog cannot instantly erase them. State the backup
expiry and any required history-remediation process. Do not delete a user's local
installation without their consent or an explicit managed-device policy.

An emergency response policy should be approved in advance: a confirmed malicious
digest can then be blocked from new distribution immediately while a human
reviews. That is a temporary security quarantine, not permission for a bot to
permanently delete capabilities. Without that policy, escalate for approval.

## Delivery phases and acceptance gates

1. **Private registry pilot.** Choose one database, object storage and retention
   policy. Package only owned/approved capabilities; implement identity, exact
   version manifests, authenticated search/download and checksum verification.
   Gate: round-trip full definitions byte-for-byte and reject digest mismatch.
2. **Review pipeline.** Add private quarantine, bounded workers, evidence reports,
   GitHub approvals and signed publication. Gate: no candidate executes during
   intake; scanner failure and approval/digest mismatch block publication.
3. **Upstream maintenance.** Add deduplicated release/advisory watching, compatible
   version comparisons, notifications and rollback. Gate: duplicate events create
   one candidate, permission changes require review, and rollback is exercised.
4. **Opt-in client monitoring.** Ship the local agent plus a discoverable control
   skill/MCP interface and explicit supported-client matrix. Integrate the
   existing no-slash harness adapters. Gate: local-only mode makes no inventory
   upload, private paths/secrets never enter submissions, and unknown clients are
   reported unsupported rather than silently claimed covered.
5. **Lifecycle operations.** Add adoption dossiers, precise retirement approval,
   tombstones and cleanup reconciliation. Gate: dependency impact is visible,
   retries cannot widen deletion scope, partial failures recover, and restoration
   from backup replays tombstones before enabling downloads.

Size the service using observed package sizes, download volume, scanner CPU time,
retention and human review load. Database capacity alone is not the operating cost.
Do not commit to fleet-wide automatic upgrades until those gates and key-rotation,
backup-restore and incident-response drills have passed.
