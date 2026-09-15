"""Draw the graphify experiment: correctness, cost, time, and the 400-token ceiling.

    python benchmarks/2026-09-15/harness/chart.py

reads results/runs.json and writes charts/graphify_experiment.png|svg.
"""
from __future__ import annotations

import json
import pathlib
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

BENCH = pathlib.Path(__file__).resolve().parents[1]
ARMS = ["bare_strict", "bare_nograph", "bare_graph", "base_graph", "super_graph"]
LABELS = {"bare_strict": "No harness\ngraphify forbidden", "bare_nograph": "No harness\nnot offered",
          "bare_graph": "No harness\ngraphify offered", "base_graph": "Base harness\n+ graphify",
          "super_graph": "Super harness\n+ graphify"}
COLORS = {"bare_strict": "#6b717b", "bare_nograph": "#3b3f46", "bare_graph": "#4f7a8a",
          "base_graph": "#c44e16", "super_graph": "#8a3f1e"}
INK, INK2, GRID, GROUND = "#121316", "#454a53", "#d9d6cf", "#fbfaf7"
plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"], "font.size": 9.5, "axes.edgecolor": "#b9b5ad",
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
    "axes.titleweight": "semibold", "axes.titlesize": 10.5, "figure.facecolor": GROUND,
    "axes.facecolor": GROUND, "savefig.facecolor": GROUND, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.6, "axes.axisbelow": True, "axes.spines.top": False,
    "axes.spines.right": False,
})


def main() -> None:
    rows = [r for r in json.loads((BENCH / "results" / "runs.json").read_text(encoding="utf-8"))
            if r.get("completed")]
    limit = json.loads((BENCH / "prompts" / "tasks.json").read_text(encoding="utf-8"))["limit"]
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]

    def cell(arm, fn, default=0):
        values = [fn(r) for r in rows if r["arm"] == arm]
        return statistics.median(values) if values else default

    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    panels = [
        ("Facts correct (share of the graph's own answer)",
         lambda a: (sum(r["score"]["found"] for r in rows if r["arm"] == a)
                    / max(1, sum(r["score"]["expected"] for r in rows if r["arm"] == a)) * 100), "%.0f%%"),
        ("Cost per answer (USD, median)", lambda a: cell(a, lambda r: r["costUsd"]), "$%.3f"),
        ("Time per answer (s, median)", lambda a: cell(a, lambda r: r["seconds"]), "%.0fs"),
        ("Tool calls per answer (median)", lambda a: cell(a, lambda r: r["toolCalls"]), "%.0f"),
        ("Runs that used graphify",
         lambda a: sum(1 for r in rows if r["arm"] == a and r["graphifyCalls"] > 0), "%.0f"),
        ("Answers within the 400-token ceiling",
         lambda a: sum(1 for r in rows if r["arm"] == a and r["withinLimit"]), "%.0f"),
    ]
    for ax, (title, fn, fmt) in zip(axes.flat, panels):
        values = [fn(a) for a in arms]
        bars = ax.bar(range(len(arms)), values, 0.62, color=[COLORS[a] for a in arms])
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), fmt % value,
                    ha="center", va="bottom", fontsize=8.5, color=INK2)
        ax.set_xticks(range(len(arms)), [LABELS[a] for a in arms], fontsize=7.5)
        ax.set_title(title, loc="left")
        if "ceiling" in title or "used graphify" in title:
            ax.set_ylim(0, max(6, max(values) + 1))
    total = len(rows)
    over = [r for r in rows if not r["withinLimit"]]
    fig.suptitle(f"graphify across the harnesses: {total} runs, 2 codebase questions, "
                 f"{limit}-token ceiling ({len(over)} answer(s) over it)",
                 x=0.01, ha="left", fontsize=12.5, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    charts = BENCH / "charts"
    charts.mkdir(exist_ok=True)
    fig.savefig(charts / "graphify_experiment.png", dpi=170, bbox_inches="tight")
    fig.savefig(charts / "graphify_experiment.svg", bbox_inches="tight")
    print(f"wrote {charts / 'graphify_experiment.png'}")


if __name__ == "__main__":
    main()
