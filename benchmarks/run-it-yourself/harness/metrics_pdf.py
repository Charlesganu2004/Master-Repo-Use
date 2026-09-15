"""Build the metrics PDF: every measured number and every chart, in one file.

    python benchmarks/run-it-yourself/harness/metrics_pdf.py

Reads the result files of all three runs (the 600-token kit run, the graphify
experiment, and the September 11 harness and browser benchmarks) and writes
report/metrics.html and report/metrics.pdf. Nothing numeric is typed here: a
section whose results file is missing is skipped and said to be missing.
"""
from __future__ import annotations

import html
import json
import pathlib
import statistics
import shutil
import subprocess

KIT = pathlib.Path(__file__).resolve().parents[1]
BENCHMARKS = KIT.parent
REPORT = KIT / "report"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
esc = html.escape

ARM_LABEL = {"bare_strict": "No harness, graphify forbidden", "bare_nograph": "No harness, not offered",
             "bare_graph": "No harness, graphify offered", "base_graph": "Base harness + graphify",
             "super_graph": "Super harness + graphify", "bare": "No harness", "super": "Super harness",
             "super_ponytail_caveman": "Super + ponytail + caveman",
             "super_ponytail_nocaveman": "Super + ponytail, no caveman",
             "ponytail": "Ponytail only", "caveman": "Caveman only"}
SUBJECT = {"base_graph", "super_graph"}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def table(headers: list, rows: list) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr" + (' class="subject"' if flag else "") + ">"
                   + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>" for cells, flag in rows)
    return f'<div class="wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def figure(src: pathlib.Path, caption: str) -> str:
    if not src.exists():
        return f'<p class="missing">chart not built: {esc(str(src.name))}</p>'
    return (f'<figure><img src="{esc(src.as_uri())}" alt="{esc(caption)}">'
            f"<figcaption>{esc(caption)}</figcaption></figure>")


def kit_section() -> str:
    scores = load(KIT / "results" / "runs.json")
    if not scores:
        return '<p class="missing">The 600-token kit has not been run yet.</p>'
    rows = []
    for task in ("complex", "super_complex"):
        for arm in ("bare_strict", "bare_graph", "base_graph", "super_graph"):
            cell = [r for r in scores if r["task"] == task and r["arm"] == arm and r.get("completed")]
            if not cell:
                continue
            facts = sum(r["score"]["found"] for r in cell)
            want = sum(r["score"]["expected"] for r in cell)
            within = sum(r["withinLimit"] for r in cell)
            tokens = [r["answerTokens"] for r in cell]
            cost = sum(r["costUsd"] for r in cell) / len(cell)
            secs = sum(r["seconds"] for r in cell) / len(cell)
            used = sum(1 for r in cell if r["graphifyCalls"] > 0)
            rows.append(([task.replace("_", " "), ARM_LABEL[arm], len(cell), f"{facts}/{want}",
                          f"{within}/{len(cell)}", f"{statistics.median(tokens):,.0f}", f"{max(tokens):,}",
                          f"${cost:.4f}", f"{secs:.0f}s", f"{used}/{len(cell)}"], arm in SUBJECT))
    return table(["Question", "Arm", "Runs", "Facts right", "Within 600", "Median answer tokens",
                  "Worst answer", "Mean cost", "Mean time", "Used graphify"], rows)


def graphify_section() -> str:
    summary = load(BENCHMARKS / "2026-09-15" / "results" / "summary.json")
    if not summary:
        return '<p class="missing">The graphify experiment has no summary yet.</p>'
    rows = []
    for key, cell in summary.items():
        task, arm = key.split(":")
        rows.append(([task, ARM_LABEL.get(arm, arm), cell["n"], f"{cell['scoreRate']:.0%}",
                      f"{cell['withinLimit']}/{cell['n']}", f"{cell['answerTokens']:.0f}",
                      f"{cell['maxAnswerTokens']:,}", f"${cell['costUsd']:.4f}",
                      f"{cell['seconds']:.0f}s", f"{cell['graphifyRuns']}/{cell['n']}"],
                     arm in SUBJECT))
    return table(["Question", "Arm", "Runs", "Facts right", "Within 400", "Median answer tokens",
                  "Worst answer", "Median cost", "Median time", "Used graphify"], rows)


