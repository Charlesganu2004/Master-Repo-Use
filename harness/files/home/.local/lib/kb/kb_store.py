"""Tantivy (Rust) BM25 store for document chunks and chat memories, plus sync."""

import json
import os
import re
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

import tantivy

from kb_extract import SUPPORTED, chunk_sections, extract_sections

HOME = Path.home()
KB_HOME = Path(os.environ.get("KB_HOME", HOME / ".local" / "share" / "kb"))
BASE_DIR = Path(os.environ.get("BASE_DIR", HOME)).resolve()
INDEX_DIR = KB_HOME / "tantivy"
FILES_JSON = KB_HOME / "files.json"
JOBS_JSON = KB_HOME / "jobs.json"
DIRTY = KB_HOME / "graph.dirty"
MAX_FILE_BYTES = 50 * 1024 * 1024
SKIP_DIRS = {"node_modules", "AppData", "__pycache__", "graphify-out", "$RECYCLE.BIN", "venv"}
WORD = re.compile(r"[\w][\w.\-]*", re.UNICODE)
STOP = set(
    "a an and are as at be by can do does for from has have how i in is it its of on or should "
    "that the this to was what when where which who why will with".split()
)


def _schema() -> tantivy.Schema:
    b = tantivy.SchemaBuilder()
    b.add_text_field("uid", stored=True, tokenizer_name="raw")
    b.add_text_field("kind", stored=True, tokenizer_name="raw")
    b.add_text_field("path", stored=True, tokenizer_name="raw")
    b.add_text_field("path_lc", tokenizer_name="raw")
    b.add_integer_field("idx", stored=True, indexed=True, fast=True)
    b.add_text_field("heading", stored=True, tokenizer_name="en_stem")
    b.add_text_field("body", stored=True, tokenizer_name="en_stem")
    b.add_text_field("tags", stored=True, tokenizer_name="default")
    b.add_text_field("project", stored=True, tokenizer_name="raw")
    b.add_integer_field("created", stored=True, fast=True)
    return b.build()


SCHEMA = _schema()
_index = None


def index() -> tantivy.Index:
    global _index
    if _index is None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        _index = tantivy.Index(SCHEMA, path=str(INDEX_DIR), reuse=True)
    _index.reload()
    return _index


@contextmanager
def lock(name: str, timeout: float = 60.0):
    """Cross-process lock via an exclusive lock file (stale after 10 minutes)."""
    KB_HOME.mkdir(parents=True, exist_ok=True)
    path = KB_HOME / f"{name}.lock"
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime > 600:
                    path.unlink(missing_ok=True)
                    continue
            except FileNotFoundError:
                continue
            if time.time() > deadline:
                raise TimeoutError(f"{name} is busy in another process; try again shortly.")
            time.sleep(0.2)
    try:
        yield
    finally:
        os.close(fd)
        path.unlink(missing_ok=True)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, path)


def _inside_base(p: str) -> Path:
    path = Path(p).expanduser().resolve()
    if path != BASE_DIR and BASE_DIR not in path.parents:
        raise ValueError(f"{path} is outside BASE_DIR {BASE_DIR}")
    return path


def _writes(fn):
    """Run fn(writer) under the kb lock, commit, and mark the graph for rebuild."""
    with lock("index"):
        writer = index().writer(heap_size=20_000_000, num_threads=1)
        result = fn(writer)
        writer.commit()
        writer.wait_merging_threads()
        DIRTY.touch()
    index()
    return result


def _add_file(writer, path: Path) -> int:
    key = str(path).lower()
    writer.delete_documents_by_term("path_lc", key)
    chunks = chunk_sections(extract_sections(path))
    for i, c in enumerate(chunks):
        writer.add_document(tantivy.Document(
            uid=f"doc:{key}#{i}", kind="doc", path=str(path), path_lc=key, idx=i,
            heading=c["heading"] or "", body=c["text"], created=int(time.time()),
        ))
    return len(chunks)


