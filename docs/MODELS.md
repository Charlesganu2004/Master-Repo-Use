# Local models

Every model this repository catalogues, with the command that gets it. Nothing
here sends you to Hugging Face: the commands pull from the Ollama registry, and
this repository holds the pinned version of each one.

## Get everything your machine can hold

Install the runtime once:

    winget install --id Ollama.Ollama --accept-source-agreements --accept-package-agreements   # Windows
    curl -fsSL https://ollama.com/install.sh | sh                                              # Linux and macOS

Then one command pulls every model that fits, verified against the digest pinned
in `docs/model-manifest.json`:

    python scripts/vendor_models.py --fetch --max-ram 16

Change `16` to your memory in gigabytes. After that the machine is offline for
these: no registry, no Hugging Face, no network at all.

See what it would do first:

    python scripts/vendor_models.py --plan --max-ram 16
    python scripts/vendor_models.py --fetch --max-ram 16 --dry-run

## Why the weights are not committed here

Charles asked for the models to live in the repository. They cannot, and the
numbers are the reason rather than a preference. Measured on 2026-09-09 against
`registry.ollama.ai` and GitHub's published limits:

| limit | value | what the models are |
|---|---|---|
| GitHub file size | 100 MB, hard rejection | smallest model is 274 MB, **2.6x over** |
| Repository size | 5 GB recommended cap | all 35 total **227 GB, 42x over** |
| GitHub Pages site | 1 GB | this repo publishes through Pages |
| Release asset | 2 GiB per file, 1000 per release | the only GitHub path that holds one |

Not one of the 35 fits inside git's file limit. Git LFS would raise the per-file
ceiling but bills storage and bandwidth, and would make a clone of this
repository pull 227 GB.

So the repository carries the three things that actually remove the trip to a
model page:

1. **`docs/model-manifest.json`** pins every tag to the exact digest and byte
   size the registry returned. The repository states which models and which
   versions; drift is detectable rather than assumed.
2. **`models/*.Modelfile`**, one per tag, committed. `ollama create` builds the
   named model from this repository's definition.
3. **One command**, above, that fetches and verifies the lot.

## Refreshing to the current versions

    python scripts/vendor_models.py --manifest      # re-pin from the registry
    python scripts/vendor_models.py --modelfiles    # rewrite the definitions
    python scripts/vendor_models.py --check         # offline agreement check
    python scripts/verify_model_tags.py             # every tag still resolves

A digest that changes means the upstream model moved. That shows up as a diff in
`docs/model-manifest.json` rather than as a silent difference between two
machines.

## Redistributing the weights

Release assets are the one GitHub path that can hold a model, at 2 GiB each and
1000 per release. Size is not the only gate: redistributing weights makes you a
distributor, and the licence decides whether that is allowed.

**Four are clean to redistribute today**, all Apache-2.0 and all under 2 GiB:

| model | size | licence |
|---|---|---|
| `nomic-embed-text` | 0.27 GB | Apache-2.0 |
| `qwen3:0.6b` | 0.52 GB | Apache-2.0 |
| `smollm2:360m` | 0.73 GB | Apache-2.0 |
| `qwen3:1.7b` | 1.36 GB | Apache-2.0 |

    python scripts/vendor_models.py --release --dry-run
    python scripts/vendor_models.py --release --out dist/models

**Eleven are pull-only, and the reason is the licence rather than the size:**

- **Gemma Terms of Use** (9 models) require the use policy and terms to be passed
  to every recipient. A release asset does not do that.
- **Llama 3.2 Community** (2 models) require attribution, a "Built with Llama"
  notice, a copy of the licence, and carry a monthly-active-user clause.

Both permit redistribution if those conditions are met. Meeting them is a legal
commitment rather than a file copy, so this repository does not make it on
Charles's behalf. Pulling them costs the user one command and costs him nothing.

## Every model

Sorted by memory needed. `--fetch --max-ram N` takes everything at or below N.

| model | size | memory | licence | redistribute |
|---|---|---|---|---|
| nomic-embed-text | 0.27 GB | 4 GB | Apache-2.0 | yes |
| gemma3:270m | 0.29 GB | 4 GB | Gemma Terms | pull only |
| embeddinggemma | 0.62 GB | 4 GB | Gemma Terms | pull only |
| smollm2:360m | 0.73 GB | 4 GB | Apache-2.0 | yes |
| qwen3:0.6b | 0.52 GB | 4 GB | Apache-2.0 | yes |
| gemma3:1b | 0.82 GB | 4 GB | Gemma Terms | pull only |
| llama3.2:1b | 1.32 GB | 4 GB | Llama 3.2 Community | pull only |
| qwen3:1.7b | 1.36 GB | 6 GB | Apache-2.0 | yes |
| gemma3n:e2b | 5.62 GB | 6 GB | Gemma Terms | pull only |
| llama3.2:3b | 2.02 GB | 6 GB | Llama 3.2 Community | pull only |
| phi4-mini | 2.49 GB | 6 GB | MIT | over 2 GiB |
| phi4-mini-reasoning | 3.15 GB | 6 GB | MIT | over 2 GiB |
| phi3.5 | 2.18 GB | 6 GB | MIT | over 2 GiB |
| phi3:mini | 2.18 GB | 6 GB | MIT | over 2 GiB |
| gemma3:4b | 3.34 GB | 6 GB | Gemma Terms | pull only |
| gemma3n:e4b | 7.55 GB | 6 GB | Gemma Terms | pull only |
| qwen3:4b | 2.50 GB | 6 GB | Apache-2.0 | over 2 GiB |
| codegemma:7b | 5.01 GB | 8 GB | Gemma Terms | pull only |
| qwen2.5-coder:7b | 4.68 GB | 8 GB | Apache-2.0 | over 2 GiB |
| mistral | 4.37 GB | 8 GB | Apache-2.0 | over 2 GiB |
| deepseek-r1:7b | 4.68 GB | 8 GB | MIT | over 2 GiB |
| qwen3:8b | 5.23 GB | 12 GB | Apache-2.0 | over 2 GiB |
| gemma2:9b | 5.44 GB | 12 GB | Gemma Terms | pull only |
| gemma3:12b | 8.15 GB | 12 GB | Gemma Terms | pull only |
| phi3:medium | 7.90 GB | 16 GB | MIT | over 2 GiB |
| phi4 | 9.05 GB | 16 GB | MIT | over 2 GiB |
| phi4-reasoning | 11.12 GB | 16 GB | MIT | over 2 GiB |
| deepseek-r1:14b | 8.99 GB | 16 GB | MIT | over 2 GiB |
| qwen3:14b | 9.28 GB | 16 GB | Apache-2.0 | over 2 GiB |
| mistral-small | 14.33 GB | 24 GB | Apache-2.0 | over 2 GiB |
| gemma3:27b | 17.40 GB | 24 GB | Gemma Terms | pull only |
| gemma2:27b | 15.63 GB | 24 GB | Gemma Terms | pull only |
| qwen3:30b-a3b | 18.56 GB | 24 GB | Apache-2.0 | over 2 GiB |
| qwen2.5-coder:32b | 19.85 GB | 32 GB | Apache-2.0 | over 2 GiB |
| qwen3:32b | 20.20 GB | 32 GB | Apache-2.0 | over 2 GiB |

Sizes and digests are regenerated by `--manifest`, so this table is a snapshot of
`docs/model-manifest.json` rather than a second copy maintained by hand.
