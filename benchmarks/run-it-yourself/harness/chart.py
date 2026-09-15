"""Chart the 600-token kit results.

    python benchmarks/run-it-yourself/harness/chart.py

reads results/runs.json and writes charts/kit_results.png|svg.
"""
from __future__ import annotations

import json
import pathlib
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

KIT = pathlib.Path(__file__).resolve().parents[1]
ARMS = ["bare_strict", "bare_graph", "base_graph", "super_graph"]
LABELS = {"bare_strict": "No harness\ngraphify forbidden", "bare_graph": "No harness\ngraphify offered",
          "base_graph": "Base harness\n+ graphify", "super_graph": "Super harness\n+ graphify"}
COLORS = {"bare_strict": "#3b3f46", "bare_graph": "#4f7a8a", "base_graph": "#c44e16",
          "super_graph": "#8a3f1e"}
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
    rows = [r for r in json.loads((KIT / "results" / "runs.json").read_text(encoding="utf-8"))
            if r.get("completed")]
    limit = json.loads((KIT / "prompts" / "tasks.json").read_text(encoding="utf-8"))["limit"]
    if not rows:
        raise SystemExit("no completed runs in results/runs.json")
    arms = [a for a in ARMS if any(r["arm"] == a for r in rows)]
    panels = [
        ("Facts right (share of what the repository says)",
         lambda a: sum(r["score"]["found"] for r in rows if r["arm"] == a)
                   / max(1, sum(r["score"]["expected"] for r in rows if r["arm"] == a)) * 100, "%.0f%%"),
        (f"Answers within the {limit}-token ceiling",
         lambda a: sum(1 for r in rows if r["arm"] == a and r["withinLimit"]), "%.0f"),
        ("Median answer length (tokens)",
         lambda a: statistics.median([r["answerTokens"] for r in rows if r["arm"] == a]), "%.0f"),
        ("Median cost per answer (USD)",
         lambda a: statistics.median([r["costUsd"] for r in rows if r["arm"] == a]), "$%.3f"),
        ("Median time per answer (s)",
         lambda a: statistics.median([r["seconds"] for r in rows if r["arm"] == a]), "%.0fs"),
        ("Runs that used graphify",
         lambda a: sum(1 for r in rows if r["arm"] == a and r["graphifyCalls"] > 0), "%.0f"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 6.8))
    for ax, (title, fn, fmt) in zip(axes.flat, panels):
        values = [fn(a) for a in arms]
        bars = ax.bar(range(len(arms)), values, 0.6, color=[COLORS[a] for a in arms])
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), fmt % value,
                    ha="center", va="bottom", fontsize=8.5, color=INK2)
        ax.set_xticks(range(len(arms)), [LABELS[a] for a in arms], fontsize=7.5)
        ax.set_title(title, loc="left")
    over = [r for r in rows if not r["withinLimit"]]
    fig.suptitle(f"The 600-token test: {len(rows)} runs, two questions, "
                 f"{len(over)} answer(s) over the ceiling",
                 x=0.01, ha="left", fontsize=12.5, fontweight="semibold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    charts = KIT / "charts"
    charts.mkdir(exist_ok=True)
    fig.savefig(charts / "kit_results.png", dpi=170, bbox_inches="tight")
    fig.savefig(charts / "kit_results.svg", bbox_inches="tight")
    print(f"wrote {charts / 'kit_results.png'}")


if __name__ == "__main__":
    main()
