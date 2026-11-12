"""LightRAG knowledge graph over the kb store. No language model, no embedding model.

Entities come from deterministic text rules (acronyms, multi-word proper terms,
headings); relations are co-occurrence within a chunk; vectors are signed
feature-hash vectors of stemmed words and bigrams. Callers pass keywords, so
LightRAG never needs an LLM at query time.
"""

import json
import math
import os
import re
import shutil
import time
import zlib
from collections import Counter
from pathlib import Path

import numpy as np

from kb_store import DIRTY, KB_HOME, STOP, all_chunks, lock, terms

os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(KB_HOME / "tiktoken"))

from lightrag import LightRAG, QueryParam  # noqa: E402
from lightrag.utils import EmbeddingFunc, compute_mdhash_id  # noqa: E402

import logging  # noqa: E402

for _name in ("lightrag", "nano-vectordb"):
    logging.getLogger(_name).setLevel(logging.WARNING)

GRAPH_DIR = KB_HOME / "lightrag"
BUILD_JSON = GRAPH_DIR / "build.json"
DIM = 256
SEP = "<SEP>"
WORD = re.compile(r"[a-z0-9]+")
ACRONYM = re.compile(r"\b[A-Z][A-Z0-9&]{1,9}\b")
PROPER = re.compile(r"\b[A-Z][a-z0-9]+(?:[ -][A-Z][a-z0-9]+){1,4}\b")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
SUFFIXES = (("ations", "at"), ("ation", "at"), ("ies", "y"), ("sses", "ss"), ("ing", ""), ("ed", ""), ("es", ""), ("s", ""))


def _stem(word: str) -> str:
    for suffix, repl in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)] + repl
    return word


def embed_text(text: str) -> np.ndarray:
    words = [_stem(w) for w in WORD.findall(text.lower()) if len(w) > 1 and w not in STOP]
    vec = np.zeros(DIM, dtype=np.float32)
    for feature, tf in Counter(words + [f"{a}_{b}" for a, b in zip(words, words[1:])]).items():
        h = zlib.crc32(feature.encode())
        vec[h % DIM] += (1.0 if (h >> 16) & 1 else -1.0) * (1.0 + math.log(tf))
    norm = float(np.linalg.norm(vec))
    return vec / norm if norm else vec


async def _embed(texts: list[str], **_) -> np.ndarray:
    return np.stack([embed_text(t) for t in texts]) if texts else np.zeros((0, DIM), dtype=np.float32)


async def _no_llm(*_, **__):
    raise RuntimeError("No language model is configured. Pass keywords to lightrag_query.")


def _make(workspace: str) -> LightRAG:
    return LightRAG(
        working_dir=str(GRAPH_DIR),
        workspace=workspace,
        embedding_func=EmbeddingFunc(embedding_dim=DIM, max_token_size=8192, func=_embed, model_name="hash-256"),
        llm_model_func=_no_llm,
        enable_llm_cache=False,
        vector_db_storage_cls_kwargs={"cosine_better_than_threshold": 0.05},
    )


def _entities(text: str, heading: str | None) -> tuple[Counter, list[str]]:
    found = Counter(m for m in ACRONYM.findall(text) if not m.isdigit())
    for match in PROPER.findall(text):
        words = match.replace("-", " ").split()
        while words and words[0].lower() in STOP:
            words.pop(0)
        if len(words) >= 2:
            found[" ".join(words)] += 1
    topics = [h.strip() for h in (heading or "").split(" > ") if h.strip() and not h.startswith("page ")]
    return found, topics


