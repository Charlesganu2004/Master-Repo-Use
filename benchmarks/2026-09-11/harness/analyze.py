"""Aggregate the collected runs and draw the charts.

Medians, not means: five runs per cell is enough to see a direction and not
enough for a mean to survive one slow run. Every chart shows the range as well,
so a difference inside the spread is visibly inside it.

    python benchmarks/2026-09-11/harness/analyze.py

reads results/coding-runs.json, results/browser-runs.json, results/engine.json
and arms/manifest.json; writes results/summary.json and charts/*.png|svg.
"""
from __future__ import annotations

import json
import pathlib
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BENCH = pathlib.Path(__file__).resolve().parents[1]
RESULTS = BENCH / "results"
CHARTS = BENCH / "charts"

ARMS = ["bare", "super", "super_ponytail_caveman", "super_ponytail_nocaveman", "ponytail", "caveman"]
LABELS = {"bare": "No harness", "super": "Super harness", "super_ponytail_caveman": "Super + ponytail\n+ caveman",
          "super_ponytail_nocaveman": "Super + ponytail\nno caveman", "ponytail": "Ponytail", "caveman": "Caveman"}
FLAT = {k: v.replace("\n", " ") for k, v in LABELS.items()}
COLORS = {"bare": "#3b3f46", "super": "#c44e16", "super_ponytail_caveman": "#e39a6f",
          "super_ponytail_nocaveman": "#8a3f1e", "ponytail": "#4f7a8a", "caveman": "#8f8a4b"}
TOOLS = ["caveman-browse", "playwright", "rustwright"]
TOOL_COLORS = {"caveman-browse": "#8f8a4b", "playwright": "#2f6f9f", "rustwright": "#b5542a"}
TASK_NAMES = {"t1": "T1 duration parser", "t2": "T2 rate limiter (harder)"}
BTASKS = ["lookup", "count", "checkout"]

INK, INK2, GRID, GROUND = "#121316", "#454a53", "#d9d6cf", "#fbfaf7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 10, "axes.edgecolor": "#b9b5ad",
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 11, "figure.facecolor": GROUND,
    "axes.facecolor": GROUND, "savefig.facecolor": GROUND, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
})


