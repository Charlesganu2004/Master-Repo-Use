"""Build the full report as HTML and print it to PDF with Microsoft Edge.

Every number in the tables comes from results/summary.json and the run files;
nothing numeric is typed here. The interpretation lives in report/narrative.json,
written after the results were read, so a conclusion cannot predate its data.

    python benchmarks/2026-09-11/harness/report.py

writes report/report.html and report/report.pdf.
"""
from __future__ import annotations

import html
import json
import pathlib
import subprocess

BENCH = pathlib.Path(__file__).resolve().parents[1]
REPORT = BENCH / "report"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

ARMS = ["bare", "super", "super_ponytail_caveman", "super_ponytail_nocaveman", "ponytail", "caveman"]
LABEL = {"bare": "No harness", "super": "Super harness", "super_ponytail_caveman": "Super + ponytail + caveman",
         "super_ponytail_nocaveman": "Super + ponytail, no caveman", "ponytail": "Ponytail only",
         "caveman": "Caveman only"}
TOOLS = ["caveman-browse", "playwright", "rustwright"]
BTASKS = ["lookup", "count", "checkout"]
esc = html.escape


def money(v):
    return "" if v is None else f"${v:.4f}"


def num(v, digits=0):
    if v is None:
        return ""
    return f"{v:,.{digits}f}" if isinstance(v, float) and digits else f"{v:,.0f}" if isinstance(v, (int, float)) else str(v)


def pct(v):
    return "" if v is None else f"{v:+.0f}%"


def rng(pair, fmt):
    lo, hi = pair or (None, None)
    return "" if lo is None else f"{fmt(lo)} to {fmt(hi)}"


def para(items):
    return "".join(f"<p>{text}</p>" for text in items)


def bullets(items):
    return "<ul>" + "".join(f"<li>{text}</li>" for text in items) + "</ul>"


def coding_table(summary, task):
    rows = []
    for arm in ARMS:
        c = summary["coding"].get(f"{task}:{arm}")
        if not c:
            continue
        base = summary["coding"].get(f"{task}:bare")
        added = (c["firstCallContext"] - base["firstCallContext"]) if base and c["firstCallContext"] else None
        rows.append(f"""<tr class="{'subject' if arm == 'super' else ''}"><td>{LABEL[arm]}</td>
<td>{num(summary['manifestContextBytes'][task][arm] / 1000, 1)}</td><td>{num(added)}</td>
<td>{money(c['costUsd'])}</td><td>{pct(c.get('vsBare', {}).get('costUsd'))}</td>
<td>{num(c['seconds'], 1)}</td><td>{num(c['outputTokens'])}</td><td>{num(c['solutionLoc'])}</td>
<td>{num(c['testLoc'])}</td><td>{num(c['toolCalls'])}</td><td>{num(c['proseWords'])}</td>
<td>{c['hiddenPassRate']:.0%}</td><td>{c['ownTestsGreen']}/{c['n']}</td>
<td>{'' if c['judgeOverall'] is None else f"{c['judgeOverall']:.2f}"}</td><td>{money(c['costPerCorrect'])}</td></tr>""")
    return f"""<div class="table-wrap"><table>
<thead><tr><th>Arm</th><th>Injected KB</th><th>Real tokens added</th><th>Cost</th><th>Cost vs none</th>
<th>Seconds</th><th>Output tokens</th><th>Solution LOC</th><th>Test LOC</th><th>Tool calls</th>
<th>Prose words</th><th>Hidden tests</th><th>Own tests green</th><th>Judge /10</th><th>Cost per correct</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def judge_table(summary):
    rows = []
    for arm in ARMS:
        cells = [summary["coding"].get(f"{t}:{arm}") for t in ("t1", "t2")]
        if not all(cells) or not cells[0]["judge"]:
            continue
        dims = ["correctness", "code_quality", "test_quality", "instruction_following", "communication"]
        avg = {d: (cells[0]["judge"][d] + cells[1]["judge"][d]) / 2 for d in dims}
        t2 = cells[1]
        note = "" if t2["threeSentenceNote"] is None else f"{t2['threeSentenceNote']:.0%}"
        unhandled = "" if t2["listsUnhandled"] is None else f"{t2['listsUnhandled']:.0%}"
        rows.append(f"<tr><td>{LABEL[arm]}</td>" + "".join(f"<td>{avg[d]:.2f}</td>" for d in dims)
                    + f"<td>{note}</td><td>{unhandled}</td></tr>")
    return f"""<div class="table-wrap"><table>