def _knowledge(chunks: list[dict]) -> tuple[dict, dict, dict]:
    text_chunks, entities, relations = {}, {}, {}
    for c in chunks:
        body = (c.get("body") or "").strip()
        if not body:
            continue
        path = c.get("path") or "memory"
        cid = compute_mdhash_id(body, prefix="chunk-")
        text_chunks[cid] = {"content": body, "full_doc_id": path, "file_path": path,
                            "chunk_order_index": int(c.get("idx") or 0), "tokens": len(body) // 4}
        found, topics = _entities(body, c.get("heading"))
        top = [name for name, _ in found.most_common(8)]
        sentences = SENTENCE.split(body)
        for name in dict.fromkeys(top + topics):
            e = entities.setdefault(name, {"type": "topic" if name in topics else ("acronym" if name.isupper() else "term"),
                                           "description": "", "sources": set(), "files": set()})
            if not e["description"]:
                e["description"] = next((s for s in sentences if name in s), body[:200]).strip()[:240]
            e["sources"].add(cid)
            e["files"].add(path)
        anchors = topics[-1:] or top[:1]
        pairs = [(a, b) for a in anchors for b in top if a != b] + list(zip(top, top[1:5]))
        for a, b in pairs:
            src, tgt = sorted((a, b))
            r = relations.setdefault((src, tgt), {"weight": 0.0, "sources": set(), "files": set(),
                                                  "where": c.get("heading") or Path(path).name})
            r["weight"] += 1.0
            r["sources"].add(cid)
            r["files"].add(path)
    return text_chunks, entities, relations


async def _write(rag: LightRAG, chunks: list[dict]) -> dict:
    text_chunks, entities, relations = _knowledge(chunks)
    now = int(time.time())
    if text_chunks:
        await rag.text_chunks.upsert(text_chunks)
        await rag.chunks_vdb.upsert(text_chunks)
    ent_vdb = {}
    for name, e in entities.items():
        data = {"entity_id": name, "entity_type": e["type"], "description": e["description"] or name,
                "source_id": SEP.join(sorted(e["sources"])), "file_path": SEP.join(sorted(e["files"])), "created_at": now}
        await rag.chunk_entity_relation_graph.upsert_node(name, node_data=data)
        ent_vdb[compute_mdhash_id(name, prefix="ent-")] = {"content": f"{name}\n{data['description']}", "entity_name": name,
                                                           "source_id": data["source_id"], "file_path": data["file_path"]}
    rel_vdb = {}
    for (src, tgt), r in relations.items():
        description = f"{src} and {tgt} appear together in {r['where']}"
        data = {"weight": r["weight"], "description": description, "keywords": "co-occurrence",
                "source_id": SEP.join(sorted(r["sources"])), "file_path": SEP.join(sorted(r["files"])), "created_at": now}
        await rag.chunk_entity_relation_graph.upsert_edge(src, tgt, edge_data=data)
        rel_vdb[compute_mdhash_id(src + tgt, prefix="rel-")] = {"src_id": src, "tgt_id": tgt, "source_id": data["source_id"],
                                                                "content": f"co-occurrence\t{src}\n{tgt}\n{description}",
                                                                "file_path": data["file_path"]}
    if ent_vdb:
        await rag.entities_vdb.upsert(ent_vdb)
    if rel_vdb:
        await rag.relationships_vdb.upsert(rel_vdb)
    for storage in (rag.text_chunks, rag.chunks_vdb, rag.entities_vdb, rag.relationships_vdb, rag.chunk_entity_relation_graph):
        await storage.index_done_callback()
    return {"chunks": len(text_chunks), "entities": len(entities), "relations": len(relations)}


def _build_info() -> dict:
    try:
        return json.loads(BUILD_JSON.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


async def rebuild() -> dict:
    """Rebuild the graph from every stored chunk and memory into a fresh workspace."""
    with lock("graph", timeout=300):
        started = time.time()
        workspace = f"b{int(started * 1000)}"
        rag = _make(workspace)
        await rag.initialize_storages()
        counts = await _write(rag, all_chunks())
        await rag.finalize_storages()
        info = {"workspace": workspace, "built": time.strftime("%Y-%m-%dT%H:%M:%S"), "seconds": round(time.time() - started, 2), **counts}
        BUILD_JSON.write_text(json.dumps(info), encoding="utf-8")
        DIRTY.unlink(missing_ok=True)
        for old in GRAPH_DIR.iterdir():
            if old.is_dir() and old.name != workspace:
                shutil.rmtree(old, ignore_errors=True)
        return info


_reader: tuple[str, LightRAG] | None = None


async def _current() -> LightRAG:
    global _reader
    if DIRTY.exists() or not BUILD_JSON.exists():
        await rebuild()
    workspace = _build_info()["workspace"]
    if _reader is None or _reader[0] != workspace:
        if _reader is not None:
            await _reader[1].finalize_storages()
        rag = _make(workspace)
        await rag.initialize_storages()
        _reader = (workspace, rag)
    return _reader[1]


def _short(text: str, n: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


async def query(question: str, keywords: list[str] | None = None, themes: list[str] | None = None,
                mode: str = "mix", top_k: int = 10, max_tokens: int = 2500) -> str:
    """Graph plus chunk context from LightRAG, within a token budget. Keywords default to the question's words."""
    rag = await _current()
    low = [k for k in (keywords or terms(question)[:8]) if k]
    high = [k for k in (themes or low[:4]) if k]
    param = QueryParam(mode=mode, only_need_context=True, ll_keywords=low, hl_keywords=high,
                       top_k=max(1, min(int(top_k), 40)), chunk_top_k=5, max_entity_tokens=1000,
                       max_relation_tokens=1000, max_total_tokens=8000, enable_rerank=False)
    data = (await rag.aquery_data(question, param)).get("data") or {}
    lines = []
    if data.get("entities"):
        lines.append("Entities:")
        lines += [f"- {e.get('entity_name')} ({e.get('entity_type')}): {_short(e.get('description'), 200)}" for e in data["entities"][:12]]
    if data.get("relationships"):
        lines.append("Relations:")
        lines += [f"- {r.get('src_id')} <-> {r.get('tgt_id')}: {_short(r.get('description'), 160)}" for r in data["relationships"][:12]]
    if data.get("chunks"):
        lines.append("Chunks:")
        lines += [f"[{i}] {c.get('file_path')}\n{_short(c.get('content'), 1200)}" for i, c in enumerate(data["chunks"][:5], 1)]
    out = "\n".join(lines) or "No graph matches. Try other keywords, or query_documents for exact words."
    return out[: max_tokens * 4]


def status() -> dict:
    info = _build_info()
    return {"graph": info or "not built yet", "pendingRebuild": DIRTY.exists()}
