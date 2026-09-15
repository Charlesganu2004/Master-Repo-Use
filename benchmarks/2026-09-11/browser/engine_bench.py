"""Browser engines without a model: caveman-browse, Playwright, Rustwright.

Each tool does the same three tasks on the same local pages, from a cold start,
N times. Measured per run: wall time, whether the answer matches the key, and
the client's memory. Measured per tool: lines of code for the three tasks, and
the size of the page view an agent would have to read (bytes, and tokens by the
o200k_base counter caveman-browse's own README uses, so the two are comparable;
Claude's tokenizer differs, and the agent half of the benchmark reports
Claude's real counts).

Playwright and Rustwright run literally the same task functions: Rustwright is a
drop-in, so only the import changes. All three drive the same installed
Microsoft Edge, so the browser is held constant and the engine is what varies.

    BENCH_CAVEMAN_BROWSE=path/to/caveman-browse.exe \\
    python benchmarks/2026-09-11/browser/engine_bench.py --runs 5 --out results/engine.json
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import json
import os
import pathlib
import re
import statistics
import subprocess
import tempfile
import time

BENCH = pathlib.Path(__file__).resolve().parents[1]
ANSWERS = json.loads((BENCH / "fixtures" / "answers.json").read_text(encoding="utf-8"))
BASE = os.environ.get("BENCH_BASE", "http://localhost:8777/benchmarks/2026-09-11/fixtures")
EDGE = os.environ.get("BENCH_EDGE", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
CAVEMAN = os.environ.get("BENCH_CAVEMAN_BROWSE", "caveman-browse")
TASKS = ("lookup", "count", "checkout")
# Rustwright finds its browser through this variable; without it every run
# fails with "Could not find a Chromium executable", which is what the first
# run of this script recorded fifteen times.
os.environ.setdefault("RUSTWRIGHT_CHROMIUM", EDGE)


# --------------------------------------------------- Playwright-API tasks
# Shared, unchanged, by Playwright and Rustwright.
def api_lookup(page):
    page.goto(f"{BASE}/orders.html")
    row = page.locator("tbody tr", has_text=ANSWERS["lookup"]["order"])
    return row.locator("td").nth(4).inner_text()


def api_count(page):
    page.goto(f"{BASE}/orders.html")
    return str(page.evaluate("""() => [...document.querySelectorAll('tbody tr')].filter(r =>
        r.cells[3].textContent === 'Shipped' &&
        parseFloat(r.cells[4].textContent.replace(/[$,]/g, '')) > 500).length"""))


def api_checkout(page):
    data = ANSWERS["checkout"]["input"]
    page.goto(f"{BASE}/checkout.html")
    page.get_by_label("Full name").fill(data["name"])
    page.get_by_label("Email").fill(data["email"])
    page.get_by_label("Street address").fill(data["street"])
    page.get_by_label("City").fill(data["city"])
    page.get_by_label("Postcode").fill(data["postcode"])
    page.get_by_label("Shipping method").select_option(data["shipping"])
    page.get_by_label("Coupon code").fill(data["coupon"])
    page.get_by_label("I accept the terms").check()
    page.get_by_role("button", name="Place order").click()
    return page.locator("#confirmation").inner_text().rsplit(" ", 1)[-1]


API_TASKS = {"lookup": api_lookup, "count": api_count, "checkout": api_checkout}


def client_rss_mib() -> float:
    """This Python process plus any non-browser children (Playwright's node
    driver). The browser itself is the same Edge for every tool, so it is
    excluded: it would add the same weight to all three."""
    import psutil
    me = psutil.Process()
    total = me.memory_info().rss
    for child in me.children(recursive=True):
        try:
            if "msedge" not in child.name().lower():
                total += child.memory_info().rss
        except psutil.Error:
            pass
    return round(total / 2**20, 1)


def run_api(engine: str, task: str) -> dict:
    module = importlib.import_module(f"{engine}.sync_api")
    started = time.perf_counter()
    with module.sync_playwright() as p:
        kwargs = {"headless": True}
        if engine == "playwright":
            kwargs["channel"] = "msedge"
        browser = p.chromium.launch(**kwargs)
        launched = time.perf_counter()
        page = browser.new_page()
        answer = API_TASKS[task](page)
        rss = client_rss_mib()
        browser.close()
    return {"seconds": round(time.perf_counter() - started, 3),
            "launchSeconds": round(launched - started, 3), "answer": answer, "clientMiB": rss}


# ------------------------------------------------------ caveman-browse tasks
def cb(env: dict, *args: str) -> dict:
    out = subprocess.run([CAVEMAN, *args], env=env, capture_output=True, text=True,
                         encoding="utf-8", timeout=180).stdout
    return json.loads(out)


def cb_rows(view: str) -> list[list[str]]:
    rows, current = [], None
    for line in view.splitlines():
        stripped = line.strip()
        if stripped.startswith("row") and not stripped.startswith("rowgroup"):
            current = []
            rows.append(current)
        elif current is not None and stripped.startswith(("cell ", "[")) and ' cell "' in f" {stripped}":
            current.append(re.search(r'cell "(.*)"', stripped).group(1))
    return [r for r in rows if r]


def cb_lookup(env: dict) -> str:
    view = cb(env, "snapshot", f"{BASE}/orders.html")["uids"]
    for cells in cb_rows(view):
        if cells and cells[0] == ANSWERS["lookup"]["order"]:
            return cells[4]
    return ""


def cb_count(env: dict) -> str:
    view = cb(env, "snapshot", f"{BASE}/orders.html")["uids"]
    hits = [c for c in cb_rows(view)
            if len(c) >= 5 and c[3] == "Shipped" and float(c[4].strip("$").replace(",", "")) > 500]
    return str(len(hits))


def cb_checkout(env: dict) -> str:
    data = ANSWERS["checkout"]["input"]
    view = cb(env, "snapshot", f"{BASE}/checkout.html")["uids"]

    def uid(role: str, name: str) -> str:
        return re.search(rf'\[(u\w+)\] {role} "{re.escape(name)}"', view).group(1)

    for label, key in (("Full name", "name"), ("Email", "email"), ("Street address", "street"),
                       ("City", "city"), ("Postcode", "postcode"), ("Coupon code", "coupon")):
        cb(env, "act", uid("textbox", label), "type", data[key])
    cb(env, "act", uid("combobox", "Shipping method"), "select", data["shipping"])
    cb(env, "act", uid("checkbox", "I accept the terms"), "click")
    cb(env, "act", uid("button", "Place order"), "click")
    # The CLI's snapshot always navigates, which would reset the form, so the
    # result is read with eval, the tool's documented escape hatch.
    text = cb(env, "eval", "document.getElementById('confirmation').textContent")["result"]
    return text.rsplit(" ", 1)[-1]


CB_TASKS = {"lookup": cb_lookup, "count": cb_count, "checkout": cb_checkout}


def run_caveman(task: str, index: int) -> dict:
    # ignore_cleanup_errors: Edge can still hold its profile for a moment after
    # close, and on Windows the failed delete raised WinError 267 AFTER the task
    # had finished, throwing away a measured answer. Cleanup is not the result.
    with tempfile.TemporaryDirectory(prefix="cb-bench-", ignore_cleanup_errors=True) as home:
        env = dict(os.environ, CAVEMAN_HOME=home, CAVEMAN_BROWSE_CHROME=EDGE,
                   CAVEMAN_BROWSE_PORT=str(9600 + index))
        started = time.perf_counter()
        try:
            answer = CB_TASKS[task](env)
        finally:
            subprocess.run([CAVEMAN, "close"], env=env, capture_output=True, timeout=60)
        return {"seconds": round(time.perf_counter() - started, 3), "answer": answer,
                "clientMiB": None}


# ------------------------------------------------------------- page views
def page_views() -> dict:
    import tiktoken
    enc = tiktoken.get_encoding("o200k_base")
    measure = lambda text: {"bytes": len(text.encode("utf-8")), "tokens": len(enc.encode(text))}
    views = {}
    for engine in ("playwright", "rustwright"):
        module = importlib.import_module(f"{engine}.sync_api")
        with module.sync_playwright() as p:
            kwargs = {"headless": True, **({"channel": "msedge"} if engine == "playwright" else {})}
            browser = p.chromium.launch(**kwargs)
            page = browser.new_page()
            for name in ("orders", "checkout"):
                page.goto(f"{BASE}/{name}.html")
                views[f"{engine}:{name}:full"] = measure(page.locator("body").aria_snapshot())
            browser.close()
    with tempfile.TemporaryDirectory(prefix="cb-views-", ignore_cleanup_errors=True) as home:
        env = dict(os.environ, CAVEMAN_HOME=home, CAVEMAN_BROWSE_CHROME=EDGE,
                   CAVEMAN_BROWSE_PORT="9690")
        try:
            for name, query in (("orders", ANSWERS["lookup"]["order"]), ("checkout", "")):
                full = cb(env, "snapshot", f"{BASE}/{name}.html")
                views[f"caveman-browse:{name}:full"] = measure(full["uids"])
                if query:
                    narrowed = cb(env, "snapshot", f"{BASE}/{name}.html", query)
                    views[f"caveman-browse:{name}:query"] = measure(narrowed["uids"])
                interactive = cb(env, "snapshot", f"{BASE}/{name}.html", "-i")
                views[f"caveman-browse:{name}:interactive"] = measure(interactive["uids"])
        finally:
            subprocess.run([CAVEMAN, "close"], env=env, capture_output=True, timeout=60)
    return views


def loc(functions) -> int:
    lines = []
    for fn in functions:
        lines += [l for l in inspect.getsource(fn).splitlines()
                  if l.strip() and not l.strip().startswith("#")]
    return len(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    expected = {"lookup": ANSWERS["lookup"]["total"], "count": str(ANSWERS["count"]["count"]),
                "checkout": ANSWERS["checkout"]["code"]}
    runs = []
    for index in range(args.runs):
        # Interleaved by round, so a slow minute on the machine hits every tool.
        for task in TASKS:
            for tool in ("caveman-browse", "playwright", "rustwright"):
                try:
                    result = (run_caveman(task, index) if tool == "caveman-browse"
                              else run_api(tool, task))
                    result["correct"] = result["answer"] == expected[task]
                except Exception as error:
                    result = {"seconds": None, "answer": None, "correct": False,
                              "error": f"{type(error).__name__}: {error}"[:300]}
                runs.append({"tool": tool, "task": task, "round": index, **result})
                print(json.dumps(runs[-1]))
    summary = {}
    for tool in ("caveman-browse", "playwright", "rustwright"):
        for task in TASKS:
            rows = [r for r in runs if r["tool"] == tool and r["task"] == task]
            times = [r["seconds"] for r in rows if r["seconds"] is not None]
            mem = [r["clientMiB"] for r in rows if r.get("clientMiB")]
            summary[f"{tool}:{task}"] = {
                "medianSeconds": round(statistics.median(times), 3) if times else None,
                "minSeconds": min(times) if times else None,
                "maxSeconds": max(times) if times else None,
                "correct": sum(r["correct"] for r in rows), "runs": len(rows),
                "medianClientMiB": statistics.median(mem) if mem else None,
            }
    result = {
        "runs": runs, "summary": summary, "views": page_views(),
        "loc": {"caveman-browse": loc([cb, cb_rows, cb_lookup, cb_count, cb_checkout]),
                "playwright": loc([api_lookup, api_count, api_checkout]),
                "rustwright": loc([api_lookup, api_count, api_checkout])},
        "note": ("Rustwright runs the Playwright task functions unchanged; its LOC is "
                 "Playwright's by construction. caveman-browse LOC includes the snapshot "
                 "parsing a script needs, because its interface is a text view, not a DOM API."),
    }
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print(json.dumps(result["views"], indent=1))
    print(result["loc"])


if __name__ == "__main__":
    main()