def med(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def span(values):
    values = [v for v in values if v is not None]
    return (min(values), max(values)) if values else (None, None)


# ------------------------------------------------------------ aggregation
def summarize_coding(rows: list[dict]) -> dict:
    out = {}
    for task in ("t1", "t2"):
        for arm in ARMS:
            cell = [r for r in rows if r["task"] == task and r["arm"] == arm]
            if not cell:
                continue
            full = [r for r in cell if r["hidden"].get("total") and r["hidden"]["passed"] == r["hidden"]["total"]]
            cost = [r["costUsd"] for r in cell]
            judge = [r["judgeMean"].get("overall") for r in cell if r["judgeMean"]]
            flags = [j for r in cell for j in r["judges"] if j]
            metric = lambda key: [r[key] for r in cell]
            out[f"{task}:{arm}"] = {
                "task": task, "arm": arm, "n": len(cell),
                "promptVerified": all(r["promptVerified"] for r in cell),
                "costUsd": med(cost), "costRange": span(cost), "costTotal": round(sum(c or 0 for c in cost), 4),
                "seconds": med(metric("seconds")), "secondsRange": span(metric("seconds")),
                "tokensTotal": med(metric("tokensTotal")),
                "outputTokens": med([r["tokens"]["output"] for r in cell]),
                "outputRange": span([r["tokens"]["output"] for r in cell]),
                "cacheRead": med([r["tokens"]["read"] for r in cell]),
                "cacheWrite": med([r["tokens"]["cw5m"] + r["tokens"]["cw1h"] for r in cell]),
                "inputFresh": med([r["tokens"]["input"] for r in cell]),
                "firstCallContext": med(metric("firstCallContext")),
                "apiCalls": med(metric("apiCalls")), "toolCalls": med(metric("toolCalls")),
                "toolRange": span(metric("toolCalls")),
                "skillCalls": sum(metric("skillCalls")), "fileToolCalls": sum(metric("fileToolCalls")),
                "solutionLoc": med(metric("solutionLoc")), "locRange": span(metric("solutionLoc")),
                "testLoc": med(metric("testLoc")),
                "proseWords": med(metric("proseWords")), "proseRange": span(metric("proseWords")),
                "emDashes": sum(metric("emDashes")),
                "hiddenPassRate": round(sum(r["hidden"].get("passed", 0) for r in cell)
                                        / max(1, sum(r["hidden"].get("total") or 0 for r in cell)), 4),
                "fullyCorrect": len(full),
                "ownTestsGreen": sum(1 for r in cell if r["ownTests"].get("ran") and r["ownTests"].get("exit") == 0),
                "judgeOverall": round(statistics.mean(judge), 2) if judge else None,
                "judgeRange": span(judge),
                "judge": {d: round(statistics.mean(r["judgeMean"][d] for r in cell if r["judgeMean"]), 2)
                          for d in ("correctness", "code_quality", "test_quality",
                                    "instruction_following", "communication")} if judge else {},
                "threeSentenceNote": (round(sum(1 for j in flags if j.get("three_sentence_note")) / len(flags), 2)
                                      if task == "t2" and flags else None),
                "listsUnhandled": (round(sum(1 for j in flags if j.get("lists_unhandled_edge_cases")) / len(flags), 2)
                                   if task == "t2" and flags else None),
                "costPerCorrect": round(sum(c or 0 for c in cost) / len(full), 4) if full else None,
                "judgePerDollar": round(statistics.mean(judge) / med(cost), 1) if judge and med(cost) else None,
                "judgeCostUsd": round(sum(r.get("judgeCostUsd") or 0 for r in cell), 4),
            }
    for key, cell in out.items():
        base = out.get(f"{cell['task']}:bare")
        if base:
            cell["vsBare"] = {m: (round(100 * (cell[m] - base[m]) / base[m], 1) if base[m] else None)
                              for m in ("costUsd", "seconds", "outputTokens", "solutionLoc", "proseWords",
                                        "tokensTotal")}
    return out


def summarize_browser(rows: list[dict], engine: dict) -> dict:
    out = {"agent": {}, "engine": engine.get("summary", {}), "views": engine.get("views", {}),
           "engineLoc": engine.get("loc", {})}
    for task in BTASKS:
        for tool in TOOLS:
            attempted = [r for r in rows if r["task"] == task and r["tool"] == tool]
            cell = [r for r in attempted if not r.get("declined")]
            if not cell:
                continue
            out["agent"][f"{task}:{tool}"] = {
                "task": task, "tool": tool, "n": len(cell), "correct": sum(r["correct"] for r in cell),
                "declined": sum(1 for r in attempted if r.get("declined")),
                "costUsd": med([r["costUsd"] for r in cell]), "costRange": span([r["costUsd"] for r in cell]),
                "tokensTotal": med([r["tokensTotal"] for r in cell]),
                "outputTokens": med([r["tokens"]["output"] for r in cell]),
                "seconds": med([r["seconds"] for r in cell]), "secondsRange": span([r["seconds"] for r in cell]),
                "toolCalls": med([r["toolCalls"] for r in cell]), "apiCalls": med([r["apiCalls"] for r in cell]),
                "codeLines": med([r["codeLines"] for r in cell]),
                "answers": [r["answer"] for r in cell],
            }
    return out


# ----------------------------------------------------------------- charts
def save(fig, name):
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS / f"{name}.png", dpi=170, bbox_inches="tight")
    fig.savefig(CHARTS / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def grouped(ax, summary, metric, rng=None, scale=1.0):
    width = 0.13
    for i, arm in enumerate(ARMS):
        xs, ys, lo, hi = [], [], [], []
        for t, task in enumerate(("t1", "t2")):
            cell = summary.get(f"{task}:{arm}")
            if not cell or cell[metric] is None:
                continue
            x = t + (i - 2.5) * width
            y = cell[metric] * scale
            xs.append(x), ys.append(y)
            if rng and cell.get(rng) and cell[rng][0] is not None:
                lo.append(y - cell[rng][0] * scale), hi.append(cell[rng][1] * scale - y)
            else:
                lo.append(0), hi.append(0)
        ax.bar(xs, ys, width * 0.92, color=COLORS[arm], label=FLAT[arm],
               yerr=[lo, hi] if rng else None, error_kw={"elinewidth": 0.8, "capsize": 2, "ecolor": "#6b717b"})
    ax.set_xticks([0, 1], [TASK_NAMES["t1"], TASK_NAMES["t2"]])


def chart_coding(summary):
    panels = [("costUsd", "costRange", "Cost per answer (USD, median, range)", 1.0),
              ("seconds", "secondsRange", "Time per answer (seconds)", 1.0),
              ("outputTokens", "outputRange", "Output tokens per answer", 1.0),
              ("solutionLoc", "locRange", "Solution lines of code (no docstrings or comments)", 1.0),
              ("toolCalls", "toolRange", "Tool calls per answer (agent activity)", 1.0),
              ("proseWords", "proseRange", "Words of prose outside code", 1.0)]
    fig, axes = plt.subplots(3, 2, figsize=(11, 11.5))
    for ax, (metric, rng, title, scale) in zip(axes.flat, panels):
        grouped(ax, summary, metric, rng, scale=scale)
        ax.set_title(title, loc="left")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False, fontsize=8.5,
               bbox_to_anchor=(0.5, -0.01))
    fig.suptitle("Coding benchmark: six prompt arms, two tasks, five runs each, Claude Sonnet 5",
                 x=0.01, ha="left", fontsize=13, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    save(fig, "coding_overview")

    for metric, rng, title, name in [("costUsd", "costRange", "Cost per answer (USD)", "coding_cost"),
                                     ("seconds", "secondsRange", "Time per answer (seconds)", "coding_time"),
                                     ("outputTokens", "outputRange", "Output tokens per answer", "coding_tokens"),
                                     ("solutionLoc", "locRange", "Solution lines of code", "coding_loc")]:
        fig, ax = plt.subplots(figsize=(9, 4.2))
        grouped(ax, summary, metric, rng)
        ax.set_title(title + " (median; whiskers show the range of five runs)", loc="left")
        ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
        save(fig, name)


def chart_quality(summary):
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.4))
    for ax, (metric, title, scale, limit) in zip(axes, [
            ("hiddenPassRate", "Hidden tests passed (%)", 100, (0, 105)),
            ("judgeOverall", "Blind judge overall (1-10, mean of 2 judges x 5 runs)", 1, (0, 10.5)),
            ("costPerCorrect", "Cost per fully correct answer (USD)", 1, None)]):
        grouped(ax, summary, metric, "judgeRange" if metric == "judgeOverall" else None, scale=scale)
        ax.set_title(title, loc="left", fontsize=10)
        if limit:
            ax.set_ylim(*limit)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=6, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "coding_quality")