<thead><tr><th>Arm</th><th>Correctness</th><th>Code quality</th><th>Test quality</th><th>Instructions followed</th>
<th>Communication</th><th>T2 three-sentence note</th><th>T2 lists unhandled cases</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def browser_tables(summary):
    b = summary["browser"]
    agent_rows, engine_rows = [], []
    for task in BTASKS:
        for tool in TOOLS:
            c = b["agent"].get(f"{task}:{tool}")
            if c:
                agent_rows.append(f"<tr><td>{task}</td><td>{tool}</td><td>{c['correct']}/{c['n']}</td>"
                                  f"<td>{money(c['costUsd'])}</td><td>{num(c['tokensTotal'])}</td>"
                                  f"<td>{num(c['outputTokens'])}</td><td>{num(c['seconds'], 1)}</td>"
                                  f"<td>{num(c['toolCalls'])}</td><td>{num(c['codeLines'])}</td></tr>")
            e = b["engine"].get(f"{tool}:{task}")
            if e:
                engine_rows.append(f"<tr><td>{task}</td><td>{tool}</td><td>{e['correct']}/{e['runs']}</td>"
                                   f"<td>{num(e['medianSeconds'], 2)}</td>"
                                   f"<td>{num(e['minSeconds'], 2)} to {num(e['maxSeconds'], 2)}</td>"
                                   f"<td>{num(e['medianClientMiB'], 1) if e['medianClientMiB'] else 'n/a'}</td></tr>")
    views = "".join(f"<tr><td>{esc(k)}</td><td>{num(v['bytes'])}</td><td>{num(v['tokens'])}</td></tr>"
                    for k, v in sorted(b["views"].items()))
    loc = "".join(f"<tr><td>{tool}</td><td>{b['engineLoc'].get(tool, '')}</td></tr>" for tool in TOOLS)
    return f"""<h3>Agent in the loop</h3><div class="table-wrap"><table><thead><tr><th>Task</th><th>Tool</th>
<th>Correct</th><th>Cost</th><th>Tokens, all kinds</th><th>Output tokens</th><th>Seconds</th><th>Tool calls</th>
<th>Code lines written</th></tr></thead><tbody>{''.join(agent_rows)}</tbody></table></div>
<p class="note">Code lines written: lines of Python the agent ran for Playwright and Rustwright; for caveman-browse,
the number of CLI commands it ran, since its interface is commands rather than a script.</p>
<h3>No model: the same tasks as fixed scripts, cold start each time</h3><div class="table-wrap"><table><thead><tr><th>Task</th>
<th>Tool</th><th>Correct</th><th>Median s</th><th>Range s</th><th>Client memory MiB</th></tr></thead>
<tbody>{''.join(engine_rows)}</tbody></table></div>
<div class="two"><div class="table-wrap"><table><thead><tr><th>Page view</th><th>Bytes</th><th>Tokens (o200k)</th></tr></thead>
<tbody>{views}</tbody></table></div><div class="table-wrap"><table><thead><tr><th>Tool</th><th>Script LOC for the three tasks</th></tr></thead>
<tbody>{loc}</tbody></table></div></div>"""


GRAPHIFY_ARMS = ["bare_strict", "bare_nograph", "bare_graph", "base_graph", "super_graph"]
GRAPHIFY_LABELS = {"bare_strict": "No harness, graphify forbidden",
                   "bare_nograph": "No harness, not offered",
                   "bare_graph": "No harness, graphify offered",
                   "base_graph": "Base harness + graphify",
                   "super_graph": "Super harness + graphify"}


