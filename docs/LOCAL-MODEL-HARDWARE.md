# Local Models & Hardware Fit

**Question this page answers:** *"I have N GB of RAM. What can I actually run, and which
repos in this catalog are worth installing on this machine?"*

The command center has an interactive version of this under the **Local Models** tab.
Both read the same file: [`docs/hardware-profiles.json`](hardware-profiles.json).

## Scope

Deliberately narrow — three vendors only:

| Vendor | Why it is here |
|---|---|
| **Ollama** | The default local runtime. One binary, `ollama pull`, done. |
| **Microsoft** | The only credible sub-8 GB path (BitNet, ONNX/NPU) plus the Phi small-model family. |
| **Google / Gemini** | Gemma open weights, `gemma.cpp`, and the hosted Gemini fallback for when RAM is the binding constraint. |

General-purpose serving stacks (llama.cpp, vLLM, SGLang) are a different problem and live in
[`repo-lists/llm-models-serving.txt`](../repo-lists/llm-models-serving.txt).

## How the numbers are produced

**These are computed estimates, not benchmarks.** The arithmetic is published so you can
disagree with it:

```
weights_gb  = params_b × bytes_per_param[quant]      # q4 = 0.60, q8 = 1.10, fp16 = 2.05
required_gb = weights_gb + 0.5 (runtime) + 0.35 (KV cache @ 4k ctx)
usable_gb   = total_ram − os_reserve                 # Windows 3.0, macOS 2.5, Linux 1.5
a model fits when required_gb ≤ usable_gb
```

`tests/test_hardware_profiles.py` re-derives every `min_ram_gb` in the JSON from this formula
and fails if the data drifts. A recommendation that says "fits" is arithmetic, not optimism.

Two things the formula does **not** model, and you should adjust for yourself:

- **Discrete GPU VRAM.** VRAM substitutes for system RAM on the weights term. A 16 GB machine
  with an 8 GB GPU behaves closer to a 24 GB machine.
- **Context length.** The KV-cache term assumes ~4k tokens. Long context costs meaningfully more;
  roughly add 0.35 GB per additional 4k for a mid-size model.

## The tiers

| RAM | Usable (Win) | Verdict | What it means |
|---:|---:|---|---|
| 4 GB | 1.0 | **severely constrained** | No local chat model fits. Use hosted Gemini. |
| 6 GB | 3.0 | tiny models only | 0.3B–1B assistants. Classification and extraction, not conversation. |
| 8 GB | 5.0 | small models, usable | First genuinely useful tier. 3–4B Q4. |
| 12 GB | 9.0 | comfortable small | 4B with room; 12B fits but context is tight. |
| 16 GB | 13.0 | **solid daily driver** | 12–14B Q4 with real context. Sweet spot for local coding help. |
| 24 GB | 21.0 | strong | 27B-class Q4, plus embeddings alongside. |
| 32 GB | 29.0 | excellent | 27–32B Q4 long context, or a full local RAG stack resident at once. |

### The 4 GB answer nobody wants

A 4 GB Windows 11 machine has roughly 1 GB free after the OS. Even a 270M-parameter model plus
runtime overhead needs ~1.0 GB, leaving nothing. **The honest recommendation at 4 GB is to not
run models locally** and use `google-gemini/gemini-cli` against the hosted API. The advisor is
written to say this rather than recommend something that will swap.

## Model shortlist

| Model | Vendor | Params | Min RAM | Runtime | Good for |
|---|---|---:|---:|---|---|
| `gemma3:270m` | Google | 0.27B | 6 GB | Ollama | Classification, tagging |
| `gemma3:1b` | Google | 1B | 6 GB | Ollama | Short summarisation, extraction |
| BitNet b1.58 | Microsoft | 2.4B | 6 GB | `bitnet.cpp` | Best sub-8 GB option; 1.58-bit weights |
| `phi4-mini` | Microsoft | 3.8B | 8 GB | Ollama | Reasoning-tuned small model |
| `gemma3:4b` | Google | 4B | 8 GB | Ollama | General assistant, vision input |
| `gemma3:12b` | Google | 12B | 12 GB | Ollama | Multi-step instructions, code review |
| `phi4` | Microsoft | 14B | 16 GB | Ollama | Best MS open-weight reasoning at 16 GB |
| `gemma3:27b` | Google | 27B | 24 GB | Ollama | Genuine local coding assistance |
| `nomic-embed-text` | Ollama | 0.14B | 6 GB | Ollama | RAG embeddings, runs alongside chat |

Verify a tag before relying on it — model libraries move faster than this document:

```bash
ollama show gemma3:4b
```

## Licensing note

Gemma models ship under the **Gemma Terms of Use**, not a standard OSI licence. There are use
restrictions. Phi and BitNet are MIT. Read the terms before shipping anything built on Gemma
into a product.

## Repos, sized

Which catalog entries are worth installing at which tier — the advisor filters this list live:

- **4 GB+:** `ollama/ollama`, clients, `microsoft/PhiCookBook`, `google-gemini/gemini-cli` (hosted)
- **6 GB+:** `microsoft/BitNet`, `google/gemma.cpp`
- **8 GB+:** `microsoft/foundry-local`, `microsoft/onnxruntime-genai`, `google-deepmind/gemma`
- **16 GB+:** `microsoft/Olive` (quantisation needs headroom to convert)

See [`repo-lists/local-models.txt`](../repo-lists/local-models.txt) for the full lane.
