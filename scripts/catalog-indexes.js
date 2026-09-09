// Indexes for the catalog itself, loaded into MongoDB.
//
//   mongosh atlas --file scripts/catalog-indexes.js
//
// This is a different store from scripts/monitor-indexes.js, and the difference
// is worth stating because the two look similar and behave nothing alike.
//
//   monitor   append-only events, written constantly, expired on a TTL. The
//             queries are "what did this person do recently".
//   catalog   1120 components across 177 lanes, rewritten wholesale whenever
//             scripts/build_atlas_data.py runs. Nothing expires. The queries are
//             the ones the atlas interface already makes: filter by family, by
//             kind, by lane, search by name, and find what a route names.
//
// So there is no TTL here, and the write pattern is a full reload rather than a
// stream. Reload is why every index is created after the load in the loader, and
// why source_unique has no counterpart: a catalog document has a natural id.
//
// Safe to re-run. createIndex is idempotent when the spec and options match.

// "Show me this family" and "show me this kind", which is the filter bar on
// every one of the thirty designs. Family first because it is the coarser cut
// and a compound index answers a prefix query too: this one alone serves
// {family} and {family, kind}, so no separate family-only index is needed.
db.components.createIndex({ family: 1, kind: 1 }, { name: "family_kind" });

// "What is in this lane", which is what clicking a lane does. order carries the
// author's own sequence, so the sort comes off the index rather than from a
// sort stage in memory.
db.components.createIndex({ lane: 1, order: 1 }, { name: "lane_order" });

// The search box. A text index rather than a regex scan, because a regex without
// a left anchor cannot use a btree index at all and 1120 documents is enough to
// notice. Weighted so a name match outranks a description match, which is what
// somebody typing a name expects.
db.components.createIndex(
  { name: "text", detail: "text" },
  { name: "component_search", weights: { name: 10, detail: 2 } });

// "Which components can actually be set up", the question behind the Build
// basket. Sparse because most components carry no recipe, and a sparse index
// skips those documents instead of storing a null for each one.
db.components.createIndex({ setupRecipe: 1 },
  { name: "by_recipe", sparse: true });

// Lanes are browsed by family, and inside a family by how much they hold.
db.lanes.createIndex({ family: 1, count: -1 }, { name: "lane_family_size" });

// A lane is looked up by the file it came from when a design links back to
// source. Unique, but PARTIAL: the fifteen runtime stage lanes all carry the
// sentinel "runtime" rather than a path, so a plain unique index rejects the
// load with a duplicate key error on the second one. Checked against the real
// catalog, which is how that was found rather than discovered on first load.
// The claim worth keeping is narrower: no real file backs two lanes.
db.lanes.createIndex({ source: 1 },
  { name: "lane_source", unique: true,
    partialFilterExpression: { isFileSource: true } });

// "Which routes touch this component" and "which touch this lane". members and
// lanes are arrays, so both of these are multikey: one route naming four
// components gets four index entries and matches any of them.
db.routes.createIndex({ members: 1 }, { name: "route_members" });
db.routes.createIndex({ lanes: 1 }, { name: "route_lanes" });

// The surface picker groups by group, then filters local models by memory.
// NOT sparse, though minRamGb is absent on 14 of the 49. A compound sparse index
// only skips a document missing every indexed field, and group is on all of
// them, so sparse would skip nothing while claiming the opposite. The leading
// field decides.
db.surfaces.createIndex({ group: 1, minRamGb: 1 }, { name: "surface_group_ram" });

// Setup recipes are fetched by id constantly, once per rendered command. _id
// already covers that, so the only index worth adding is the one that answers
// "which recipes are ready on this platform".
db.recipes.createIndex({ kind: 1, state: 1 }, { name: "recipe_ready" });

print("components: " + db.components.getIndexes().map(i => i.name).join(", "));
print("lanes:      " + db.lanes.getIndexes().map(i => i.name).join(", "));
print("routes:     " + db.routes.getIndexes().map(i => i.name).join(", "));
print("surfaces:   " + db.surfaces.getIndexes().map(i => i.name).join(", "));
print("recipes:    " + db.recipes.getIndexes().map(i => i.name).join(", "));

// ---------------------------------------------------------------------------
// skills, agents, tools and mcp as collections of their own.
//
// Charles asked that someone opening MongoDB finds these four there. They could
// have been a query over components with a family filter, and that is what the
// first version was, but then `show collections` answers with one bucket and you
// have to already know the field name to find anything. A collection you can see
// is worth the duplication: the four together are 214 KB, and components stays
// for the cross-family queries.

// "What do we own, and what are we only pointing at." origin is the field that
// separates a skill whose full text is stored from a repository we deliberately
// do not vendor, so it leads every one of these.
db.skills.createIndex({ origin: 1, name: 1 }, { name: "skill_origin" });
db.agents.createIndex({ origin: 1, name: 1 }, { name: "agent_origin" });
db.tools.createIndex({ origin: 1, name: 1 }, { name: "tool_origin" });
db.mcp.createIndex({ origin: 1, name: 1 }, { name: "mcp_origin" });

// "Which of these has gone stale, been archived, or failed a scan." Only a
// catalogued document carries health, so skills and mcp are sparse: 35 of 132
// and 33 of 35, and storing a null for the rest buys nothing.
//
// agents is NOT sparse, because every one of the 50 is catalogued and carries
// health. Sparse there would skip nothing while claiming the opposite, which is
// the same mistake surface_group_ram made and the checker caught both.
db.skills.createIndex({ "health.status": 1 }, { name: "skill_health", sparse: true });
db.agents.createIndex({ "health.status": 1 }, { name: "agent_health", sparse: true });
db.mcp.createIndex({ "health.status": 1 }, { name: "mcp_health", sparse: true });

// Search the skills we own by what is actually in them. The body is the whole
// SKILL.md, so this searches the instructions rather than a one-line summary,
// which is the difference between a catalog and a library.
db.skills.createIndex(
  { name: "text", detail: "text", "definition.body": "text" },
  { name: "skill_fulltext",
    weights: { name: 10, detail: 4, "definition.body": 1 } });

// Every collection above is browsed by the lane that vouches for the entry.
db.skills.createIndex({ lane: 1 }, { name: "skill_lane" });
db.agents.createIndex({ lane: 1 }, { name: "agent_lane" });
db.tools.createIndex({ lane: 1 }, { name: "tool_lane" });
db.mcp.createIndex({ lane: 1 }, { name: "mcp_lane" });

print("skills:     " + db.skills.getIndexes().map(i => i.name).join(", "));
print("agents:     " + db.agents.getIndexes().map(i => i.name).join(", "));
print("tools:      " + db.tools.getIndexes().map(i => i.name).join(", "));
print("mcp:        " + db.mcp.getIndexes().map(i => i.name).join(", "));