def graphify_table(summary: dict, tasks: dict) -> str:
    rows = []
    for task in ("g1", "g2"):
        rows.append(f'<tr class="divider"><td colspan="9">{task}: {esc(tasks["tasks"][task]["name"])}'
                    f'{" (a graph answers this; reading files does not)" if task == "g1" else " (one grep finds this)"}</td></tr>')
        for arm in GRAPHIFY_ARMS:
            c = summary.get(f"{task}:{arm}")
            if not c:
                continue
            subject = " class=\"subject\"" if arm in ("base_graph", "super_graph") else ""
            rows.append(
                f"<tr{subject}><td>{GRAPHIFY_LABELS[arm]}</td><td>{c['n']}</td>"
                f"<td>{c['scoreRate']:.0%}</td><td>{c['withinLimit']}/{c['n']}</td>"
                f"<td>{num(c['answerTokens'])}</td><td>{num(c['maxAnswerTokens'])}</td>"
                f"<td>{money(c['costUsd'])}</td><td>{num(c['seconds'], 1)}</td>"
                f"<td>{c['graphifyRuns']}/{c['n']}</td></tr>")
    return f"""<div class="table-wrap"><table><thead><tr><th>Arm</th><th>Runs</th><th>Facts correct</th>
<th>Within 400 tokens</th><th>Median answer tokens</th><th>Worst answer</th><th>Cost</th><th>Seconds</th>
<th>Used graphify</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>"""