def _walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in SKIP_DIRS]
        for name in filenames:
            if not name.startswith(("~$", ".")) and Path(name).suffix.lower() in SUPPORTED:
                yield Path(dirpath) / name


def sync(target: str | None = None) -> dict:
    """Index new or changed files under target (or re-check indexed files) and drop deleted ones."""
    record = {"jobId": f"sync_{uuid.uuid4().hex[:8]}", "state": "running", "path": None,
              "scanned": 0, "added": 0, "updated": 0, "unchanged": 0, "removed": 0, "failed": []}
    files = _read_json(FILES_JSON, {})
    if target:
        root = _inside_base(target)
        record["path"] = str(root)
        candidates = list(_walk(root)) if root.is_dir() else [root]
        scope = str(root).lower()
    else:
        candidates = [Path(v["path"]) for v in files.values()]
        scope = None

    todo = []
    for path in candidates:
        if not path.exists():
            continue
        record["scanned"] += 1
        st = path.stat()
        prev = files.get(str(path).lower())
        if st.st_size > MAX_FILE_BYTES:
            record["failed"].append({"file": str(path), "error": "larger than 50 MB"})
        elif prev and prev["mtime"] == st.st_mtime and prev["size"] == st.st_size:
            record["unchanged"] += 1
        else:
            todo.append((path, st, prev is not None))
    gone = [k for k, v in files.items()
            if (scope is None or k == scope or k.startswith(scope.rstrip("\\/") + os.sep))
            and not Path(v["path"]).exists()]

    if todo or gone:
        def apply(writer):
            for path, st, existed in todo:
                try:
                    n = _add_file(writer, path)
                    files[str(path).lower()] = {"path": str(path), "mtime": st.st_mtime, "size": st.st_size, "chunks": n}
                    record["updated" if existed else "added"] += 1
                except Exception as err:  # noqa: BLE001 - report per-file failures and continue
                    record["failed"].append({"file": str(path), "error": str(err)[:200]})
            for key in gone:
                writer.delete_documents_by_term("path_lc", key)
                files.pop(key, None)
                record["removed"] += 1

        _writes(apply)
        _write_json(FILES_JSON, files)

    record.update(state="succeeded", finishedAt=time.strftime("%Y-%m-%dT%H:%M:%S"))
    jobs = _read_json(JOBS_JSON, {})
    jobs[record["jobId"]] = record
    _write_json(JOBS_JSON, dict(list(jobs.items())[-50:]))
    return record


def job(job_id: str) -> dict:
    found = _read_json(JOBS_JSON, {}).get(job_id)
    if not found:
        raise ValueError(f"No sync job {job_id}")
    return found


def ingest_file(file_path: str) -> dict:
    path = _inside_base(file_path)
    if path.suffix.lower() not in SUPPORTED:
        raise ValueError(f"Unsupported type. Supported: {' '.join(sorted(SUPPORTED))}")
    files = _read_json(FILES_JSON, {})
    n = _writes(lambda w: _add_file(w, path))
    st = path.stat()
    files[str(path).lower()] = {"path": str(path), "mtime": st.st_mtime, "size": st.st_size, "chunks": n}
    _write_json(FILES_JSON, files)
    return {"file": str(path), "chunks": n}


def delete_file(file_path: str) -> dict:
    key = str(Path(file_path).expanduser().resolve()).lower()
    _writes(lambda w: w.delete_documents_by_term("path_lc", key))
    files = _read_json(FILES_JSON, {})
    files.pop(key, None)
    _write_json(FILES_JSON, files)
    return {"deleted": key}


def save_memory(text: str, tags: str = "", project: str = "") -> dict:
    if not text or not text.strip():
        raise ValueError("Memory text is required.")
    uid = f"mem:{uuid.uuid4().hex[:12]}"
    _writes(lambda w: w.add_document(tantivy.Document(
        uid=uid, kind="memory", path="memory", path_lc="memory", idx=0, heading=tags,
        body=text.strip(), tags=tags, project=project.lower(), created=int(time.time()),
    )))
    return {"saved": uid}


