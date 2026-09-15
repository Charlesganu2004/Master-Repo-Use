# graphify across the harnesses, with a 400-token ceiling, 15 September 2026

Five arms, two codebase questions, three runs each, on Claude Sonnet 5. Every
answer was capped at 400 tokens. The harness arms received that cap the way a
person sets it, by typing `/token limit 400`, which the repository's own hook
turns into rule 15. The bare arms received the same cap as a plain sentence.

    bare_strict     no harness, graphify forbidden, answer from the source
    bare_nograph    no harness, graphify not mentioned (but installed on the machine)
    bare_graph      no harness, graphify offered as a tool
    base_graph      base harness (the three layers, rule 1 GRAPHIFY THEN CAVEMAN) + graphify
    super_graph     super harness (the ten-pass chain on top) + graphify

The four harnesses other than super (surface, proxy, wrapper, goal) deliver the
same base pipeline text through different mechanisms, so `base_graph` stands for
all four and `super_graph` adds the chain.

## The questions

    g1  Name the three most connected symbols in this repository, and the file
        each is defined in.
    g2  Which file defines the class Verifier, and which function calls it?

g1 is the question a graph is for: ranking by connectedness is expensive to do
by reading files. g2 is the control: one grep finds it.

Ground truth comes from the graph itself (`god-nodes --top 3 --json` and
`affected "Verifier" --depth 1`), so answers are scored against what the code
contains, not against an opinion.

## Reproduce

```bash
python scripts/graphify_local.py --index master-repo-use   # build the graph
python benchmarks/2026-09-15/harness/build_arms.py         # render the five arms
# run harness/graphify_workflow.js through the Workflow tool with the prompts as args
python benchmarks/2026-09-15/harness/collect.py --run <workflow run dir>
python benchmarks/2026-09-15/harness/chart.py
```

`results/answers/` holds every answer as written. `results/runs.json` holds the
per-run measurements, each traceable to a transcript.

## Two corrections made during the run, both recorded here

The first pass had four arms, and its control was not clean: graphify is
installed on this machine, so an agent that was not told about it could still
find it. `bare_strict` was added to close that, and forbids it outright.

The first scorer counted a run as having used graphify whenever the word
appeared in a shell command. Several runs matched only because they were
*excluding* the graph directory from a grep (`-g '!graphify-out/**'`), which is
the opposite of using it. The detector now requires a real invocation, and the
strict arm's count went from 2 of 3 to 0 of 3, which is what the transcripts say.

## About the committed copies

The prompts and answers here were run with this machine's absolute paths, because
the question names the repository and the tool card names the binary. The
committed copies replace those with `<repo>`, `<graphify>` and `<home>`, so the
repository carries no machine layout. The verification that each run received the
exact prompt was done at collection time against the unedited files, and the
result is recorded per run as `promptVerified` in results/runs.json.
