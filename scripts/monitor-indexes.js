// Indexes for the chat and code activity monitor store.
//
//   mongosh monitor --file scripts/monitor-indexes.js
//
// Safe to re-run: createIndex is idempotent when the spec and options match, and
// this is the step you repeat on every new machine. It is a file rather than a
// --eval one-liner because quoting a multi-statement --eval across PowerShell and
// bash is how it ends up half-run, with the unique index missing and duplicates
// already ingested.
//
// The design these belong to is docs/CHAT-CODE-MONITOR.md. Read the TTL notes
// there before changing expires_at: the field must be a Date, the index must stay
// single-field, and expireAfterSeconds: 0 is deliberate.

// "What did this person do recently" - the query behind every summary.
db.events.createIndex({ actor: 1, ts: -1 }, { name: "actor_recent" });

// "What happened on this repository" - the query behind a per-project rollup.
db.events.createIndex({ project: 1, ts: -1 }, { name: "project_recent" });

// Re-ingesting the same capture is a no-op rather than a duplicate. Without this,
// a restarted capture agent quietly doubles a day's events and every count built
// on top of them is wrong.
db.events.createIndex({ source_id: 1 }, { name: "source_unique", unique: true });

// Retention. expireAfterSeconds: 0 means "expire at the moment in expires_at", so
// the retention period is a property of whoever wrote the document. A shorter
// retention for one person or one project then needs no index change.
db.events.createIndex({ expires_at: 1 },
  { name: "events_ttl", expireAfterSeconds: 0 });

// Summaries outlive the events they were built from. No TTL here on purpose.
db.summaries.createIndex({ scope: 1, period_start: -1 }, { name: "scope_period" });
db.summaries.createIndex({ projects: 1, period_start: -1 }, { name: "project_period" });

// Consent is an audit record. Looking up "is this person's capture currently
// permitted" has to be one indexed query, or it becomes an assumption.
db.consent.createIndex({ actor: 1, scope: 1, granted_at: -1 }, { name: "consent_lookup" });

print("events:    " + db.events.getIndexes().map(i => i.name).join(", "));
print("summaries: " + db.summaries.getIndexes().map(i => i.name).join(", "));
print("consent:   " + db.consent.getIndexes().map(i => i.name).join(", "));