def chart_efficiency(summary):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, task in zip(axes, ("t1", "t2")):
        for arm in ARMS:
            cell = summary.get(f"{task}:{arm}")
            if not cell or cell["judgeOverall"] is None:
                continue
            ax.scatter(cell["costUsd"], cell["judgeOverall"], s=90, color=COLORS[arm], zorder=3,
                       edgecolor="white", linewidth=0.8)
            ax.annotate(FLAT[arm], (cell["costUsd"], cell["judgeOverall"]), textcoords="offset points",
                        xytext=(7, 4), fontsize=8, color=INK2)
        ax.set_title(f"{TASK_NAMES[task]}: quality against cost", loc="left")
        ax.set_xlabel("Median cost per answer (USD)")
    axes[0].set_ylabel("Blind judge overall (1-10)")
    fig.tight_layout()
    save(fig, "coding_efficiency")


def chart_context(manifest, summary):
    fig, ax = plt.subplots(figsize=(9.5, 4))
    width = 0.38
    for t, task in enumerate(("t1", "t2")):
        xs = [i + (t - 0.5) * width for i in range(len(ARMS))]
        ys = [manifest["tasks"][task][arm]["contextBytes"] / 1000 for arm in ARMS]
        ax.bar(xs, ys, width * 0.92, color=["#8a8f98", "#c9c5bd"][t], label=TASK_NAMES[task])
        for x, arm in zip(xs, ARMS):
            cell = summary.get(f"{task}:{arm}")
            base = summary.get(f"{task}:bare")
            if cell and base and cell["firstCallContext"] and base["firstCallContext"]:
                added = cell["firstCallContext"] - base["firstCallContext"]
                ax.text(x, manifest["tasks"][task][arm]["contextBytes"] / 1000 + 0.3, f"+{added:,}",
                        ha="center", fontsize=7, color=INK2, rotation=90)
    ax.set_xticks(range(len(ARMS)), [LABELS[a] for a in ARMS], fontsize=8.5)
    ax.set_ylabel("Injected context (KB)")
    ax.set_title("What each arm adds before the prompt: KB injected, and real tokens added (label)", loc="left")
    ax.legend(frameon=False, fontsize=8.5)
    save(fig, "coding_context")


