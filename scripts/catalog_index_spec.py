#!/usr/bin/env python3
"""Parse scripts/catalog-indexes.js once, for everyone who needs to read it.

Two files parsed this independently and both got the same bug: a quoted dotted
key, `{ "health.status": 1 }`, matched no field, so every nested index reported
zero coverage and read as a prefix of everything else. It was found once, then
fixed twice, in build_atlas_data.py and in load_catalog_mongo.py separately.

A defect that has to be fixed in two places is duplication that costs something,
which is the only kind worth extracting. So the createIndex regex, the field
parser, the name extractor and the flag detection live here, and both callers
import them.

The mongosh file stays the source of truth. Nothing here restates an index; it
only reads what is already written there, so a new index appears everywhere at
once and a renamed one cannot leave a stale explanation attached to new keys.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX_FILE = ROOT / "scripts" / "catalog-indexes.js"

# db.<collection>.createIndex({ <keys> }, { <options> })
CREATE = re.compile(
    r"db\.(?P<coll>\w+)\.createIndex\(\s*(?P<keys>\{.*?\})\s*,\s*(?P<opts>\{.*?\})\s*\)",
    re.DOTALL)

# A key is either a bare identifier or a quoted path. The quoted form is the one
# that was missed: "health.status" and "definition.body" are real index keys and
# a bare \w+ pattern skips both.
KEY = re.compile(r'"([\w.]+)"\s*:|(\w+)\s*:')

NAME = re.compile(r'name:\s*"([^"]+)"')

# partialFilterExpression, and the operator list is short on purpose. MongoDB
# permits equality, $exists: true, $gt/$gte/$lt/$lte, $type, $and, $or, $in,
# $geoWithin and $geoIntersects, and NOTHING else. Checked against
# mongodb.com/docs/manual/core/index-partial on 2026-09-09.
#
# $ne is absent from that list, and lane_source was first written with
# { source: { $ne: "runtime" } }. The server would have rejected it at creation.
# The index now filters on a boolean the documents carry, which is an equality
# and therefore allowed.
PARTIAL = re.compile(r"partialFilterExpression:\s*\{(?P<body>[^}]*(?:\{[^}]*\}[^}]*)*)\}")

PARTIAL_BOOL = re.compile(r"(\w+):\s*(true|false)\s*\}?")

PARTIAL_ALLOWED = ("$exists", "$gt", "$gte", "$lt", "$lte", "$type",
                   "$and", "$or", "$in", "$geoWithin", "$geoIntersects")
PARTIAL_OPERATOR = re.compile(r"\$\w+")


def partial_filter(options: str):
    """The (field, value) a boolean partialFilterExpression selects on, or None.

    Returned rather than a bare flag because a unique index that is partial only
    claims uniqueness over the documents the filter covers, and the caller has to
    exclude the rest before counting duplicates.
    """
    found = PARTIAL.search(options)
    if not found:
        return None
    pair = PARTIAL_BOOL.search(found.group("body"))
    if not pair:
        return None
    return pair.group(1), pair.group(2) == "true"


def partial_problems(options: str) -> list[str]:
    """Operators used in a partialFilterExpression that MongoDB will refuse.

    The offline check validated an index against the file it was written in,
    which cannot catch an operator the server rejects. This is the rule the
    server applies, applied earlier.
    """
    found = PARTIAL.search(options)
    if not found:
        return []
    body = found.group("body")
    return sorted({op for op in PARTIAL_OPERATOR.findall(body)
                   if op not in PARTIAL_ALLOWED})

# Indexes over an array field, which MongoDB stores as multikey: one document
# with four members produces four index entries.
MULTIKEY = {"route_members", "route_lanes"}


def fields_in(keys: str) -> list[str]:
    """Every indexed field, in order, quoted paths included."""
    return [quoted or bare for quoted, bare in KEY.findall(keys)]


def parse(path: pathlib.Path | None = None) -> list[dict]:
    """Every createIndex call in the file, as the callers need it."""
    text = (path or INDEX_FILE).read_text(encoding="utf-8")
    out = []
    for match in CREATE.finditer(text):
        keys = " ".join(match.group("keys").split())
        opts = match.group("opts")
        name = NAME.search(opts)
        name = name.group(1) if name else "unnamed"
        out.append({
            "collection": match.group("coll"),
            "name": name,
            "keys": keys,
            "fields": fields_in(match.group("keys")),
            "unique": "unique: true" in opts,
            "sparse": "sparse: true" in opts,
            "partial": bool(PARTIAL.search(opts)),
            "partialFilter": partial_filter(opts),
            "partialProblems": partial_problems(opts),
            "text": '"text"' in keys,
            # A TTL index expires documents. Only the monitor store uses one:
            # the catalog is rewritten wholesale and nothing in it expires.
            "ttl": "expireAfterSeconds" in opts,
            "multikey": name in MULTIKEY,
        })
    return out


def value_at(document: dict, field: str):
    """Walk a dotted path the way MongoDB does.

    health.status and definition.body are real index keys, and a flat
    document.get on either returns None, so every nested index would read as
    covering zero documents. Same root cause as the parser bug above.
    """
    value = document
    for part in field.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def coverage(documents: list[dict], field: str) -> int:
    """How many documents actually carry this field."""
    return sum(1 for doc in documents
               if value_at(doc, field) not in (None, "", [], {}))


if __name__ == "__main__":
    for index in parse():
        flags = " ".join(f for f in ("unique", "sparse", "text", "multikey")
                         if index[f]) or "-"
        print(f"{index['collection']:<14}{index['name']:<20}{index['keys'][:34]:<36}{flags}")
