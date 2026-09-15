# Harness, skills and browser benchmark, 11 September 2026

Two measurements, both run live against real models and real tools.

**Coding.** One prompt sent six ways, on two tasks, five runs each, on Claude
Sonnet 5: no harness, the super harness, super plus ponytail plus caveman,
super plus ponytail with caveman removed, ponytail alone, caveman alone. Scored
by hidden tests the model never saw, by running each answer's own tests, and by
two blind judges (one Opus 5, one Sonnet 5) on the first three runs of each cell.

**Browser.** caveman-browse against Playwright against Rustwright, on three
tasks over two local pages: once with an agent driving the tool, and once as
fixed scripts with no model at all.

## Layout

    prompts/        the task prompts, the delivery instructions and the browser tool cards
    arms/           the exact prompt each arm sends, rendered from the real sources
    arms/sources/   ponytail and caveman as their own hooks inject them, level full
    hidden/         the hidden checks; no model sees these
    fixtures/       the two browser pages and the answer key, from one seeded generator
    browser/        the no-model engine benchmark
    harness/        build, run, collect, analyse, report
    results/        raw per-run metrics, the summary, and every answer as it was written
    charts/         the figures, PNG and SVG
    report/         the full report, HTML and PDF

## Reproduce

Needs Python 3.11+, Node, Microsoft Edge, and a Playwright/Rustwright virtual
environment. The arms rebuild byte for byte; the runs will not, because models
vary between runs, which is why every cell is run five times and reported as a
median with its range.

```bash
# 1. the exact prompts, from the real hook and the real upstream rule files
python benchmarks/2026-09-11/harness/build_arms.py

# 2. the fixture pages and the answer key
python benchmarks/2026-09-11/fixtures/make_fixtures.py

# 3. serve the fixtures (the repo's preview server config), then the browser
#    engine benchmark with no model in the loop
BENCH_CAVEMAN_BROWSE=<path to caveman-browse> \
  python benchmarks/2026-09-11/browser/engine_bench.py --runs 5 --out benchmarks/2026-09-11/results/engine.json

# 4. the agent runs: harness/coding_workflow.js and harness/browser_workflow.js
#    are Workflow scripts; they take their inputs as `args` (see harness/build_arms.py
#    output and prompts/browser.json)

# 5. metrics, charts and the report
python benchmarks/2026-09-11/harness/collect.py --coding <run dir> --browser <run dir>
python benchmarks/2026-09-11/harness/analyze.py
python benchmarks/2026-09-11/harness/report.py
```

## What is measured, and how

| Metric | Where it comes from |
| --- | --- |
| Tokens | Each API response's own usage, counted once per response id |
| Cost | Those counts at the published per-token prices, in `harness/collect.py` |
| Time | First to last transcript timestamp of the run |
| Agent activity | API calls and tool calls in the transcript |
| Lines of code | The answer's implementation, blank lines, comments and docstrings excluded |
| Correctness | `hidden/hidden_t1.py` and `hidden_t2.py`, plus the answer's own tests re-run |
| Quality | Two blind judges scoring five dimensions, neither told which arm produced the answer |
| Browser correctness | The answer key in `fixtures/answers.json` |

## Third-party material

ponytail (MIT, DietrichGebert) and caveman (MIT for the skill, JuliusBrussee)
are rendered by running their own hook code at the pinned commits in
`arms/manifest.json`. caveman-browse is BSL-1.1: it is used here, not
redistributed, and its agent guide is fetched at run time rather than copied in.