def delete_memory(uid: str) -> dict:
    _writes(lambda w: w.delete_documents_by_term("uid", uid))
    return {"deleted": uid}


def terms(text: str) -> list[str]:
    seen = []
    for w in WORD.findall(str(text or "").lower()):
        w = w.strip(".-_")
        if len(w) > 1 and w not in STOP and w not in seen:
            seen.append(w)
    return seen


def _hits(query, limit: int) -> list[dict]:
    searcher = index().searcher()
    out = []
    for score, address in searcher.search(query, limit).hits:
        d = searcher.doc(address).to_dict()
        out.append({k: (v[0] if isinstance(v, list) and v else v) for k, v in d.items()} | {"score": round(score, 3)})
    return out


def search(text: str, kind: str = "doc", limit: int = 5, scope: str | None = None, project: str | None = None) -> list[dict]:
    words = terms(text)
    if not words:
        return []
    parsed = index().parse_query_lenient(" ".join(words), ["body", "heading", "tags"], field_boosts={"heading": 0.6, "tags": 1.5})
    parsed = parsed[0] if isinstance(parsed, tuple) else parsed
    must = [(tantivy.Occur.Must, parsed), (tantivy.Occur.Must, tantivy.Query.term_query(SCHEMA, "kind", kind))]
    if scope:
        prefix = re.escape(str(Path(scope).expanduser().resolve()).lower())
        must.append((tantivy.Occur.Must, tantivy.Query.regex_query(SCHEMA, "path_lc", prefix + ".*")))
    if project:
        must.append((tantivy.Occur.Must, tantivy.Query.term_query(SCHEMA, "project", project.lower())))
    return _hits(tantivy.Query.boolean_query(must), max(1, min(int(limit or 5), 20)))


def neighbors(file_path: str, chunk_index: int, before: int = 1, after: int = 1) -> list[dict]:
    i = int(chunk_index)
    lo, hi = i - max(0, min(int(before), 5)), i + max(0, min(int(after), 5))
    key = str(Path(file_path).expanduser().resolve()).lower()
    q = tantivy.Query.boolean_query([
        (tantivy.Occur.Must, tantivy.Query.term_query(SCHEMA, "path_lc", key)),
        (tantivy.Occur.Must, tantivy.Query.range_query(SCHEMA, "idx", tantivy.FieldType.Integer, lo, hi)),
    ])
    return sorted(_hits(q, hi - lo + 1), key=lambda h: h["idx"])


def all_chunks() -> list[dict]:
    """Every stored doc chunk and memory, for graph rebuilds."""
    searcher = index().searcher()
    total = searcher.num_docs
    return _hits(tantivy.Query.all_query(), max(total, 1)) if total else []


def list_files(limit: int = 200) -> list[dict]:
    files = _read_json(FILES_JSON, {})
    return [{"path": v["path"], "chunks": v["chunks"]} for v in sorted(files.values(), key=lambda v: v["path"])][:limit]


def size_on_disk() -> int:
    return sum(f.stat().st_size for f in KB_HOME.rglob("*") if f.is_file())


def format_hits(hits: list[dict]) -> str:
    if not hits:
        return "No matches. Retry with other distinctive words or a synonym."
    lines = []
    for n, h in enumerate(hits, 1):
        where = "memory " + h.get("uid", "") if h.get("kind") == "memory" else f"{h.get('path')} #{h.get('idx')}"
        head = f" ({h['heading']})" if h.get("heading") else ""
        score = f" score {h['score']}" if "score" in h else ""
        lines.append(f"[{n}] {where}{head}{score}\n{h.get('body', '')}")
    return "\n\n".join(lines)
