"""Local knowledge base for coding agents: tantivy (Rust) BM25 search, chat memory,
and a model-free LightRAG graph. Everything stays on this machine.

CLI: query | read-neighbors | sync | ingest | delete | list | status |
     memory-save | memory-search | memory-delete | graph-query | graph-rebuild | mcp
"""

import argparse
import asyncio
import json
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
for name in ("lightrag", "nano-vectordb"):
    logging.getLogger(name).setLevel(logging.WARNING)

import tantivy  # noqa: E402

import kb_graph  # noqa: E402
import kb_store as store  # noqa: E402


def status() -> dict:
    searcher = store.index().searcher()
    memories = searcher.search(tantivy.Query.term_query(store.SCHEMA, "kind", "memory"), 1, count=True).count
    return {
        "documentCount": len(store.list_files(10**9)),
        "chunkCount": searcher.num_docs - memories,
        "memoryCount": memories,
        "search": "tantivy (Rust) BM25 with English stemming",
        "graph": kb_graph.status(),
        "embeddings": "word-hash vectors (no model, nothing downloaded)",
        "diskBytes": store.size_on_disk(),
        "home": str(store.KB_HOME),
        "baseDir": str(store.BASE_DIR),
    }


def serve() -> None:
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("local-rag")

    @mcp.tool()
    def query_documents(query: str, limit: int = 5, scope: str | None = None) -> str:
        """Keyword search (BM25 with stemming) over indexed documents. Use the distinctive words the
        document would contain; retry with a synonym if nothing matches. Returns ranked chunks."""
        return store.format_hits(store.search(query, "doc", limit, scope))

    @mcp.tool()
    def read_chunk_neighbors(filePath: str, chunkIndex: int, before: int = 1, after: int = 1) -> str:
        """Read the chunks around a search hit when its text lacks context."""
        return store.format_hits(store.neighbors(filePath, chunkIndex, before, after))

    @mcp.tool()
    async def lightrag_query(query: str, keywords: list[str] | None = None, themes: list[str] | None = None,
                             mode: str = "mix", topK: int = 10, maxTokens: int = 2500) -> str:
        """LightRAG graph retrieval: related entities, their relations, and source chunks, within maxTokens.
        Pass keywords (specific names, terms, codes) and themes (broader topics); mode is mix, local,
        global, hybrid or naive. Use it to explore how topics connect across documents and memories."""
        return await kb_graph.query(query, keywords, themes, mode, topK, maxTokens)

    @mcp.tool()
    def memory_save(text: str, tags: str = "", project: str = "") -> str:
        """Save a short fact, decision or result from this chat for later sessions. Keep it to a few
        sentences; tags are space-separated words; project is the repository path or name."""
        return json.dumps(store.save_memory(text, tags, project))

    @mcp.tool()
    def memory_search(query: str, limit: int = 5, project: str | None = None) -> str:
        """Search saved chat memories (BM25). Use at the start of a task instead of re-reading old chats."""
        return store.format_hits(store.search(query, "memory", limit, None, project))

    @mcp.tool()
    def memory_delete(memoryId: str) -> str:
        """Delete one saved memory by its id (mem:...)."""
        return json.dumps(store.delete_memory(memoryId))

    @mcp.tool()
    def sync_start(path: str | None = None) -> str:
        """Index new and changed files (PDF, DOCX, MD, TXT, RST, CSV, LOG) under an absolute path inside
        BASE_DIR and drop deleted ones. Without a path, re-checks indexed files. Returns the job record."""
        return json.dumps(store.sync(path))

    @mcp.tool()
    def sync_status(jobId: str) -> str:
        """Get the record of a sync job by its jobId."""
        return json.dumps(store.job(jobId))

    @mcp.tool()
    def ingest_file(filePath: str) -> str:
        """Index or re-index one file by absolute path."""
        return json.dumps(store.ingest_file(filePath))

    @mcp.tool()
    def delete_file(filePath: str) -> str:
        """Remove one file from the index."""
        return json.dumps(store.delete_file(filePath))

    @mcp.tool()
    def list_files() -> str:
        """List indexed files with their chunk counts (first 200)."""
        return json.dumps(store.list_files())

    @mcp.tool(name="status")
    def status_tool() -> str:
        """Counts, search engine, graph build state, disk use, and paths."""
        return json.dumps(status())

    mcp.run()


