# Local Models & Hardware Fit

**Question this page answers:** *"I have N GB of RAM. What can I actually run, and which
repos in this catalog are worth installing on this machine?"*

The command center has an interactive version under the **Local Models** tab, including an
install checker. Both read the same file: [`docs/hardware-profiles.json`](hardware-profiles.json)
— **36 models** across three vendors, sized against seven RAM tiers.

## Scope

Deliberately narrow — three sources only:

| Source | Why it is here |
|---|---|
| **Ollama** | The default local runtime, plus the wider open-weight families it ships (Qwen, Llama, Mistral, DeepSeek, SmolLM). |
| **Microsoft** | The only credible sub-8 GB path (BitNet, ONNX/NPU) plus the Phi small-model family. |
| **Google / Gemini** | Gemma open weights, `gemma.cpp`, and hosted Gemini for when RAM is the binding constraint. |

General-purpose training and serving stacks (llama.cpp, vLLM, Megatron-LM, LMFlow) solve a
different problem and live in [`repo-lists/llm-models-serving.txt`](../repo-lists/llm-models-serving.txt).

## How the numbers are produced

**Computed estimates, not benchmarks.** The arithmetic is published so you can disagree with it:

```
per_b       = bytes_per_param[quant] + 0.03 (runtime) + 0.02 (KV cache @ 4k)
required_gb = params_b × per_b + 0.25
usable_gb   = total_ram − os_reserve          # Windows 3.0, macOS 2.5, Linux 1.5
fits when   required_gb ≤ usable_gb
```

`bytes_per_param`: q4 = 0.6, q8 = 1.1, fp16 = 2.05.

Overhead **scales with parameter count**. A flat term was wrong at both ends: it made a 270M
model look unrunnable on a 4 GB box and understated KV cache on a 27B one.

`tests/test_hardware_profiles.py` re-derives every `min_ram_gb` from this formula and fails if
the data drifts. A recommendation that says "fits" is arithmetic, not optimism.

Two things the formula does **not** model:

- **Discrete GPU VRAM** substitutes for system RAM on the weights term. A 16 GB machine with an
  8 GB GPU behaves closer to a 24 GB one.
- **Long context.** The KV term assumes ~4k tokens; add roughly
  0.02 GB per billion parameters for each additional 4k.

## Are the tags real?

They could not be verified automatically when this data was authored, so the repository ships a
checker rather than an assurance. It resolves every tag against a running Ollama daemon, or the
public registry if none is running:

```bash
python scripts/verify_model_tags.py
```

That check has already earned its place: it caught `phi4-multimodal`, which does not exist in the
Ollama library, before it shipped.

## The tiers

| RAM | Usable (Win) | Verdict | Models that fit | Microsoft | Google | Ollama |
|---:|---:|---|---:|---:|---:|---:|
| **4 GB** | 1.0 | severely constrained | 8 | 1 | 3 | 4 |
| **6 GB** | 3.0 | tiny to small | 18 | 5 | 6 | 7 |
| **8 GB** | 5.0 | small models, usable | 22 | 5 | 7 | 10 |
| **12 GB** | 9.0 | comfortable small / tight mid | 25 | 5 | 9 | 11 |
| **16 GB** | 13.0 | solid daily driver | 30 | 8 | 9 | 13 |
| **24 GB** | 21.0 | strong | 34 | 8 | 11 | 15 |
| **32 GB** | 29.0 | excellent | 36 | 8 | 11 | 17 |

### The 4 GB answer

A 4 GB Windows machine has roughly 1 GB free once the OS has taken its share. Sub-1B models fit
and are genuinely useful for classification, tagging and extraction — but **nothing conversational
does**, and the advisor says so rather than recommending something that will swap. On Linux the
same box has ~2.5 GB usable and the picture improves noticeably.

Microsoft has no sub-1B open-weight model, so at 4 GB its only entry is BitNet, whose 1.58-bit
weights make it far smaller than its 2.4B parameter count implies.

## Microsoft