def main() -> None:
    summary = json.loads((BENCH / "results" / "summary.json").read_text(encoding="utf-8"))
    narrative = json.loads((REPORT / "narrative.json").read_text(encoding="utf-8"))
    # The graphify experiment lives in its own dated folder; its summary is read
    # from there so this report never restates a number by hand.
    graphify_dir = BENCH.parent / "2026-09-15"
    graphify = json.loads((graphify_dir / "results" / "summary.json").read_text(encoding="utf-8"))
    graphify_tasks = json.loads((graphify_dir / "prompts" / "tasks.json").read_text(encoding="utf-8"))
    facts = json.loads((REPORT / "facts.json").read_text(encoding="utf-8"))
    coding = json.loads((BENCH / "prompts" / "coding.json").read_text(encoding="utf-8"))
    browser = json.loads((BENCH / "prompts" / "browser.json").read_text(encoding="utf-8"))
    path_svg = (REPORT / "assets" / "registry-path.svg").read_text(encoding="utf-8")
    arch_svg = (REPORT / "assets" / "registry-architecture.svg").read_text(encoding="utf-8")
    img = lambda name, alt: f'<figure><img src="../charts/{name}.png" alt="{esc(alt)}"><figcaption>{esc(alt)}</figcaption></figure>'

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Harness, Skills and Browser Benchmark</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap">
<style>
@page {{ size: A4; margin: 16mm 15mm 18mm; }}
:root {{ --ink:#121316; --ink2:#454a53; --ink3:#6b717b; --line:rgba(20,22,27,.14); --accent:#c44e16; --panel:#fbfaf7; --zone:rgba(20,22,27,.03); }}
* {{ box-sizing: border-box; }}
body {{ margin:0; color:var(--ink); background:#fff; font:400 10.5pt/1.55 "Geist","Segoe UI",system-ui,sans-serif; }}
h1 {{ font-size:26pt; line-height:1.1; margin:0 0 6pt; letter-spacing:-.02em; font-weight:650; }}
h2 {{ font-size:16pt; margin:22pt 0 8pt; letter-spacing:-.01em; font-weight:620; break-after:avoid; }}
h3 {{ font-size:11.5pt; margin:14pt 0 6pt; font-weight:620; break-after:avoid; }}
p, li {{ max-width:170mm; color:var(--ink2); }}
.part {{ break-before:page; }}
.eyebrow {{ font:500 8.5pt "Geist Mono",Consolas,monospace; letter-spacing:.06em; text-transform:uppercase; color:var(--ink3); }}
.lede {{ font-size:12pt; color:var(--ink2); }}
code, .mono {{ font-family:"Geist Mono",Consolas,monospace; font-size:.9em; }}
pre {{ font:8.5pt/1.5 "Geist Mono",Consolas,monospace; background:#f4f3f0; border:1px solid var(--line); border-radius:6px;
      padding:8pt 10pt; white-space:pre-wrap; overflow-wrap:anywhere; }}
.table-wrap {{ margin:6pt 0 10pt; }}
table {{ width:100%; border-collapse:collapse; font-size:8pt; font-variant-numeric:tabular-nums; break-inside:auto; }}
th, td {{ text-align:right; padding:3.5pt 4pt; border-bottom:1px solid var(--line); vertical-align:top; }}
th:first-child, td:first-child, th:nth-child(2):not(:last-child) {{ text-align:left; }}
thead th {{ font:500 7pt "Geist Mono",Consolas,monospace; text-transform:uppercase; letter-spacing:.04em; color:var(--ink3); }}
tr.subject td {{ background:rgba(196,78,22,.07); }}
tr {{ break-inside:avoid; }}
figure {{ margin:8pt 0 12pt; break-inside:avoid; }}
figure img {{ width:100%; }}
figcaption {{ font-size:8.5pt; color:var(--ink3); margin-top:3pt; }}
.note {{ font-size:8.5pt; color:var(--ink3); }}
.callout {{ border:1px solid var(--line); border-left:3px solid var(--accent); border-radius:6px; padding:8pt 12pt; margin:10pt 0; background:var(--panel); break-inside:avoid; }}
.callout p {{ margin:4pt 0; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:10pt; }}
.dg {{ width:100%; height:auto; font-family:"Geist","Segoe UI",sans-serif; }}
.dg .zone {{ fill:var(--zone); stroke:rgba(20,22,27,.26); stroke-width:1; }}
.dg .zone.untrusted {{ stroke-dasharray:6 4; }}
.dg .zlabel {{ font:500 10.5px "Geist Mono",monospace; letter-spacing:.08em; fill:var(--ink3); }}
.dg .box {{ fill:#fff; stroke:rgba(20,22,27,.3); stroke-width:1.2; }}
.dg .box.gate {{ stroke:var(--accent); stroke-width:2.2; }}
.dg .ghost {{ fill:none; stroke:var(--ink3); stroke-width:1.2; stroke-dasharray:4 4; }}
.dg .t {{ font-size:12.5px; font-weight:600; fill:var(--ink); }}
.dg .t.gate {{ fill:var(--accent); }}
.dg .s {{ font-size:10.5px; fill:var(--ink2); }}
.dg .g {{ font-size:11px; fill:var(--ink3); font-style:italic; }}
.dg .row {{ font-size:12px; font-weight:600; fill:var(--ink); }}
.dg .row2 {{ font-size:11px; fill:var(--ink3); }}
.dg .edge {{ fill:none; stroke:var(--ink3); stroke-width:1.4; }}
.dg .edge.dashed {{ stroke-dasharray:4 3; }}
.dg .lbl {{ font-size:10.5px; fill:var(--ink3); paint-order:stroke; stroke:#fff; stroke-width:4px; stroke-linejoin:round; }}
.dg .head {{ fill:var(--ink3); }}
</style></head><body>

<p class="eyebrow">Master Repo &middot; {esc(facts['date'])} &middot; commit {esc(facts['commit'])}</p>
<h1>Harness, Skills and Browser Benchmark</h1>
<p class="lede">{narrative['lede']}</p>
<div class="callout"><h3>The short version</h3>{bullets(narrative['summary'])}</div>
<h3>What was asked, and where each part is answered</h3>{bullets(narrative['asked'])}

<section class="part"><p class="eyebrow">Part A</p><h2>Super harness against no harness, and the skill combinations</h2>
<h3>How it was run</h3>{para(narrative['method'])}
{img('coding_overview', 'Six arms, two tasks, five runs each. Bars are medians; whiskers are the range across the five runs.')}
<h3>T1, the standard prompt: duration parser</h3>{coding_table(summary, 't1')}
<h3>T2, the slightly harder prompt: sliding-window rate limiter</h3>{coding_table(summary, 't2')}
<p class="note">Real tokens added is the first API call's full context for that arm minus the no-harness arm's, as Claude's own
tokenizer counted it. Hidden tests are the checks in hidden/, which no model saw. Own tests green counts runs whose own tests passed
when run against their own code. Judge is the mean of two blind Opus 5 judges per answer. Cost per correct is total cost divided by
answers that passed every hidden test.</p>
{img('coding_quality', 'Quality: hidden tests passed, blind judge score, and cost per fully correct answer.')}
{img('coding_efficiency', 'Quality against cost, per arm and task. Up and to the left is better.')}
<h3>Blind judge scores by dimension (mean of both tasks)</h3>{judge_table(summary)}
{img('coding_context', 'What each arm puts in front of the prompt: kilobytes injected, labelled with the real tokens added.')}
<h3>What the numbers say</h3>{bullets(narrative['coding_findings'])}
<h3>Super + ponytail + caveman against super + ponytail without caveman, and ponytail against caveman</h3>{bullets(narrative['combo_findings'])}
</section>

<section class="part"><p class="eyebrow">Part B</p><h2>caveman-browse against Playwright against Rustwright</h2>
{para(narrative['browser_method'])}
{img('browser_agent', 'An agent does each task with each tool: tokens and time, with how many of three runs got the right answer.')}
{img('browser_engine', 'Without a model: seconds per task from a cold start, and the tokens each tool needs to show the orders page.')}
{browser_tables(summary)}
<h3>What the numbers say</h3>{bullets(narrative['browser_findings'])}
</section>

<section class="part"><p class="eyebrow">Part C</p><h2>The prompts, so you can run it yourself</h2>
<h3>T1, the standard prompt</h3><pre>{esc(coding['tasks']['t1']['prompt'])}</pre>
<h3>T2, the slightly harder prompt</h3><pre>{esc(coding['tasks']['t2']['prompt'])}</pre>
<h3>Appended to every arm</h3><pre>{esc(coding['delivery'])}</pre>
<p>The bare, ponytail and caveman arms also get: <code>{esc(coding['no_skills'])}</code></p>
<h3>Browser tasks</h3><pre>{esc(chr(10).join(f"{k}: {v.replace('{BASE}', browser['base'])}" for k, v in browser['tasks'].items()))}</pre>
<h3>Reproduce</h3>{bullets(narrative['reproduce'])}
</section>

<section class="part"><p class="eyebrow">Part C2</p><h2>graphify: set up locally, then measured across the harnesses</h2>
{para(narrative['graphify_setup'])}
<figure><img src="../../2026-09-15/charts/graphify_experiment.png" alt="graphify experiment results">
<figcaption>Five arms, two codebase questions, three runs each, every answer capped at 400 tokens.</figcaption></figure>
{graphify_table(graphify, graphify_tasks)}
<h3>What the numbers say</h3>{bullets(narrative['graphify_findings'])}
</section>

<section class="part"><p class="eyebrow">Part D</p><h2>The super harness is on, and it works</h2>{bullets(narrative['verification'])}
<h3>/token limit</h3>{bullets(narrative['token_limit'])}
<h3>The + on every client surface</h3>{bullets(narrative['plus'])}
<h3>Skills as deep as their originals, and upstream tracking</h3>{bullets(narrative['skills'])}
</section>

<section class="part"><p class="eyebrow">Part E</p><h2>Moving skills, tools, plugins and MCP into a database: will it work?</h2>
{para(narrative['registry_answer'])}
<h3>Where the plan as written breaks</h3>{bullets(narrative['registry_flaws'])}
<figure>{path_svg}<figcaption>Your plan as written against the plan that works: the columns line up, and as written the path jumps
from the scan straight to publishing, over the column where a person should decide.</figcaption></figure>
<figure>{arch_svg}<figcaption>The architecture. Only the publisher writes to the registry, and only after your approval of the exact
digest; nothing in the dashed zone holds a secret. Clients pull the signed index and verify before installing.</figcaption></figure>
<h3>The plan</h3>{bullets(narrative['registry_plan'])}
<h3>Decisions that are yours</h3>{bullets(narrative['registry_decisions'])}
</section>

<section class="part"><p class="eyebrow">Part F</p><h2>Limits of this benchmark, what is blocked, and the files</h2>
<h3>Limits</h3>{bullets(narrative['limits'])}
<h3>Blocked</h3>{bullets(narrative['blocked'])}
<h3>Files</h3>{bullets(narrative['files'])}
</section>
</body></html>"""
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "report.html").write_text(doc, encoding="utf-8", newline="\n")
    pdf = REPORT / "report.pdf"
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=8000", f"--print-to-pdf={pdf}",
                    (REPORT / "report.html").resolve().as_uri()], check=True, capture_output=True, timeout=180)
    print(f"wrote {REPORT / 'report.html'} and {pdf} ({pdf.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
