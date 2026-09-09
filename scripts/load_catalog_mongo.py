#!/usr/bin/env python3
"""Load the catalog into MongoDB, create its indexes, and check they earn their keep.

Charles asked to see what the atlas index looks like backed by MongoDB. This is
the half that runs; designs/d32-mongo.html is the half you look at.

The useful part is --check, which runs with no server at all. An index is a claim
about the documents ("this field exists, on enough of them to be worth a btree")
and about the queries ("this one is served by that index"). Both claims can be
checked against the real catalog before anything is installed, and both are the
kind of claim that rots silently: a field renamed in build_atlas_data.py leaves an
index that is still created, still listed, and never used again.

So --check verifies, against atlas-data.json:
  every indexed field exists on the documents of that collection
  how many documents actually carry it, so a sparse index is a decision
  every query the interface makes is covered by an index prefix
  no index is redundant, meaning a prefix of another index on the same keys

What it will not do:
  It will not drop a collection it did not create. A reload replaces documents
  by _id and leaves anything else alone.
  It will not invent an _id. The catalog has natural ids and uses them, so a
  reload is idempotent rather than a second copy.

Usage:
    python scripts/load_catalog_mongo.py --check
    python scripts/load_catalog_mongo.py --explain
    python scripts/load_catalog_mongo.py --load
    python scripts/load_catalog_mongo.py --load --uri mongodb://127.0.0.1:27017 --db atlas
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys

from capability_definitions import read_owned_definition

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "atlas-data.json"
INDEX_FILE = ROOT / "scripts" / "catalog-indexes.js"

# Which payload key becomes which collection. The shaped family collections are
# payload is either metadata or presentation and has no query behind it.
COLLECTIONS = {
    "components": "components",
    "lanes": "lanes",
    "routes": "routes",
    "surfaces": "surfaces",
    "setupRecipes": "recipes",
}

_CREATE = re.compile(
    r"db\.(?P<coll>\w+)\.createIndex\(\s*(?P<keys>\{.*?\})\s*,\s*(?P<opts>\{.*?\})\s*\)",
    re.DOTALL)

# Boolean equality is supported by MongoDB partial indexes. $ne is not.
_PARTIAL_EQ = re.compile(r'partialFilterExpression:\s*\{\s*(\w+):\s*(true|false)\s*\}')

# The queries the atlas interface actually makes, written the way the code makes
# them. Each names the index that must serve it. A query with no index here is a
# collection scan somebody will not notice until the catalog doubles.
QUERIES = [
    ("components", "family_kind", ["family"],
     "Filter the map to one family, which is the first row of chips."),
    ("components", "family_kind", ["family", "kind"],
     "Family and kind together, the second row of chips. Served by the same "
     "index because a compound index answers its own prefix."),
    ("components", "lane_order", ["lane"],
     "Open one lane. The sort on order comes off the index rather than memory."),
    ("components", "by_recipe", ["setupRecipe"],
     "Everything that can actually be set up, which is what Build collects."),
    ("components", "component_search", ["$text"],
     "The search box, weighted so a name match outranks a description match."),
    ("lanes", "lane_family_size", ["family"],
     "Lanes grouped by family, largest first."),
    ("lanes", "lane_source", ["source"],
     "Follow a lane back to the file that produced it."),
    ("routes", "route_members", ["members"],
     "Which hybrid routes touch this component. Multikey over an array."),
    ("routes", "route_lanes", ["lanes"],
     "Which routes cross this lane."),
    ("surfaces", "surface_group_ram", ["group"],
     "The surface picker, one group at a time."),
    ("surfaces", "surface_group_ram", ["group", "minRamGb"],
     "Local models this machine can hold, which is the group plus a memory floor."),
    ("recipes", "recipe_ready", ["kind", "state"],
     "Recipes that are reviewed and ready on this platform."),
]


# --------------------------------------------------------------- the documents
#
# Charles asked what would actually be stored, so that someone can open MongoDB
# and find the skills, agents, tools and MCP servers there. Two tiers, and the
# difference between them is the whole answer:
#
#   local     Skills, hooks, harnesses and scripts this repository owns. The
#             document carries the FULL TEXT, because we wrote it and it is ours
#             to store. A skill in Mongo is the skill, not a link to it.
#
#   catalog   Third-party repositories the catalog points at. The document
#             carries the RECORD: slug, licence, health, scan verdict, the lane
#             that vouches for it. NOT the code.
#
# That second line is a decision, not a limitation. This repository deliberately
# does not vendor third-party source: install_catalog_skill.py refuses any slug
# that is not catalogued, never executes anything from a clone, and never
# overwrites a skill it did not install. Copying 300 repositories into a database
# would undo all of that and leave a stale copy nobody scans.

CATALOG_STATUS = ROOT / "docs" / "catalog-status.json"

# Which families become their own collection. Someone typing `show collections`
# should see the four things Charles named, not one bucket called components
# with a family field they have to know about first.
FAMILY_COLLECTIONS = {
    "skills": "skills",
    "agents": "agents",
    "tools": "tools",
    "mcp": "mcp",
}

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SLUG = re.compile(r"^[\w.-]+/[\w.-]+$")


def health_by_repo() -> dict:
    """Lifecycle and scan state per catalogued repository, keyed by slug."""
    if not CATALOG_STATUS.is_file():
        return {}
    data = json.loads(CATALOG_STATUS.read_text(encoding="utf-8"))
    out = {}
    for row in data.get("repos", []):
        out[row["repo"]] = {
            "status": row.get("status"),
            "license": row.get("license"),
            "pushedAt": row.get("pushed_at"),
            "ageDays": row.get("age_days"),
            "archived": bool(row.get("archived")),
            "deepScanned": bool(row.get("deep_scanned")),
            "critical": bool(row.get("critical")),
            "findings": row.get("findings") or [],
            "note": row.get("note") or "",
        }
    return out


def local_skill_bodies() -> dict:
    """Every SKILL.md this repository owns, by directory name.

    The body is stored whole. A skill is instructions, and instructions
    summarised are instructions broken, which is the same reason the no-compress
    guard exists.
    """
    out = {}
    source = ROOT / "skills"
    if not source.is_dir():
        return out
    for path in sorted(source.iterdir()):
        definition = path / "SKILL.md"
        if not path.is_dir() or not definition.is_file():
            continue
        raw = definition.read_bytes()
        text = raw.decode("utf-8")
        front = _FRONTMATTER.match(text.lstrip("\ufeff"))
        description, name = "", path.name
        if front:
            for line in front.group(1).splitlines():
                if line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                elif line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
        out[path.name] = {
            "skillName": name,
            "description": description,
            "path": str(definition.relative_to(ROOT)).replace("\\", "/"),
            "body": text,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return out


def catalog_slug_for(component: dict, lane: dict) -> str:
    """The owner/repo a catalogued component points at, or empty for a local one."""
    name = (component.get("name") or "").strip()
    owner = (component.get("owner") or "").strip()
    if owner and _SLUG.match(f"{owner}/{name}"):
        return f"{owner}/{name}"
    if _SLUG.match(name):
        return name
    return ""


def mongo_document(component: dict, lane: dict, health: dict, bodies: dict) -> dict:
    """One component as it would sit in MongoDB.

    _id is the natural id rather than an ObjectId, so a reload replaces a
    document instead of adding a second copy of it.
    """
    doc = {
        "_id": component["id"],
        "name": component["name"],
        "family": component["family"],
        "kind": component["kind"],
        "lane": component["lane"],
        "laneName": lane.get("name", ""),
        "detail": component.get("detail", ""),
        "origin": "catalog" if lane.get("catalog") else "local",
        "source": lane.get("source", ""),
        # The author's sequence within a lane. lane_order sorts on it, so leaving
        # it out made that index reference a field no document carried.
        "order": component.get("order", 0),
    }
    if component.get("sub"):
        doc["sub"] = component["sub"]
    if component.get("cmd"):
        doc["commands"] = component["cmd"]
    if component.get("setupRecipe"):
        doc["setupRecipe"] = component["setupRecipe"]
        doc["setupState"] = component.get("setupState", "")
    if component.get("routes"):
        doc["routes"] = component["routes"]
    if component.get("connects"):
        doc["connects"] = component["connects"]

    # Local definition: the whole thing. Matched on the directory name, the
    # component id, and the name declared in the skill's own frontmatter,
    # because the three disagree often enough to matter: caveman-compact is the
    # component, caveman-ultra-compact is the directory.
    body = (bodies.get(component["id"])
            or bodies.get(component.get("name", ""))
            or next((b for b in bodies.values()
                     if b["skillName"] in (component["id"], component.get("name"))), None))
    if body:
        doc["origin"] = "local"
        doc["definition"] = {
            "path": body["path"],
            "description": body["description"],
            "body": body["body"],
            "bytes": body["bytes"],
            "sha256": body["sha256"],
        }

    if component.get("definitionPath"):
        definition = read_owned_definition(ROOT, component["definitionPath"])
        if definition:
            doc["definition"] = definition
            doc["origin"] = "local"
            doc["role"] = component.get("role", "")

    # Catalogued entry: the record about it, never its code.
    slug = catalog_slug_for(component, lane)
    if slug:
        doc["slug"] = slug
        doc["url"] = f"https://github.com/{slug}"
        if slug in health:
            doc["health"] = health[slug]
    return doc


def mongo_documents(payload: dict) -> dict:
    """Every collection that would be created, with its documents."""
    lanes = {l["id"]: l for l in payload["lanes"]}
    health = health_by_repo()
    bodies = local_skill_bodies()

    collections = {name: [] for name in FAMILY_COLLECTIONS.values()}
    collections["components"] = []
    for component in payload["components"]:
        lane = lanes.get(component["lane"], {})
        doc = mongo_document(component, lane, health, bodies)
        collections["components"].append(doc)
        target = FAMILY_COLLECTIONS.get(component["family"])
        if target:
            collections[target].append(doc)

    # Any skill this repository owns that no component names still belongs in the
    # skills collection. Three of the fifteen were in exactly that position, and
    # a skill nobody can find in the database is the failure this whole
    # collection exists to prevent.
    claimed = {d.get("definition", {}).get("path") for d in collections["skills"]}
    for directory, body in sorted(bodies.items()):
        if body["path"] in claimed:
            continue
        collections["skills"].append({
            "_id": directory,
            "name": body["skillName"],
            "family": "skills",
            "kind": "capability",
            "lane": "sys-skills",
            "laneName": "Skills",
            "detail": body["description"],
            "origin": "local",
            "source": body["path"],
            "definition": {
                "path": body["path"],
                "description": body["description"],
                "body": body["body"],
                "bytes": body["bytes"],
                "sha256": body["sha256"],
            },
        })

    collections["lanes"] = [dict(l, _id=l["id"], isFileSource=l.get("source") != "runtime")
                            for l in payload["lanes"]]
    collections["routes"] = [dict(r, _id=r["id"]) for r in payload["routes"]]
    collections["surfaces"] = [dict(s, _id=s["id"]) for s in payload["surfaces"]]
    collections["recipes"] = [dict(r, _id=r["id"]) for r in payload["setupRecipes"]]
    return collections


def payload() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def validate_documents(collections: dict) -> list[str]:
    """Pre-upload schema and credential checks. Report locations, never values."""
    problems = []
    patterns = [r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
                r"sk-(?:proj-)?[A-Za-z0-9_-]{24,}", r"AKIA[0-9A-Z]{16}",
                r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
                r"mongodb(?:\+srv)?://[^\s:/<>]+:[^\s@<>]+@"]
    for name, docs in collections.items():
        ids = set()
        for position, doc in enumerate(docs):
            ident = doc.get("_id")
            if not isinstance(ident, str) or not ident or ident in ids:
                problems.append(f"{name}[{position}] has a missing or duplicate identifier")
            ids.add(str(ident))
            blob = json.dumps(doc)
            if any(re.search(pattern, blob) for pattern in patterns):
                problems.append(f"{name}[{position}] contains a possible credential; inspect locally")
    return problems


def parse_indexes() -> list[dict]:
    """Read the index definitions from the mongosh file rather than restating them."""
    text = INDEX_FILE.read_text(encoding="utf-8")
    out = []
    for match in _CREATE.finditer(text):
        keys_raw = " ".join(match.group("keys").split())
        opts = match.group("opts")
        name = re.search(r'name:\s*"([^"]+)"', opts)
        fields = re.findall(r'"([\w.]+)"\s*:|(\w+)\s*:', match.group("keys"))
        fields = [quoted or bare for quoted, bare in fields]
        out.append({
            "collection": match.group("coll"),
            "name": name.group(1) if name else "unnamed",
            "keys": keys_raw,
            "fields": fields,
            "unique": "unique: true" in opts,
            "sparse": "sparse: true" in opts,
            "text": '"text"' in keys_raw,
            "partial": re.search(_PARTIAL_EQ, opts),
        })
    return out


def field_value(doc: dict, field: str):
    """Walk a dotted path the way MongoDB does.

    health.status and definition.body are real index keys, and a flat doc.get on
    either returns None, so every nested index read as covering zero documents.
    """
    value = doc
    for part in field.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def field_coverage(docs: list[dict], field: str) -> int:
    return sum(1 for doc in docs if field_value(doc, field) not in (None, "", [], {}))


def collections_report() -> int:
    """Exactly what MongoDB would hold, measured rather than described.

    Charles asked what data would be sent so he can set the server up. The answer
    has to be a measurement, not a paragraph: how many documents, how many bytes,
    which carry full text and which carry only a record.
    """
    data = payload()
    cols = mongo_documents(data)
    order = ["skills", "agents", "tools", "mcp",
             "lanes", "routes", "surfaces", "recipes", "components"]

    print("Collections MongoDB would hold")
    print()
    print(f"{'collection':<13}{'docs':>6}{'bytes':>11}{'local':>7}{'catalog':>9}  full text")
    print("-" * 74)
    total_docs = total_bytes = 0
    for name in order:
        docs = cols[name]
        size = len(json.dumps(docs).encode("utf-8"))
        local = sum(1 for d in docs if d.get("origin") == "local")
        catalogued = sum(1 for d in docs if d.get("origin") == "catalog")
        bodies = sum(1 for d in docs if d.get("definition"))
        total_docs += len(docs)
        total_bytes += size
        print(f"{name:<13}{len(docs):>6}{size:>11,}{local:>7}{catalogued:>9}  "
              f"{bodies if bodies else '-'}")
    print("-" * 74)
    print(f"{'total':<13}{total_docs:>6}{total_bytes:>11,}")
    distinct = total_bytes - len(json.dumps(cols["components"]).encode("utf-8"))
    print()
    print("The family collections duplicate their matching component records.")
    print(f"Without components, these collections contain {distinct:,} JSON bytes.")
    print("This is a payload estimate, not BSON, index, backup or cluster storage usage.")

    print()
    print()
    print("What a LOCAL document carries")
    print()
    print("Things this repository owns. The full text is stored, because a skill is")
    print("instructions and instructions summarised are instructions broken, which")
    print("is the same reason the no-compress guard exists.")
    print()
    sample = next(d for d in cols["skills"] if d.get("definition"))
    shown = dict(sample)
    shown["definition"] = dict(shown["definition"])
    body = shown["definition"]["body"][:110].replace("\n", " ")
    shown["definition"]["body"] = f"{body} ... [{shown['definition']['bytes']} bytes in full]"
    print(json.dumps(shown, indent=2)[:1400])

    catalogued = next((d for d in cols["agents"] if d.get("health")), None)
    if catalogued:
        print()
        print("What a CATALOG document carries")
        print()
        print("Third-party repositories the catalog points at. The RECORD is stored,")
        print("never the code. This repository does not vendor third-party source:")
        print("install_catalog_skill.py refuses an uncatalogued slug, never runs")
        print("anything from a clone, and never overwrites a skill it did not install.")
        print("Copying 293 repositories into a database would undo all of that and")
        print("leave a stale copy nobody rescans.")
        print()
        print(json.dumps(catalogued, indent=2)[:1100])

    print()
    print()
    print("What is NOT sent")
    print()
    print("  load-time checks reject recognized credential patterns before connecting.")
    print("    Review owned definitions before upload; pattern scanning is not a guarantee.")
    print("  no third-party source code, for the reason above.")
    print("  no prompts, transcripts or activity. That is the monitor store, a")
    print("    separate database with a TTL, described in docs/CHAT-CODE-MONITOR.md.")
    print("  no personal histories or machine credentials. Authored definitions may name")
    print("    their owner and contain policy text; review these as private catalog data.")
    return 0


def check() -> int:
    """Every claim an index makes, checked against the real catalog. No server.

    Validated against mongo_documents rather than the raw payload, because those
    are the documents that get stored: skills, agents, tools and mcp are shaped
    here and have no payload key of their own, so checking the payload would skip
    exactly the four collections Charles asked for.
    """
    data = payload()
    stored = mongo_documents(data)
    indexes = parse_indexes()
    failures = validate_documents(stored)

    print(f"{'collection':<14}{'index':<20}{'keys':<34}{'coverage'}")
    print("-" * 82)
    for index in indexes:
        docs = stored.get(index["collection"])
        if docs is None:
            failures.append(f"{index['name']} indexes {index['collection']}, which is not loaded")
            continue
        if not docs:
            failures.append(f"{index['collection']} has no documents to index")
            continue

        marks = []
        for field in index["fields"]:
            covered = field_coverage(docs, field)
            if covered == 0:
                failures.append(
                    f"{index['name']} indexes {index['collection']}.{field}, which no "
                    f"document carries. The field was renamed or never existed.")
            marks.append(f"{field} {covered}/{len(docs)}")

        # A sparse index is a decision, so it has to match the data. Sparse over a
        # field every document carries wastes nothing but says something untrue;
        # dense over a field most documents lack stores a null per document.
        if index["fields"]:
            first = index["fields"][0]
            covered = field_coverage(docs, first)
            ratio = covered / len(docs)
            if index["sparse"] and ratio > 0.95:
                failures.append(f"{index['name']} is sparse but {first} is on "
                                f"{ratio:.0%} of documents; sparse says the opposite")
            if not index["sparse"] and not index["text"] and ratio < 0.5:
                failures.append(f"{index['name']} is dense but {first} is on only "
                                f"{ratio:.0%} of documents; it should be sparse")

        flags = " ".join(f for f, on in
                         (("unique", index["unique"]), ("sparse", index["sparse"]),
                          ("text", index["text"])) if on)
        print(f"{index['collection']:<14}{index['name']:<20}{index['keys'][:32]:<34}"
              f"{', '.join(marks)[:40]} {flags}")

    # A unique index is a claim that no two documents share the value.
    for index in indexes:
        if not index["unique"]:
            continue
        docs = stored.get(index["collection"], [])
        field = index["fields"][0]
        # A partial index only claims uniqueness over the documents it covers, so
        # the excluded value is dropped before counting duplicates. Without this
        # the fifteen runtime lanes read as a violation of a constraint that was
        # written specifically to exclude them.
        partial = index["partial"]
        values = [doc.get(field) for doc in docs if doc.get(field) is not None
                  and (not partial or doc.get(partial.group(1)) is (partial.group(2) == "true"))]
        if len(values) != len(set(values)):
            duplicates = len(values) - len(set(values))
            failures.append(f"{index['name']} is unique but {index['collection']}.{field} "
                            f"has {duplicates} duplicate value(s); the load would fail")

    # Redundancy: an index whose keys are a prefix of another on the same
    # collection is answered by that one and only costs writes.
    by_collection = {}
    for index in indexes:
        by_collection.setdefault(index["collection"], []).append(index)
    for collection, group in by_collection.items():
        for a in group:
            for b in group:
                if a is b or a["text"] or b["text"]:
                    continue
                if len(a["fields"]) < len(b["fields"]) and \
                        b["fields"][:len(a["fields"])] == a["fields"]:
                    failures.append(
                        f"{a['name']} is a prefix of {b['name']} on {collection}; "
                        f"{b['name']} already answers it")

    print()
    print(f"{'query':<46}{'served by':<20}covered")
    print("-" * 82)
    index_by_name = {i["name"]: i for i in indexes}
    for collection, index_name, fields, description in QUERIES:
        index = index_by_name.get(index_name)
        if not index:
            failures.append(f"a query claims {index_name}, which is not created")
            continue
        if index["collection"] != collection:
            failures.append(f"{index_name} is on {index['collection']}, not {collection}")
            continue
        if fields == ["$text"]:
            covered = index["text"]
        else:
            covered = index["fields"][:len(fields)] == fields
        if not covered:
            failures.append(f"{collection} query on {fields} is not a prefix of "
                            f"{index_name} ({index['fields']}), so it scans")
        print(f"{('.'.join([collection] + fields))[:44]:<46}{index_name:<20}"
              f"{'yes' if covered else 'NO'}")

    print()
    total = sum(len(docs) for docs in stored.values())
    print(f"{total} documents across {len(stored)} collections, "
          f"{len(indexes)} indexes, {len(QUERIES)} queries checked")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("every indexed field exists, every query is covered, no index is redundant")
    return 0


def explain() -> int:
    """What each query would do, printed as the plan rather than run.

    Written from the index definitions, so it stays true when they change. It is
    not output from a server and does not pretend to be: a real explain reports
    documents examined, and that number depends on the data in the server rather
    than on the definitions.
    """
    indexes = {i["name"]: i for i in parse_indexes()}
    data = payload()
    for collection, index_name, fields, description in QUERIES:
        index = indexes[index_name]
        source_key = next(k for k, v in COLLECTIONS.items() if v == collection)
        docs = len(data.get(source_key, []))
        stage = "IXSCAN" if not index["text"] else "TEXT"
        print(f"\ndb.{collection}.find({{{', '.join(fields)}}})")
        print(f"  {description}")
        print(f"  winningPlan: {stage} using {index_name} on {index['keys']}")
        print(f"  without it: COLLSCAN over {docs} documents")
    return 0


def load(uri: str, database: str) -> int:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", database):
        print("Invalid database name: use a letter followed by letters, digits, underscores or hyphens.", file=sys.stderr)
        return 2
    if not uri:
        print("Set MONGODB_URI in the backend environment first. No connection attempted.", file=sys.stderr)
        return 2
    data = payload()
    documents = mongo_documents(data)
    problems = validate_documents(documents)
    if problems:
        for problem in problems:
            print(f"UPLOAD REFUSED: {problem}", file=sys.stderr)
        return 2
    try:
        from pymongo import MongoClient, ReplaceOne
    except ImportError:
        print("pymongo is not installed in this Python environment.\n"
              "Install a reviewed version in the backend environment before loading.\n"
              "  python scripts/load_catalog_mongo.py --check   # needs neither",
              file=sys.stderr)
        return 2

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=4000)
    except Exception:
        print("Invalid MongoDB connection configuration. URI and details withheld.", file=sys.stderr)
        return 1
    try:
        client.admin.command("ping")
    except Exception:                      # connection errors can contain credentials
        client.close()
        print("MongoDB connection failed. Check backend credentials, TLS and network access. URI and server details withheld.", file=sys.stderr)
        return 1

    try:
        db = client[database]
        for name, docs in documents.items():
            if not docs:
                continue
            # Replace owned natural IDs, never drop collections. Use a dedicated
            # catalog database: same-ID edits belong in Git, not a conflicting DB copy.
            operations = [ReplaceOne({"_id": doc["_id"]}, doc, upsert=True) for doc in docs]
            result = db[name].bulk_write(operations, ordered=False)
            print(f"{name:<16}{result.upserted_count} inserted, {result.modified_count} updated, "
                  f"{db[name].count_documents({})} total")
    except Exception:
        print("Catalog write failed; some records may already be written. No collections were dropped. Fix backend permissions or connectivity and rerun. Server details withheld.", file=sys.stderr)
        return 1
    finally:
        client.close()

    print("\nNext: connect mongosh to the SAME approved cluster and database using a secure prompt, then run:")
    print("  load('scripts/catalog-indexes.js')")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--collections", action="store_true",
                        help="print exactly what would be stored, with counts and bytes")
    parser.add_argument("--check", action="store_true",
                        help="verify every index against the real catalog, offline")
    parser.add_argument("--explain", action="store_true",
                        help="print the plan each query would use")
    parser.add_argument("--load", action="store_true", help="load the catalog into MongoDB")
    parser.add_argument("--uri", default=os.environ.get("MONGODB_URI"),
                        help="Prefer MONGODB_URI: command-line credentials can enter shell history")
    parser.add_argument("--db", default="atlas")
    args = parser.parse_args()

    if args.collections:
        return collections_report()
    if args.check:
        return check()
    if args.explain:
        return explain()
    if args.load:
        return load(args.uri, args.db)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
