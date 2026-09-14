"""Local-only deterministic browser benchmark; never calls browser MCP tools."""
import argparse
import functools
import importlib
import importlib.metadata
import json
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .audit import digest, save
from .run import capture, isolated_env

FIXTURE = """<!doctype html><html lang="en"><meta charset="utf-8">
<title>Synthetic benchmark</title><h1>Orders</h1>
<label for="query">Find order</label><input id="query">
<button id="search" onclick="document.querySelector('#result').textContent =
document.querySelector('#query').value === 'ORD-077' ? 'ORD-077 shipped 1540' : 'Not found'">Search</button>
<output id="result" role="status">Ready</output>
<label for="name">Customer</label><input id="name">
<label for="shipping">Shipping</label><select id="shipping">
<option value="standard">Standard</option><option value="express">Express</option></select>
<button id="checkout" onclick="document.querySelector('#receipt').textContent =
document.querySelector('#name').value + ':' + document.querySelector('#shipping').value + ':confirmed'">Checkout</button>
<output id="receipt">Pending</output><table><caption>Deterministic orders</caption>
<thead><tr><th>ID</th><th>Status</th><th>Cents</th></tr></thead><tbody>ROWS</tbody></table></html>"""


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return


def run(output, chromium, caveman=None):
    work = output / "browser"
    work.mkdir(parents=True, exist_ok=True)
    page_html = FIXTURE.replace("ROWS", "".join(
        f"<tr><td>ORD-{i:03}</td><td>{'shipped' if i % 2 else 'pending'}</td><td>{i*20}</td></tr>"
        for i in range(1, 121)))
    (work / "index.html").write_text(page_html, encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(work)))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    rows = []
    browser_hash = digest(chromium.read_bytes())
    old_env = os.environ.copy()
    try:
        for engine in ("playwright", "rustwright"):
            env = isolated_env(work / engine)
            os.environ.update({k: v for k, v in env.items()
                               if k in ("TMP", "TEMP", "TMPDIR", "HOME", "USERPROFILE",
                                        "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME")})
            os.environ["RUSTWRIGHT_CHROMIUM"] = str(chromium)
            try:
                module = importlib.import_module(engine + ".sync_api")
                version = importlib.metadata.version(engine)
                started = time.perf_counter()
                with module.sync_playwright() as api:
                    browser = api.chromium.launch(executable_path=str(chromium), headless=True)
                    cold_seconds = time.perf_counter() - started
                    chromium_version = browser.version
                    page = browser.new_page()
                    for phase in ("cold-task", "warm-task"):
                        start = time.perf_counter()
                        page.goto(url)
                        page.locator("#query").fill("ORD-077")
                        page.locator("#search").click()
                        assert page.locator("#result").inner_text() == "ORD-077 shipped 1540"
                        page.locator("#name").fill("Synthetic Customer")
                        page.locator("#shipping").select_option("express")
                        page.locator("#checkout").click()
                        assert page.locator("#receipt").inner_text() == "Synthetic Customer:express:confirmed"
                        count = page.locator("tbody tr").count()
                        assert count == 120
                        elapsed = time.perf_counter() - start
                        representation_start = time.perf_counter()
                        try:
                            representation = page.locator("body").aria_snapshot()
                            representation_type = "native aria_snapshot"
                        except (AttributeError, NotImplementedError):
                            representation = page.locator("body").inner_text()
                            representation_type = "inner_text fallback; not native snapshot comparison"
                        representation_seconds = time.perf_counter() - representation_start
                        path = work / f"{engine}-{phase}-representation.txt"
                        path.write_text(representation, encoding="utf-8")
                        rows.append({"engine": engine, "interface": f"Python {engine}.sync_api",
                                     "version": version, "phase": phase, "elapsed_seconds": elapsed,
                                     "launch_seconds": cold_seconds,
                                     "chromium_executable": str(chromium),
                                     "chromium_sha256": browser_hash, "chromium_version": chromium_version,
                                     "assertions_passed": 3, "assertions_total": 3,
                                     "fixture_sha256": digest(page_html.encode()),
                                     "representation_kind": representation_type,
                                     "representation_seconds": representation_seconds,
                                     "representation_bytes": len(representation.encode()),
                                     "representation_path": str(path), "tokens": None,
                                     "tokenizer": None, "cost_usd": None,
                                     "limitations": "Rustwright alpha Chromium-only; Python interface, not MCP. Cold is process-cold, not OS-cache-cold."})
                    browser.close()
            except Exception as error:  # noqa: BLE001 - engine-specific failures are evidence
                rows.append({"engine": engine, "interface": f"Python {engine}.sync_api",
                             "blocker": str(error), "elapsed_seconds": None,
                             "chromium_executable": str(chromium), "chromium_sha256": browser_hash})
            finally:
                os.environ.clear()
                os.environ.update(old_env)
        if caveman:
            env = isolated_env(work / "caveman-browse")
            env["CAVEMAN_BROWSE_CHROME"] = str(chromium)
            raw = capture([str(caveman), "snapshot", url], work, env, 60)
            save(work / "caveman-probe.json", raw)
            close = capture([str(caveman), "close"], work, env, 30)
            save(work / "caveman-close.json", close)
            rows.append({"engine": "caveman-browse", "interface": "Go direct CLI snapshot",
                         "phase": "representation-probe", "raw": raw,
                         "representation_bytes": raw["stdout_bytes"],
                         "elapsed_seconds": None, "correctness": None,
                         "blocker": "CLI snapshot alone does not prove equal task actions; excluded from engine ranking.",
                         "chromium_executable": str(chromium), "tokens": None})
        else:
            rows.append({"engine": "caveman-browse", "interface": "Go direct CLI (not substituted)",
                         "elapsed_seconds": None, "blocker": "No verified local binary; see binary-audit.json",
                         "chromium_executable": str(chromium)})
    finally:
        os.environ.clear()
        os.environ.update(old_env)
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    save(output / "browser-runs.json", rows)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chromium", type=Path, required=True)
    parser.add_argument("--caveman", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.chromium, args.caveman)))