def chart_browser(bsum):
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.6))
    for col, task in enumerate(BTASKS):
        for row, (metric, title) in enumerate([("tokensTotal", "Agent tokens, all kinds (median)"),
                                               ("seconds", "Agent time (s, median)")]):
            ax = axes[row][col]
            cells = [bsum["agent"].get(f"{task}:{tool}") for tool in TOOLS]
            ys = [c[metric] if c else 0 for c in cells]
            bars = ax.bar(range(3), ys, 0.6, color=[TOOL_COLORS[t] for t in TOOLS])
            for bar, cell in zip(bars, cells):
                if cell:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                            f"{cell['correct']}/{cell['n']} right", ha="center", va="bottom", fontsize=8, color=INK2)
            ax.set_xticks(range(3), TOOLS, fontsize=8.5)
            ax.set_title(f"{task}: {title}", loc="left", fontsize=10)
    fig.suptitle("Browser benchmark, agent in the loop (Claude Sonnet 5, three runs per tool per task)",
                 x=0.01, ha="left", fontsize=13, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save(fig, "browser_agent")

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4))
    ax = axes[0]
    width = 0.26
    for i, tool in enumerate(TOOLS):
        ys = [(bsum["engine"].get(f"{tool}:{task}") or {}).get("medianSeconds") or 0 for task in BTASKS]
        ax.bar([t + (i - 1) * width for t in range(3)], ys, width * 0.92, color=TOOL_COLORS[tool], label=tool)
    ax.set_yscale("log")
    ax.set_xticks(range(3), BTASKS)
    ax.set_title("No model: seconds per task from a cold start (median of 5, log scale)", loc="left", fontsize=10)
    ax.legend(frameon=False, fontsize=8.5)
    ax = axes[1]
    views = bsum["views"]
    keys = [("playwright:orders:full", "Playwright\nARIA snapshot"), ("rustwright:orders:full", "Rustwright\nARIA snapshot"),
            ("caveman-browse:orders:full", "caveman-browse\nfull view"),
            ("caveman-browse:orders:interactive", "caveman-browse\ncontrols only (-i)"),
            ("caveman-browse:orders:query", "caveman-browse\nquery view")]
    ys = [views.get(k, {}).get("tokens", 0) for k, _ in keys]
    colors = [TOOL_COLORS["playwright"], TOOL_COLORS["rustwright"]] + [TOOL_COLORS["caveman-browse"]] * 3
    bars = ax.bar(range(len(keys)), ys, 0.6, color=colors)
    for bar, y in zip(bars, ys):
        ax.text(bar.get_x() + bar.get_width() / 2, y, f"{y:,}", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(range(len(keys)), [label for _, label in keys], fontsize=8)
    ax.set_title("Tokens to read the 240-row orders page (o200k counter)", loc="left", fontsize=10)
    fig.tight_layout()
    save(fig, "browser_engine")


def main() -> None:
    manifest = json.loads((BENCH / "arms" / "manifest.json").read_text(encoding="utf-8"))
    coding_all = json.loads((RESULTS / "coding-runs.json").read_text(encoding="utf-8"))
    browser_all = json.loads((RESULTS / "browser-runs.json").read_text(encoding="utf-8"))
    coding = [r for r in coding_all if r.get("completed")]
    browser = [r for r in browser_all if r.get("completed")]
    print(f"completed: coding {len(coding)}/{len(coding_all)}, browser {len(browser)}/{len(browser_all)}")
    engine_path = RESULTS / "engine.json"
    engine = json.loads(engine_path.read_text(encoding="utf-8")) if engine_path.exists() else {}
    summary = {"coding": summarize_coding(coding), "browser": summarize_browser(browser, engine),
               "manifestContextBytes": {t: {a: v["contextBytes"] for a, v in arms.items()}
                                        for t, arms in manifest["tasks"].items()}}
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    chart_coding(summary["coding"])
    chart_quality(summary["coding"])
    chart_efficiency(summary["coding"])
    chart_context(manifest, summary["coding"])
    chart_browser(summary["browser"])
    for key, cell in summary["coding"].items():
        print(f"{key:32} n={cell['n']} ${cell['costUsd']:.4f} {cell['seconds']:>5}s out {cell['outputTokens']:>6}"
              f" loc {cell['solutionLoc']:>4} tools {cell['toolCalls']:>3} hidden {cell['hiddenPassRate']:.0%}"
              f" judge {cell['judgeOverall']} vsBare {cell.get('vsBare', {}).get('costUsd')}%")


if __name__ == "__main__":
    main()