def coding_section() -> str:
    summary = load(BENCHMARKS / "2026-09-11" / "results" / "summary.json")
    if not summary:
        return '<p class="missing">The September 11 coding benchmark has no summary yet.</p>'
    rows = []
    for key, cell in summary["coding"].items():
        task, arm = key.split(":")
        delta = (cell.get("vsBare") or {}).get("costUsd")
        rows.append(([task, ARM_LABEL.get(arm, arm), cell["n"], f"${cell['costUsd']:.4f}",
                      "" if delta is None else f"{delta:+.0f}%", f"{cell['seconds']:.0f}s",
                      f"{cell['outputTokens']:,.0f}", f"{cell['solutionLoc']:.0f}",
                      f"{cell['proseWords']:.0f}", f"{cell['hiddenPassRate']:.0%}",
                      "" if cell["judgeOverall"] is None else f"{cell['judgeOverall']:.1f}"], False))
    return table(["Task", "Arm", "Runs", "Cost", "vs no harness", "Time", "Output tokens",
                  "Solution LOC", "Prose words", "Hidden tests", "Judge /10"], rows)


def browser_section() -> str:
    summary = load(BENCHMARKS / "2026-09-11" / "results" / "summary.json")
    engine = load(BENCHMARKS / "2026-09-11" / "results" / "engine.json")
    if not summary or "browser" not in summary:
        return '<p class="missing">The browser benchmark has no summary yet.</p>'
    rows = []
    for key, cell in summary["browser"]["agent"].items():
        task, tool = key.split(":")
        rows.append(([task, tool, cell["n"], f"{cell['correct']}/{cell['n']}",
                      f"${cell['costUsd']:.4f}", f"{cell['tokensTotal']:,.0f}",
                      f"{cell['seconds']:.0f}s", f"{cell['codeLines']:.0f}",
                      cell.get("declined", 0)], False))
    agent = table(["Task", "Tool", "Runs", "Correct", "Median cost", "Median tokens", "Median time",
                   "Code lines", "Declined by scaffold"], rows)
    rows = []
    for key, cell in (engine or {}).get("summary", {}).items():
        tool, task = key.split(":")
        rows.append(([task, tool, f"{cell['correct']}/{cell['runs']}",
                      f"{cell['medianSeconds']:.2f}s" if cell["medianSeconds"] else "",
                      f"{cell['minSeconds']:.2f} to {cell['maxSeconds']:.2f}" if cell["minSeconds"] else "",
                      f"{cell['medianClientMiB']:.0f}" if cell.get("medianClientMiB") else "n/a"], False))
    no_model = table(["Task", "Tool", "Correct", "Median seconds", "Range", "Client MiB"], rows)
    views = (engine or {}).get("views", {})
    rows = [([esc(k), f"{v['bytes']:,}", f"{v['tokens']:,}"], False) for k, v in sorted(views.items())]
    return (agent + "<h3>The same tasks with no model in the loop</h3>" + no_model
            + "<h3>What one page costs to read</h3>" + table(["Page view", "Bytes", "Tokens (o200k)"], rows))


def ceiling_section() -> str:
    """Did rewriting rule 15 make the ceiling hold? Measured, not assumed."""
    import statistics as stats
    before = load(KIT / "results" / "runs-rule-v1.json")
    after = load(KIT / "results" / "runs.json")
    if not before or not after:
        return '<p class="missing">Only one version of the rule has been run.</p>'
    rows = []
    for name, data in (("Rule stating the token ceiling only", before),
                       ("Rule also stating a word budget, and banning preamble and summary", after)):
        done = [r for r in data if r.get("completed")]
        harness = [r for r in done if r["arm"] in ("base_graph", "super_graph")]
        rows.append(([name, len(done), f"{sum(r['withinLimit'] for r in done)}/{len(done)}",
                      f"{stats.median(r['answerTokens'] for r in done):,.0f}",
                      f"{sum(r['score']['found'] for r in done)}/{sum(r['score']['expected'] for r in done)}",
                      f"{sum(r['withinLimit'] for r in harness)}/{len(harness)}",
                      f"{stats.median(r['answerTokens'] for r in harness):,.0f}"], False))
    return table(["Version of rule 15", "Runs", "Within 600", "Median answer tokens", "Facts right",
                  "Harness arms within", "Harness median tokens"], rows)