_loop: asyncio.AbstractEventLoop | None = None


def _run(coro):
    """Run LightRAG coroutines on one long-lived loop so its storages stay bound to it."""
    global _loop
    if _loop is None:
        _loop = asyncio.new_event_loop()
    return _loop.run_until_complete(coro)


def _shutdown() -> None:
    """Stop LightRAG's background workers before the CLI exits."""
    if _loop is None or _loop.is_closed():
        return
    pending = [t for t in asyncio.all_tasks(_loop) if not t.done()]
    for task in pending:
        task.cancel()
    if pending:
        _loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    _loop.run_until_complete(_loop.shutdown_asyncgens())
    _loop.close()


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="kb", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("query"); q.add_argument("words", nargs="+"); q.add_argument("--limit", type=int, default=5); q.add_argument("--scope")
    n = sub.add_parser("read-neighbors"); n.add_argument("--file-path", required=True); n.add_argument("--chunk-index", type=int, required=True)
    n.add_argument("--before", type=int, default=1); n.add_argument("--after", type=int, default=1)
    s = sub.add_parser("sync"); s.add_argument("path", nargs="?")
    sub.add_parser("ingest").add_argument("file")
    sub.add_parser("delete").add_argument("file")
    sub.add_parser("list"); sub.add_parser("status"); sub.add_parser("graph-rebuild"); sub.add_parser("mcp")
    ms = sub.add_parser("memory-save"); ms.add_argument("text"); ms.add_argument("--tags", default=""); ms.add_argument("--project", default="")
    mq = sub.add_parser("memory-search"); mq.add_argument("words", nargs="+"); mq.add_argument("--limit", type=int, default=5); mq.add_argument("--project")
    sub.add_parser("memory-delete").add_argument("id")
    g = sub.add_parser("graph-query"); g.add_argument("words", nargs="+"); g.add_argument("--keywords", default=""); g.add_argument("--themes", default="")
    g.add_argument("--mode", default="mix"); g.add_argument("--top-k", type=int, default=10); g.add_argument("--max-tokens", type=int, default=2500)
    a = p.parse_args(argv)

    split = lambda s: [x.strip() for x in s.split(",") if x.strip()] or None  # noqa: E731
    commands = {
        "query": lambda: store.format_hits(store.search(" ".join(a.words), "doc", a.limit, a.scope)),
        "read-neighbors": lambda: store.format_hits(store.neighbors(a.file_path, a.chunk_index, a.before, a.after)),
        "sync": lambda: store.sync(a.path),
        "ingest": lambda: store.ingest_file(a.file),
        "delete": lambda: store.delete_file(a.file),
        "list": store.list_files,
        "status": status,
        "memory-save": lambda: store.save_memory(a.text, a.tags, a.project),
        "memory-search": lambda: store.format_hits(store.search(" ".join(a.words), "memory", a.limit, None, a.project)),
        "memory-delete": lambda: store.delete_memory(a.id),
        "graph-query": lambda: _run(kb_graph.query(" ".join(a.words), split(a.keywords), split(a.themes), a.mode, a.top_k, a.max_tokens)),
        "graph-rebuild": lambda: _run(kb_graph.rebuild()),
    }
    if a.cmd == "mcp":
        serve()
        return 0
    try:
        out = commands[a.cmd]()
    except Exception as err:  # noqa: BLE001 - CLI reports one clean line
        print(f"{type(err).__name__}: {err}", file=sys.stderr)
        return 1
    finally:
        _shutdown()
    print(out if isinstance(out, str) else json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
