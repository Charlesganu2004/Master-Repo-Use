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
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "atlas-data.json"
INDEX_FILE = ROOT / "scripts" / "catalog-indexes.js"

# Which payload key becomes which collection. Only these five: the rest of the
# payload is either metadata or presentation and has no query behind it.
COLLECTIONS = {
    "components": "components",
    "lanes": "lanes",
    "routes": "routes",
    "surfaces": "surfaces",
    "setupRecipes": "setupRecipes",
}

_CREATE = re.compile(
    r"db\.(?P<coll>\w+)\.createIndex\(\s*(?P<keys>\{.*?\})\s*,\s*(?P<opts>\{.*?\})\s*\)",
    re.DOTALL)

# partialFilterExpression: { field: { $ne: "value" } }. Only the $ne form, which
# is the one used here: a partial index that EXCLUDES a sentinel value.
_PARTIAL_NE = re.compile(r'partialFilterExpression:\s*\{\s*(\w+):\s*\{\s*\$ne:\s*"([^"]+)"')

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
    ("setupRecipes", "recipe_ready", ["kind", "state"],
     "Recipes that are reviewed and ready on this platform."),
]


def payload() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def parse_indexes() -> list[dict]:
    """Read the index definitions from the mongosh file rather than restating them."""
    text = INDEX_FILE.read_text(encoding="utf-8")
    out = []
    for match in _CREATE.finditer(text):
        keys_raw = " ".join(match.group("keys").split())
        opts = match.group("opts")
        name = re.search(r'name:\s*"([^"]+)"', opts)
        fields = re.findall(r"(\w+)\s*:", match.group("keys"))
        out.append({
            "collection": match.group("coll"),
            "name": name.group(1) if name else "unnamed",
            "keys": keys_raw,
            "fields": fields,
            "unique": "unique: true" in opts,
            "sparse": "sparse: true" in opts,
            "text": '"text"' in keys_raw,
            "partial": re.search(_PARTIAL_NE, opts),
        })
    return out


def field_coverage(docs: list[dict], field: str) -> int:
    return sum(1 for doc in docs if doc.get(field) not in (None, "", [], {}))


def check() -> int:
    """Every claim an index makes, checked against the real catalog. No server."""
    data = payload()
    indexes = parse_indexes()
    failures = []

    print(f"{'collection':<14}{'index':<20}{'keys':<34}{'coverage'}")
    print("-" * 82)
    for index in indexes:
        source_key = next((k for k, v in COLLECTIONS.items() if v == index["collection"]), None)
        if source_key is None:
            failures.append(f"{index['name']} indexes {index['collection']}, which is not loaded")
            continue
        docs = data.get(source_key, [])
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
        source_key = next((k for k, v in COLLECTIONS.items() if v == index["collection"]), None)
        docs = data.get(source_key, [])
        field = index["fields"][0]
        # A partial index only claims uniqueness over the documents it covers, so
        # the excluded value is dropped before counting duplicates. Without this
        # the fifteen runtime lanes read as a violation of a constraint that was
        # written specifically to exclude them.
        excluded = index["partial"].group(2) if index["partial"] else None
        values = [doc.get(field) for doc in docs
                  if doc.get(field) is not None and doc.get(field) != excluded]
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
    total = sum(len(data.get(k, [])) for k in COLLECTIONS)
    print(f"{total} documents across {len(COLLECTIONS)} collections, "
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
    try:
        from pymongo import MongoClient, ReplaceOne
    except ImportError:
        print("pymongo is not installed. This machine has no MongoDB either, so "
              "the load has never been run here.\n"
              "  pip install pymongo\n"
              "  python scripts/load_catalog_mongo.py --check   # needs neither",
              file=sys.stderr)
        return 2

    data = payload()
    client = MongoClient(uri, serverSelectionTimeoutMS=4000)
    try:
        client.admin.command("ping")
    except Exception as exc:                      # noqa: BLE001
        print(f"no MongoDB at {uri}: {exc}", file=sys.stderr)
        return 1

    db = client[database]
    for key, name in COLLECTIONS.items():
        docs = data.get(key, [])
        if not docs:
            continue
        # Replace by natural id rather than dropping the collection. A reload is
        # then idempotent and never removes something added alongside it.
        operations = [ReplaceOne({"_id": doc["id"]}, dict(doc, _id=doc["id"]), upsert=True)
                      for doc in docs]
        result = db[name].bulk_write(operations, ordered=False)
        print(f"{name:<16}{result.upserted_count} inserted, {result.modified_count} updated, "
              f"{db[name].count_documents({})} total")

    print("\nnow create the indexes:")
    print(f"  mongosh {database} --file scripts/catalog-indexes.js")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="verify every index against the real catalog, offline")
    parser.add_argument("--explain", action="store_true",
                        help="print the plan each query would use")
    parser.add_argument("--load", action="store_true", help="load the catalog into MongoDB")
    parser.add_argument("--uri", default="mongodb://127.0.0.1:27017")
    parser.add_argument("--db", default="atlas")
    args = parser.parse_args()

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