| Min RAM | Tag | Params | Family | Good for | Licence |
|---:|---|---:|---|---|---|
| 4 GB | `BitNet-b1.58-2B-4T` | 2.4B | BitNet b1.58 | 1.58-bit weights. The only credible Microsoft option below 8 GB; needs bitnet.cpp, not Ollama. | MIT |
| 6 GB | `phi4-mini` | 3.8B | Phi-4 | Reasoning-tuned small model with strong instruction following for its size. | MIT |
| 6 GB | `phi4-mini-reasoning` | 3.8B | Phi-4 | Chain-of-thought tuned variant of Phi-4-mini. Slower, better at multi-step maths. | MIT |
| 6 GB | `phi3.5` | 3.8B | Phi-3.5 | Previous generation. Keep only if a workload is already tuned against it. | MIT |
| 6 GB | `phi3:mini` | 3.8B | Phi-3 | Compact Phi-3. Useful when a workload is pinned to the Phi-3 generation. | MIT |
| 16 GB | `phi3:medium` | 14.0B | Phi-3 | Phi-3 Medium. Older than Phi-4 but a genuine mid-size Microsoft option. | MIT |
| 16 GB | `phi4` | 14.0B | Phi-4 | Best Microsoft open-weight general model for a 16 GB machine. | MIT |
| 16 GB | `phi4-reasoning` | 14.0B | Phi-4 | Reasoning-tuned Phi-4. Competitive with much larger models on maths and logic. | MIT |

Microsoft's open-weight ceiling is **14B**. Above 16 GB, the larger options come from Google or
the wider Ollama library.

## Google / Gemma

| Min RAM | Tag | Params | Family | Good for | Licence |
|---:|---|---:|---|---|---|
| 4 GB | `gemma3:270m` | 0.27B | Gemma 3 | Classification, tagging, keyword extraction. Not conversational. | Gemma Terms of Use |
| 4 GB | `embeddinggemma` | 0.31B | Gemma | Google's embedding model for local RAG. Runs alongside a chat model. | Gemma Terms of Use |
| 4 GB | `gemma3:1b` | 1.0B | Gemma 3 | Short-form summarisation and structured extraction on very small machines. | Gemma Terms of Use |
| 6 GB | `gemma3n:e2b` | 2.0B | Gemma 3n | On-device tuned; MatFormer architecture keeps active parameters low. | Gemma Terms of Use |
| 6 GB | `gemma3:4b` | 4.0B | Gemma 3 | General assistant with vision input. The sensible default at 8 GB. | Gemma Terms of Use |
| 6 GB | `gemma3n:e4b` | 4.0B | Gemma 3n | Larger on-device Gemma 3n; better reasoning than e2b at similar footprint. | Gemma Terms of Use |
| 8 GB | `codegemma:7b` | 7.0B | CodeGemma | Code completion and generation, fill-in-the-middle aware. | Gemma Terms of Use |
| 12 GB | `gemma2:9b` | 9.0B | Gemma 2 | Previous-generation Gemma; still strong general chat at mid size. | Gemma Terms of Use |
| 12 GB | `gemma3:12b` | 12.0B | Gemma 3 | Multi-step instructions and code review. Vision capable. | Gemma Terms of Use |
| 24 GB | `gemma3:27b` | 27.0B | Gemma 3 | Largest Gemma that fits a consumer box. Genuine coding assistance. | Gemma Terms of Use |
| 24 GB | `gemma2:27b` | 27.0B | Gemma 2 | Previous-generation 27B. Alternative to Gemma 3 if a workload is already tuned to it. | Gemma Terms of Use |

> **Licensing:** Gemma models ship under the **Gemma Terms of Use**, not an OSI licence, and carry
> real use restrictions. Read them before shipping a product built on Gemma.
> Google's open-weight ceiling is **27B**.

## Ollama library

