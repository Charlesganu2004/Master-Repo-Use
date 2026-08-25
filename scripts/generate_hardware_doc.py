import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
d = json.loads((ROOT / 'docs' / 'hardware-profiles.json').read_text(encoding='utf-8'))
f = d['formula']

tier_rows = []
for t in d['tiers']:
    v = t['fits_by_vendor']
    tier_rows.append(
        f"| **{t['ram_gb']} GB** | {t['usable_gb']} | {t['verdict']} | {t['fits_total']} "
        f"| {v['Microsoft']} | {v['Google']} | {v['Ollama']} |")

def table(vendor):
    rows = [m for m in d['models'] if m['vendor'] == vendor]
    rows.sort(key=lambda m: (m['min_ram_gb'], m['params_b']))
    out = ["| Min RAM | Tag | Params | Family | Good for | Licence |",
           "|---:|---|---:|---|---|---|"]
    for m in rows:
        use = m['use'].replace('|', '/')
        out.append(f"| {m['min_ram_gb']} GB | `{m['tag']}` | {m['params_b']}B | {m['family']} "
                   f"| {use} | {m['license']} |")
    return "\n".join(out)

doc = f"""# Local Models & Hardware Fit

**Question this page answers:** *"I have N GB of RAM. What can I actually run, and which
repos in this catalog are worth installing on this machine?"*

The command center has an interactive version under the **Local Models** tab, including an
install checker. Both read the same file: [`docs/hardware-profiles.json`](hardware-profiles.json)
— **{len(d['models'])} models** across three vendors, sized against seven RAM tiers.

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
per_b       = bytes_per_param[quant] + {f['overhead_per_b_gb']} (runtime) + {f['kv_cache_per_b_4k_gb']} (KV cache @ 4k)
required_gb = params_b × per_b + {f['overhead_base_gb']}
usable_gb   = total_ram − os_reserve          # Windows {f['os_reserve_gb']['windows']}, macOS {f['os_reserve_gb']['macos']}, Linux {f['os_reserve_gb']['linux']}
fits when   required_gb ≤ usable_gb
```

`bytes_per_param`: q4 = {f['bytes_per_param']['q4']}, q8 = {f['bytes_per_param']['q8']}, fp16 = {f['bytes_per_param']['fp16']}.

Overhead **scales with parameter count**. A flat term was wrong at both ends: it made a 270M
model look unrunnable on a 4 GB box and understated KV cache on a 27B one.

`tests/test_hardware_profiles.py` re-derives every `min_ram_gb` from this formula and fails if
the data drifts. A recommendation that says "fits" is arithmetic, not optimism.

Two things the formula does **not** model:

- **Discrete GPU VRAM** substitutes for system RAM on the weights term. A 16 GB machine with an
  8 GB GPU behaves closer to a 24 GB one.
- **Long context.** The KV term assumes ~4k tokens; add roughly
  {f['kv_cache_per_b_4k_gb']} GB per billion parameters for each additional 4k.

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
{chr(10).join(tier_rows)}

### The 4 GB answer

A 4 GB Windows machine has roughly 1 GB free once the OS has taken its share. Sub-1B models fit
and are genuinely useful for classification, tagging and extraction — but **nothing conversational
does**, and the advisor says so rather than recommending something that will swap. On Linux the
same box has ~2.5 GB usable and the picture improves noticeably.

Microsoft has no sub-1B open-weight model, so at 4 GB its only entry is BitNet, whose 1.58-bit
weights make it far smaller than its 2.4B parameter count implies.

## Microsoft

{table('Microsoft')}

Microsoft's open-weight ceiling is **14B**. Above 16 GB, the larger options come from Google or
the wider Ollama library.

## Google / Gemma

{table('Google')}

> **Licensing:** Gemma models ship under the **Gemma Terms of Use**, not an OSI licence, and carry
> real use restrictions. Read them before shipping a product built on Gemma.
> Google's open-weight ceiling is **27B**.

## Ollama library

{table('Ollama')}

## Repos, sized

Which catalog entries are worth installing at which tier — the advisor filters this live:

| Min RAM | Repo | Role | Why |
|---:|---|---|---|
"""

for r in sorted(d['repos'], key=lambda r: (r['min_ram_gb'], r['slug'])):
    doc += f"| {r['min_ram_gb']} GB | `{r['slug']}` | {r['role']} | {r['why']} |\n"

doc += """
See [`repo-lists/local-models.txt`](../repo-lists/local-models.txt) for the full lane.

## Regenerating this page

Both this document and `docs/hardware-profiles.json` are generated, so the tables cannot drift
from the data. Change the model list in the generator, re-run it, then re-run the tests.
"""

(ROOT / 'docs' / 'LOCAL-MODEL-HARDWARE.md').write_text(doc, encoding='utf-8')
print('LOCAL-MODEL-HARDWARE.md regenerated:', len(doc.splitlines()), 'lines')
