# LLM Models & Serving

The lane for choosing an open-weight model and the stack that runs it. "Open weights" is not
"open source": several widely used families ship permissive repository code alongside weights
under a separate licence with usage restrictions, and a few reverse that. This doc states code
licence and weight licence separately wherever they differ, because that distinction is the one
that decides whether you can ship.

This is the lane guide for [agents/model-picker.md](../agents/model-picker.md) (Picker). Picker
works backward from the binding constraint, not from a leaderboard, so the doc is ordered the
same way.

Related:
- [SECURITY-SCANNING.md](SECURITY-SCANNING.md) — how every repo below was vetted
- [VETTING-REPORT.md](VETTING-REPORT.md) — per-repo verdicts and licence findings
- [skills/dep-audit](../skills/dep-audit/SKILL.md) — run the same audit on anything not listed here
- [TOKEN-EFFICIENCY.md](TOKEN-EFFICIENCY.md) and [cost-reduction/](../cost-reduction/README.md) — cost controls

---

## Start here

Find the constraint that actually binds. One of these dominates; the rest are noise until it is
satisfied.

| Binding constraint | What to pick | Why |
|---|---|---|
| VRAM ceiling (one consumer card) | Smallest model that passes your eval, on [llama.cpp](https://github.com/ggml-org/llama.cpp) with a quantised GGUF | Single-stream runtime, low overhead, runs CPU-only if it has to |
| VRAM ceiling (one or more datacentre GPUs, multi-user) | [vLLM](https://github.com/vllm-project/vllm) with a quantised checkpoint from [llm-compressor](https://github.com/vllm-project/llm-compressor) | Paged KV cache is what makes the memory budget stretch across concurrent requests |
| p99 latency, interactive, many users | [SGLang](https://github.com/sgl-project/sglang) or vLLM, tuned for concurrency | Prefix caching and continuous batching hold tail latency under load |
| Cost per million tokens, low volume | Hosted API, optionally behind a separately audited and version-pinned gateway | Below a few million tokens a month, self-hosting rarely wins once engineering time counts |
| Cost per million tokens, high steady volume | Self-host vLLM or SGLang on reserved GPUs | Utilisation is the whole argument; idle GPUs destroy it |
| Data residency / air-gapped | Any open-weight family below, self-hosted, licence checked | Non-negotiable: it eliminates hosted APIs outright |
| Legal / redistribution risk | Apache-2.0 or MIT weights only — see the licence table | Restricted weight licences are the most common late-stage blocker |

---

## How to choose

```text
1. What binds?
   VRAM ------------> size the model to the card, then quantise, then re-eval
   latency ---------> concurrency-tuned server (SGLang / vLLM), never a local runtime
   cost ------------> compute volume first (see "Hosted vs self-hosted")
   residency -------> self-host only; stop considering hosted APIs
   licence ---------> filter the model table to permissive weights before anything else

2. Workload shape?
   batch / offline -----------> throughput server, large batch, quantisation pays off most
   interactive, many users ---> throughput server, concurrency-tuned, prefix caching matters
   single user / desktop -----> local runtime (llama.cpp); a throughput server here wastes the box

3. Task type?
   extraction, classification, routing -> start small; most of these are over-modelled
   summarisation, rewriting ------------> small-to-mid, verify on long inputs
   open-ended reasoning, agentic tools -> larger, and quantise cautiously

4. Volume?
   < ~1M tokens/month --------> hosted API, no argument
   ~1M-10M tokens/month ------> hosted API unless residency or licence forces otherwise
   > ~10M tokens/month -------> model the self-host case honestly, including staff time

5. Then, and only then, pick a model. Smallest candidate first.
   Move up only on measured failure against your own eval set.
```

---

## Serving stacks

High-throughput multi-user servers and single-machine local runtimes are not interchangeable.
Running a local runtime behind a production endpoint leaves most of the GPU idle; running a
throughput server for one desktop user adds operational weight for nothing.

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [vllm-project/vllm](https://github.com/vllm-project/vllm) | You need a multi-user, OpenAI-compatible endpoint with high throughput and memory-efficient KV cache handling. | `pip install vllm` then `vllm serve <model-id>` | Apache-2.0 |
| [sgl-project/sglang](https://github.com/sgl-project/sglang) | Your traffic shares long prefixes (system prompts, RAG context, agent loops), or you need an RL rollout backend or structured-generation frontend. | `pip install "sglang[all]"` then `python -m sglang.launch_server --model-path <model-id>` | Apache-2.0 |
| [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | You are serving one machine — laptop, workstation, edge box — possibly CPU-only, and want minimal setup with GGUF weights. | `llama-server -m ./model.gguf --port 8080` (build per README) | MIT |

### Which class is which

| Repo | Class | Optimised for | Wrong job for it |
|---|---|---|---|
| vLLM | Throughput server | Concurrent requests, continuous batching, paged KV cache | Single-user desktop use |
| SGLang | Throughput server | Prefix-cache reuse across requests, structured generation | Single-user desktop use |
| llama.cpp | Local runtime | One stream, low setup cost, CPU or mixed CPU/GPU | Production multi-user serving |

### Supporting tooling

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [vllm-project/llm-compressor](https://github.com/vllm-project/llm-compressor) | You need to quantise or sparsify a checkpoint (GPTQ, AWQ, SmoothQuant, FP8/NVFP4) into something vLLM can load. | `pip install llmcompressor` | Apache-2.0 |
| [EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) | You want standard academic benchmarks as a sanity check, with HF / vLLM / SGLang / OpenAI-compatible backends. | `pip install lm-eval` then `lm_eval --model hf --model_args pretrained=<model-id> --tasks <task>` | MIT |

Fine-tuning is usually the wrong first move. Prompting, retrieval, and a larger base model are
cheaper to try and easier to reverse. Evaluate a version-pinned fine-tuning tool only after those
options fail on a measured case and its install-time behavior has been reviewed.

---

## Model families

The licence column is the point of this table. Read it before the description.

| Repo | Use it when | Fast start | License |
|---|---|---|---|
| [QwenLM/Qwen3.6](https://github.com/QwenLM/Qwen3.6) | You want permissive small-to-mid dense and MoE open weights (roughly 0.8B to 35B-A3B) and need a clean commercial licence with no strings. | Weights on Hugging Face; serve with `vllm serve <model-id>` (ids listed in the repo README) | **Apache-2.0 for all open-weight Qwen3.5/3.6 models** — no user-count cap, no acceptable-use rider. Code and weights alike. |
| [zai-org/GLM-5](https://github.com/zai-org/GLM-5) | You need frontier-scale capability self-hosted — 744B MoE, ~40B active per token, 1M-token context, BF16 and FP8 releases — and can supply the hardware. | Weights on Hugging Face; multi-GPU vLLM or SGLang deployment per the repo README | **Split but both permissive:** Apache-2.0 for repository code, MIT for the model weights (verified for GLM-5.2 on Hugging Face; no regional restriction found). |

### Licence at a glance

| Family | Code licence | Weight licence | Commercially clean? |
|---|---|---|---|
| Qwen3.5 / Qwen3.6 | Apache-2.0 | Apache-2.0 | Yes |
| GLM-5 | Apache-2.0 | MIT | Yes |

Rules that hold across the lane:

- A permissive repository licence says nothing about the weights. They are separate artifacts
  with separate terms, published in separate places.
- Verify the licence on the Hugging Face model card for the exact checkpoint you intend to
  deploy, not on the family. Sizes within one family have shipped under different terms
  elsewhere in this catalog.
- Fine-tunes and quantised re-uploads inherit the base model's terms, and a community re-upload
  can be mislabelled. Trace it to the original card.
- Weight files are code-adjacent: prefer `safetensors` over pickle-based formats, which
  deserialise arbitrary objects. The scanners in [SECURITY-SCANNING.md](SECURITY-SCANNING.md)
  inspect repositories, not checkpoints.

---

## Quantisation

Quantisation buys memory and often throughput. It costs quality. It is a tradeoff, not free
savings, and anyone presenting it as free has not measured it on their own task.

Rough weight-memory arithmetic, before anything else is loaded:

```text
weights (GB) ~= parameters (billions) * bytes per parameter
  BF16/FP16 = 2 bytes    8-bit = 1 byte    4-bit = 0.5 bytes

Then add, and do not skip these:
  + KV cache      grows with context length x batch size — often the real ceiling
  + activations, CUDA context, framework overhead
```

What to expect qualitatively:

| Level | Typical use | Honest caveat |
|---|---|---|
| BF16 / FP16 | Baseline, and your quality reference | Measure here first or you have nothing to compare against |
| 8-bit / FP8 | Usual first step for serving | Closest to baseline of the options, but still verify on your own eval |
| 4-bit | Fitting a larger model on a smaller card | Degradation is real and lands hardest on multi-step reasoning and long context |
| Below 4-bit | Last resort on tight hardware | Expect visible quality loss; often a smaller model at higher precision is better |

Two practical rules:

1. A smaller model at higher precision frequently beats a larger model crushed to fit. Test both
   before assuming the bigger one wins.
2. Re-run your eval set after every quantisation change. Aggregate benchmark scores hide exactly
   the failures quantisation introduces.

Use [llm-compressor](https://github.com/vllm-project/llm-compressor) for vLLM-bound checkpoints
and GGUF quantisation via [llama.cpp](https://github.com/ggml-org/llama.cpp) for local runtimes.

---

## Hosted vs self-hosted

This doc quotes no per-token prices, because they change monthly and a stale price in a doc is
worse than no price. Use the method; get the current figures from the provider's pricing page at
decision time.

```text
Hosted cost/month  = (input tokens/M  * current input price/M)
                   + (output tokens/M * current output price/M)

Self-host cost/month = GPU-hours needed at REALISTIC utilisation * current GPU-hour price
                     + storage, egress, and idle time you will actually pay for
                     + engineering time to build, tune, monitor and stay on-call for it
```

The last line is the one that gets omitted, and it is usually the largest. A self-hosted endpoint
is a service someone has to operate: capacity planning, upgrades, incidents, out-of-memory
failures at 3am.

| Situation | Honest answer |
|---|---|
| Below a few million tokens a month | Hosted. Self-hosting is almost never cheaper once engineering time is counted. |
| High, steady, predictable volume | Self-hosting can win — but only at high utilisation. Bursty traffic on reserved GPUs loses to hosted. |
| Data residency or air-gap requirement | Self-host. Cost is not the deciding variable; do not let a cost comparison override the requirement. |
| Licence or vendor-independence requirement | Self-host, with the weight licence verified for your exact deployment. |
| Unclear volume | Ship on hosted first, measure real token volume for a month, then revisit. |

If provider abstraction is necessary, place a separately audited, version-pinned gateway in front.
Keep credentials scoped to the minimum providers and record spend independently so the hosted versus
self-hosted comparison remains measurable.

---

## Build an eval set first

Twenty real examples from your actual traffic predict production quality better than any public
benchmark. Public benchmarks measure a distribution that is not yours, and leaderboard position
does not transfer to your prompts, your document formats, or your failure modes.

| Step | What to do |
|---|---|
| 1. Collect | Twenty real inputs from the actual workload, including the awkward ones. Bias toward cases that have already caused trouble. |
| 2. Define pass | Write the acceptance criterion per example before running any model. Vague criteria produce vague conclusions. |
| 3. Baseline | Run the smallest plausible candidate first. Record failures, not just a score. |
| 4. Escalate on evidence | Move up in size, or off quantisation, only where you measured a failure. |
| 5. Freeze and reuse | Keep the set. Re-run it on every model swap, quantisation change, and serving-stack change. |

Use [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) for standard
benchmarks as a smoke test and a regression guard. Let your own twenty examples make the decision.

---

## Limitations / what this lane will not do for you

- **It goes stale.** Model generations, context limits, and prices move monthly. Nothing here is
  a substitute for checking the current state of a model card or pricing page before you commit.
- **It does not rank models.** No "best model" claim appears above, deliberately. Any such claim
  would be wrong within a release cycle. The eval-set method replaces it.
- **No benchmark or performance numbers.** Throughput and quality depend on your hardware, batch
  size, context length, and quantisation. Measure on your own box.
- **Licences were verified at vetting time.** They can change between releases, and a checkpoint's
  card can differ from its repository. Re-verify the exact artifact you deploy, and re-audit on
  major version bumps as described in [SECURITY-SCANNING.md](SECURITY-SCANNING.md).
- **Vetting covered repository code, not weights.** The pipeline in
  [SECURITY-SCANNING.md](SECURITY-SCANNING.md) and
  [skills/dep-audit](../skills/dep-audit/SKILL.md) scans source trees. It does not inspect model
  checkpoints, training data, or anything a model was aligned to do.
- **It says nothing about training-data provenance.** Open weights do not imply open, documented,
  or legally cleared training data. If that matters to you, it is a separate investigation.
- **Anything not listed here is unvetted.** Run [skills/dep-audit](../skills/dep-audit/SKILL.md)
  before adding it, and record the verdict in [VETTING-REPORT.md](VETTING-REPORT.md).
- **No agent accepts licence terms for you.** Picker identifies what a licence requires and hands
  the decision to a human. Accepting model terms, creating accounts, and entering payment details
  stay with you.