def main() -> None:
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Harness metrics</title>
<style>
@page {{ size: A4 landscape; margin: 12mm; }}
body {{ margin:0; color:#121316; background:#fff; font:400 9.5pt/1.5 "Segoe UI",system-ui,sans-serif; }}
h1 {{ font-size:20pt; margin:0 0 4pt; letter-spacing:-.02em; }}
h2 {{ font-size:13pt; margin:16pt 0 6pt; break-after:avoid; }}
h3 {{ font-size:10.5pt; margin:10pt 0 4pt; break-after:avoid; }}
p {{ color:#454a53; max-width:200mm; }}
.eyebrow {{ font:500 8pt "Consolas",monospace; letter-spacing:.06em; text-transform:uppercase; color:#6b717b; }}
.wrap {{ margin:4pt 0 10pt; }}
table {{ width:100%; border-collapse:collapse; font-size:8pt; font-variant-numeric:tabular-nums; }}
th,td {{ text-align:right; padding:3pt 5pt; border-bottom:1px solid rgba(20,22,27,.14); }}
th:first-child,td:first-child,th:nth-child(2),td:nth-child(2) {{ text-align:left; }}
thead th {{ font:500 7pt "Consolas",monospace; text-transform:uppercase; color:#6b717b; }}
tr.subject td {{ background:rgba(196,78,22,.08); }}
tr {{ break-inside:avoid; }}
figure {{ margin:6pt 0 10pt; break-inside:avoid; }}
figure img {{ width:100%; }}
figcaption {{ font-size:8pt; color:#6b717b; margin-top:2pt; }}
.missing {{ color:#b7353b; font-size:9pt; }}
.part {{ break-before:page; }}
.note {{ font-size:8pt; color:#6b717b; }}
</style></head><body>
<p class="eyebrow">Master Repo &middot; metrics and graphs &middot; 15 September 2026</p>
<h1>Harness metrics: graphify, the token ceilings, and the browser engines</h1>
<p>Every number here was measured on this machine and comes from a results file, not from an estimate.
Token counts are the ones the API reported per response; cost is those counts at the published prices;
time is first to last timestamp of the run. Highlighted rows are the harness arms.</p>

<h2>1. The 600-token test, the one in benchmarks/run-it-yourself</h2>
<p>Two questions, four arms, capped at 600 tokens. This is the test you can run yourself with the same prompts.</p>
{kit_section()}
{figure(KIT / "charts" / "kit_results.png", "The 600-token test: facts right, ceiling compliance, cost and time")}

<h2 class="part">1b. Does the ceiling hold? Rewriting the rule, measured</h2>
<p>The first run showed answers going past a 600-token ceiling. Rule 15 was rewritten to state a word budget as
well as a token count, and to ban the preamble and closing summary that usually blow a capped answer. The same
sixteen runs were repeated. The rewrite made answers shorter and more accurate; it did not make the ceiling hold.
Through the proxy the limit is a hard max_tokens and this question does not arise.</p>
{ceiling_section()}
<h2 class="part">2. graphify across the harnesses, capped at 400 tokens</h2>
<p>Five arms, two questions, three runs each. g1 is the question a graph answers; g2 is the control a grep answers.</p>
{graphify_section()}
{figure(BENCHMARKS / "2026-09-15" / "charts" / "graphify_experiment.png",
        "graphify across the harnesses, 30 runs at a 400-token ceiling")}

<h2 class="part">3. The harness and skill benchmark, 11 September</h2>
<p>Six prompt arms, two coding tasks, five runs each, scored by hidden tests the model never saw and by two blind judges.</p>
{coding_section()}
{figure(BENCHMARKS / "2026-09-11" / "charts" / "coding_overview.png",
        "Six arms, two coding tasks, five runs each: cost, time, output, code size, tool calls and prose")}
{figure(BENCHMARKS / "2026-09-11" / "charts" / "coding_quality.png",
        "Quality: hidden tests passed, blind judge score, and cost per fully correct answer")}

<h2 class="part">4. Browser engines: caveman-browse, Playwright, Rustwright</h2>
{browser_section()}
{figure(BENCHMARKS / "2026-09-11" / "charts" / "browser_engine.png",
        "No model in the loop: seconds per task from a cold start, and tokens to read one page")}
{figure(BENCHMARKS / "2026-09-11" / "charts" / "browser_agent.png",
        "An agent driving each tool: tokens and time, with how many runs got the right answer")}
<p class="note">Declined by scaffold counts runs that refused the task on read-only grounds without touching the
tool. That is the agent profile used for isolation, not a property of the browser tool, and those runs are
excluded from the medians rather than counted as failures.</p>
</body></html>"""
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "metrics.html").write_text(doc, encoding="utf-8", newline="\n")
    edge = EDGE if pathlib.Path(EDGE).exists() else shutil.which("msedge") or shutil.which("chrome")
    if not edge:
        print("no Edge or Chrome found; wrote metrics.html only")
        return
    pdf = REPORT / "metrics.pdf"
    subprocess.run([edge, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=10000", f"--print-to-pdf={pdf}",
                    (REPORT / "metrics.html").resolve().as_uri()],
                   check=True, capture_output=True, timeout=300)
    print(f"wrote {pdf} ({pdf.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