| Min RAM | Tag | Params | Family | Good for | Licence |
|---:|---|---:|---|---|---|
| 4 GB | `nomic-embed-text` | 0.14B | Nomic | The default local RAG embedding model. Pairs with any chat model. | Apache-2.0 |
| 4 GB | `smollm2:360m` | 0.36B | SmolLM2 | Tiny assistant for autocomplete and classification on 4 GB machines. | Apache-2.0 |
| 4 GB | `qwen3:0.6b` | 0.6B | Qwen3 | Smallest Qwen3. Surprisingly capable at structured extraction. | Apache-2.0 |
| 4 GB | `llama3.2:1b` | 1.0B | Llama 3.2 | Meta's smallest instruct model. Good summariser at 4 GB. | Llama 3.2 Community |
| 6 GB | `qwen3:1.7b` | 1.7B | Qwen3 | Step up from 0.6b with real multi-turn ability. | Apache-2.0 |
| 6 GB | `llama3.2:3b` | 3.0B | Llama 3.2 | Solid general assistant at the 6 GB tier. | Llama 3.2 Community |
| 6 GB | `qwen3:4b` | 4.0B | Qwen3 | Strong all-rounder; hybrid thinking mode for harder prompts. | Apache-2.0 |
| 8 GB | `qwen2.5-coder:7b` | 7.0B | Qwen2.5-Coder | Best small local coding model. Fill-in-the-middle and repo-level context. | Apache-2.0 |
| 8 GB | `mistral` | 7.0B | Mistral | Fast, permissive, well-understood baseline. | Apache-2.0 |
| 8 GB | `deepseek-r1:7b` | 7.0B | DeepSeek-R1 | Distilled reasoning model; shows its working. | MIT |
| 12 GB | `qwen3:8b` | 8.0B | Qwen3 | The sweet spot for general local work once you have 12 GB. | Apache-2.0 |
| 16 GB | `deepseek-r1:14b` | 14.0B | DeepSeek-R1 | Reasoning at a size a 16 GB machine can actually hold. | MIT |
| 16 GB | `qwen3:14b` | 14.0B | Qwen3 | Strong general + coding model at 16 GB. | Apache-2.0 |
| 24 GB | `mistral-small` | 24.0B | Mistral Small | Near-frontier quality for a single consumer machine. | Apache-2.0 |
| 24 GB | `qwen3:30b-a3b` | 30.0B | Qwen3 MoE | Mixture-of-experts: 30B total but ~3B active, so it runs far faster than its size implies. | Apache-2.0 |
| 32 GB | `qwen2.5-coder:32b` | 32.0B | Qwen2.5-Coder | The strongest local coding model that fits 32 GB. | Apache-2.0 |
| 32 GB | `qwen3:32b` | 32.0B | Qwen3 | Largest dense Qwen3 for a 32 GB box. | Apache-2.0 |

## Repos, sized

Which catalog entries are worth installing at which tier — the advisor filters this live:

| Min RAM | Repo | Role | Why |
|---:|---|---|---|
| 4 GB | `google-gemini/cookbook` | reference | Gemini API recipes. No local footprint. |
| 4 GB | `google-gemini/gemini-cli` | hosted | Hosted Gemini. Listed because it is the right answer when RAM is the binding constraint. |
| 4 GB | `googleapis/python-genai` | client | Official Google GenAI Python SDK. |
| 4 GB | `microsoft/BitNet` | runtime | 1-bit CPU inference. The only realistic Microsoft path below 8 GB. |
| 4 GB | `microsoft/PhiCookBook` | reference | Recipes and docs for the Phi family. No runtime cost. |
| 4 GB | `ollama/ollama` | runtime | The runtime everything else here assumes. Install this first. |
| 4 GB | `ollama/ollama-js` | client | Node/TypeScript client. |
| 4 GB | `ollama/ollama-python` | client | Python client. Negligible footprint of its own. |
| 6 GB | `google/gemma.cpp` | runtime | Minimal C++ Gemma runtime; lighter than a full stack. |
| 8 GB | `google-deepmind/gemma` | reference | Reference Gemma implementations and weights guidance. |
| 8 GB | `microsoft/foundry-local` | runtime | Local Foundry runtime with hardware-aware model selection built in. |
| 8 GB | `microsoft/onnxruntime-genai` | runtime | ONNX generative runtime; best CPU/NPU path on Windows. |
| 16 GB | `microsoft/Olive` | tooling | Model optimisation and quantisation. Needs headroom to convert models. |

See [`repo-lists/local-models.txt`](../repo-lists/local-models.txt) for the full lane.

## Regenerating this page

Both this document and `docs/hardware-profiles.json` are generated, so the tables cannot drift
from the data. Change the model list in the generator, re-run it, then re-run the tests.
