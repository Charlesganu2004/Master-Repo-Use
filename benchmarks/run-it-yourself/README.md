# Run the harness test yourself

Two questions about this repository, four ways of asking, every answer capped at
**600 tokens**. It takes about ten minutes and needs no API key of its own: you
can paste the prompts into whatever assistant you already pay for.

    complex         trace how a prompt becomes injected context, then name the
                    three most connected symbols and where each is defined
    super_complex   name the entry script of all five harnesses, name the three
                    hubs, say what calls the Verifier class, and name the one
                    file whose change would reach the most callers

Four arms per question:

| Arm | What it gets |
| --- | --- |
| `bare_strict` | The question, a 600-token sentence, and an instruction not to use graphify |
| `bare_graph` | The question, the same ceiling, and graphify offered as a tool |
| `base_graph` | The repository's base harness (three layers) via `/token limit 600`, plus graphify |
| `super_graph` | The super harness (ten-pass chain) via `/token limit 600`, plus graphify |

The harness arms are not written by hand. `build_arms.py` asks this repository's
own hook what it would inject for that prompt, so what you send is what a real
session receives, including rule 15 at 600 tokens.

## Setup

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File benchmarks\run-it-yourself\setup.ps1
```

macOS or Linux:

```bash
bash benchmarks/run-it-yourself/setup.sh
```

That installs graphify into `~/.graphify/venv`, indexes this repository with
local AST parsing only (no API key, nothing leaves the machine), and writes the
eight prompts into `arms/`.

## Run

1. Open `arms/<task>/<arm>.prompt.md` and paste the whole file into your
   assistant as one message. Do that for each of the eight.
2. Save each reply as `answers/<task>/<arm>.md`.
3. Score them:

```bash
python benchmarks/run-it-yourself/harness/score.py
```

You get, per answer, how many of the required facts it contained, whether it
stayed inside 600 tokens, and what it missed.

## What to watch for

- **The hubs question is the one that separates them.** Ranking symbols by how
  connected they are is cheap against a graph and expensive by reading files.
- **Whether the ceiling holds.** In our run the arms without the graph ran far
  past the limit because they pasted evidence to justify an answer they were not
  sure of; the graph arms answered in a few lines and stayed inside it.
- **Whether the answer is right.** `score.py` checks against the repository, so
  a confident wrong answer scores zero, which is the point.

## Honest limits

- The scorer's token count is words divided by 0.75, an estimate. Your
  provider's usage page has the real number.
- Four arms, two questions and one run each is a demonstration, not a
  measurement. Our own numbers come from three runs per cell and are in
  `benchmarks/2026-09-15/`.
- Ground truth is tied to this repository at this commit. Change the code,
  rebuild the graph with `graphify update .`, and the expected answers move.

## A note on the committed prompts

`arms/` holds the prompts as they were generated on the machine that ran them,
with local paths replaced by `<repo>` and `<graphify>`. When you run setup, they
are rewritten with your own paths, so expect a local diff there. That is the
generator doing its job, not a change to the test.
