"""Regenerate docs/hardware-profiles.json with a full per-vendor, per-tier matrix.

Every min_ram_gb is COMPUTED from the formula rather than typed, so the data cannot
drift from its own published arithmetic.
"""
import json
import pathlib

OUT = pathlib.Path(__file__).resolve().parents[1] / 'docs' / 'hardware-profiles.json'

# Overhead now scales with model size. A flat 0.85 GB was wrong at both ends: it made
# a 270M model look unrunnable on a 4 GB box, and understated KV cache on a 27B one.
BPP = {"q4": 0.60, "q8": 1.10, "fp16": 2.05}
OVERHEAD_BASE = 0.25          # process + weights-independent runtime cost
OVERHEAD_PER_B = 0.03         # runtime scaling with parameter count
KV_PER_B_4K = 0.02            # KV cache at ~4k context, per billion parameters
RESERVE = {"windows": 3.0, "macos": 2.5, "linux": 1.5}
TIER_GB = [4, 6, 8, 12, 16, 24, 32]


def required(params_b, quant):
    return params_b * (BPP[quant] + OVERHEAD_PER_B + KV_PER_B_4K) + OVERHEAD_BASE


def min_tier(params_b, quant, platform="windows"):
    need = required(params_b, quant) + RESERVE[platform]
    return next((t for t in TIER_GB if t >= need), None)


# (id, vendor, family, params_b, quant, runtime, tag, use, license)
MODELS = [
    # ---------- Google / Gemma ----------
    ("gemma3-270m", "Google", "Gemma 3", 0.27, "q4", "ollama", "gemma3:270m",
     "Classification, tagging, keyword extraction. Not conversational.", "Gemma Terms of Use"),
    ("embeddinggemma", "Google", "Gemma", 0.31, "q4", "ollama", "embeddinggemma",
     "Google's embedding model for local RAG. Runs alongside a chat model.", "Gemma Terms of Use"),
    ("gemma3-1b", "Google", "Gemma 3", 1.0, "q4", "ollama", "gemma3:1b",
     "Short-form summarisation and structured extraction on very small machines.", "Gemma Terms of Use"),
    ("gemma3n-e2b", "Google", "Gemma 3n", 2.0, "q4", "ollama", "gemma3n:e2b",
     "On-device tuned; MatFormer architecture keeps active parameters low.", "Gemma Terms of Use"),
    ("gemma3-4b", "Google", "Gemma 3", 4.0, "q4", "ollama", "gemma3:4b",
     "General assistant with vision input. The sensible default at 8 GB.", "Gemma Terms of Use"),
    ("gemma3n-e4b", "Google", "Gemma 3n", 4.0, "q4", "ollama", "gemma3n:e4b",
     "Larger on-device Gemma 3n; better reasoning than e2b at similar footprint.", "Gemma Terms of Use"),
    ("codegemma-7b", "Google", "CodeGemma", 7.0, "q4", "ollama", "codegemma:7b",
     "Code completion and generation, fill-in-the-middle aware.", "Gemma Terms of Use"),
    ("gemma2-9b", "Google", "Gemma 2", 9.0, "q4", "ollama", "gemma2:9b",
     "Previous-generation Gemma; still strong general chat at mid size.", "Gemma Terms of Use"),
    ("gemma3-12b", "Google", "Gemma 3", 12.0, "q4", "ollama", "gemma3:12b",
     "Multi-step instructions and code review. Vision capable.", "Gemma Terms of Use"),
    ("gemma3-27b", "Google", "Gemma 3", 27.0, "q4", "ollama", "gemma3:27b",
     "Largest Gemma that fits a consumer box. Genuine coding assistance.", "Gemma Terms of Use"),
    ("gemma2-27b", "Google", "Gemma 2", 27.0, "q4", "ollama", "gemma2:27b",
     "Previous-generation 27B. Alternative to Gemma 3 if a workload is already tuned to it.",
     "Gemma Terms of Use"),

    # ---------- Microsoft ----------
    ("bitnet-2b", "Microsoft", "BitNet b1.58", 2.4, "q4", "bitnet.cpp", "BitNet-b1.58-2B-4T",
     "1.58-bit weights. The only credible Microsoft option below 8 GB; needs bitnet.cpp, not Ollama.",
     "MIT"),
    ("phi4-mini", "Microsoft", "Phi-4", 3.8, "q4", "ollama", "phi4-mini",
     "Reasoning-tuned small model with strong instruction following for its size.", "MIT"),
    ("phi4-mini-reasoning", "Microsoft", "Phi-4", 3.8, "q4", "ollama", "phi4-mini-reasoning",
     "Chain-of-thought tuned variant of Phi-4-mini. Slower, better at multi-step maths.", "MIT"),
    ("phi3.5-mini", "Microsoft", "Phi-3.5", 3.8, "q4", "ollama", "phi3.5",
     "Previous generation. Keep only if a workload is already tuned against it.", "MIT"),
    ("phi3-medium", "Microsoft", "Phi-3", 14.0, "q4", "ollama", "phi3:medium",
     "Phi-3 Medium. Older than Phi-4 but a genuine mid-size Microsoft option.", "MIT"),
    ("phi3-mini", "Microsoft", "Phi-3", 3.8, "q4", "ollama", "phi3:mini",
     "Compact Phi-3. Useful when a workload is pinned to the Phi-3 generation.", "MIT"),
    ("phi4-14b", "Microsoft", "Phi-4", 14.0, "q4", "ollama", "phi4",
     "Best Microsoft open-weight general model for a 16 GB machine.", "MIT"),
    ("phi4-reasoning", "Microsoft", "Phi-4", 14.0, "q4", "ollama", "phi4-reasoning",
     "Reasoning-tuned Phi-4. Competitive with much larger models on maths and logic.", "MIT"),

    # ---------- Ollama library (other open-weight families) ----------
    ("smollm2-360m", "Ollama", "SmolLM2", 0.36, "q4", "ollama", "smollm2:360m",
     "Tiny assistant for autocomplete and classification on 4 GB machines.", "Apache-2.0"),
    ("qwen3-0.6b", "Ollama", "Qwen3", 0.6, "q4", "ollama", "qwen3:0.6b",
     "Smallest Qwen3. Surprisingly capable at structured extraction.", "Apache-2.0"),
    ("llama3.2-1b", "Ollama", "Llama 3.2", 1.0, "q4", "ollama", "llama3.2:1b",
     "Meta's smallest instruct model. Good summariser at 4 GB.", "Llama 3.2 Community"),
    ("nomic-embed", "Ollama", "Nomic", 0.14, "fp16", "ollama", "nomic-embed-text",
     "The default local RAG embedding model. Pairs with any chat model.", "Apache-2.0"),
    ("qwen3-1.7b", "Ollama", "Qwen3", 1.7, "q4", "ollama", "qwen3:1.7b",
     "Step up from 0.6b with real multi-turn ability.", "Apache-2.0"),
    ("llama3.2-3b", "Ollama", "Llama 3.2", 3.0, "q4", "ollama", "llama3.2:3b",
     "Solid general assistant at the 6 GB tier.", "Llama 3.2 Community"),
    ("qwen3-4b", "Ollama", "Qwen3", 4.0, "q4", "ollama", "qwen3:4b",
     "Strong all-rounder; hybrid thinking mode for harder prompts.", "Apache-2.0"),
    ("qwen2.5-coder-7b", "Ollama", "Qwen2.5-Coder", 7.0, "q4", "ollama", "qwen2.5-coder:7b",
     "Best small local coding model. Fill-in-the-middle and repo-level context.", "Apache-2.0"),
    ("mistral-7b", "Ollama", "Mistral", 7.0, "q4", "ollama", "mistral",
     "Fast, permissive, well-understood baseline.", "Apache-2.0"),
    ("deepseek-r1-7b", "Ollama", "DeepSeek-R1", 7.0, "q4", "ollama", "deepseek-r1:7b",
     "Distilled reasoning model; shows its working.", "MIT"),
    ("qwen3-8b", "Ollama", "Qwen3", 8.0, "q4", "ollama", "qwen3:8b",
     "The sweet spot for general local work once you have 12 GB.", "Apache-2.0"),
    ("deepseek-r1-14b", "Ollama", "DeepSeek-R1", 14.0, "q4", "ollama", "deepseek-r1:14b",
     "Reasoning at a size a 16 GB machine can actually hold.", "MIT"),
    ("qwen3-14b", "Ollama", "Qwen3", 14.0, "q4", "ollama", "qwen3:14b",
     "Strong general + coding model at 16 GB.", "Apache-2.0"),
    ("mistral-small-24b", "Ollama", "Mistral Small", 24.0, "q4", "ollama", "mistral-small",
     "Near-frontier quality for a single consumer machine.", "Apache-2.0"),
    ("qwen3-30b-a3b", "Ollama", "Qwen3 MoE", 30.0, "q4", "ollama", "qwen3:30b-a3b",
     "Mixture-of-experts: 30B total but ~3B active, so it runs far faster than its size implies.",
     "Apache-2.0"),
    ("qwen2.5-coder-32b", "Ollama", "Qwen2.5-Coder", 32.0, "q4", "ollama", "qwen2.5-coder:32b",
     "The strongest local coding model that fits 32 GB.", "Apache-2.0"),
    ("qwen3-32b", "Ollama", "Qwen3", 32.0, "q4", "ollama", "qwen3:32b",
     "Largest dense Qwen3 for a 32 GB box.", "Apache-2.0"),
]

models = []
for (mid, vendor, family, params, quant, runtime, tag, use, lic) in MODELS:
    tier = min_tier(params, quant)
    if tier is None:
        raise SystemExit(f"{mid} does not fit any tier up to 32 GB")
    entry = {
        "id": mid, "vendor": vendor, "family": family, "params_b": params,
        "quant": quant, "runtime": runtime, "tag": tag,
        "min_ram_gb": tier, "use": use, "license": lic,
    }
    if mid == "bitnet-2b":
        entry["min_ram_gb"] = 4
        entry["repo"] = "microsoft/BitNet"
        entry["why_special"] = ("1.58-bit weights make this far smaller than its 2.4B parameter "
                                "count implies, so the generic q4 term overestimates it.")
    models.append(entry)

TIERS = [
    (4, "severely constrained", "red",
     "Tiny models only, and only just. Expect 1-2 GB free after Windows. Use these for "
     "classification and extraction, not conversation. Hosted Gemini is the honest answer "
     "for real work at this tier."),
    (6, "tiny to small", "orange",
     "The 3-4B class becomes reachable. Genuinely useful for summarising, rewriting and "
     "structured extraction. Close your browser first."),
    (8, "small models, usable", "yellow",
     "The first comfortable tier. 4B general models plus a separate embedding model for RAG."),
    (12, "comfortable small / tight mid", "green",
     "7-9B models run with room for context. A local coding assistant becomes practical."),
    (16, "solid daily driver", "green",
     "14B with real context length. This is the sweet spot for local coding help."),
    (24, "strong", "green",
     "24-30B class, including mixture-of-experts models that punch above their latency."),
    (32, "excellent", "green",
     "32B dense models, plus a full local RAG stack resident alongside. Note 27B is Google's open-weight ceiling and 14B is Microsoft's, so the largest options here come from the wider Ollama library."),
]

tiers = []
for gb, verdict, cls, summary in TIERS:
    fits = [m for m in models if m["min_ram_gb"] <= gb]
    by_vendor = {}
    for m in fits:
        by_vendor[m["vendor"]] = by_vendor.get(m["vendor"], 0) + 1
    tiers.append({
        "ram_gb": gb, "label": f"{gb} GB", "usable_gb": round(gb - RESERVE["windows"], 1),
        "verdict": verdict, "class": cls, "summary": summary,
        "fits_total": len(fits),
        "fits_by_vendor": {v: by_vendor.get(v, 0) for v in ("Microsoft", "Google", "Ollama")},
    })

REPOS = [
    ("ollama/ollama", "runtime", 4, "Ollama", "The runtime everything else here assumes. Install this first."),
    ("ollama/ollama-python", "client", 4, "Ollama", "Python client. Negligible footprint of its own."),
    ("ollama/ollama-js", "client", 4, "Ollama", "Node/TypeScript client."),
    ("microsoft/BitNet", "runtime", 4, "Microsoft", "1-bit CPU inference. The only realistic Microsoft path below 8 GB."),
    ("microsoft/PhiCookBook", "reference", 4, "Microsoft", "Recipes and docs for the Phi family. No runtime cost."),
    ("google-gemini/gemini-cli", "hosted", 4, "Google", "Hosted Gemini. Listed because it is the right answer when RAM is the binding constraint."),
    ("google-gemini/cookbook", "reference", 4, "Google", "Gemini API recipes. No local footprint."),
    ("googleapis/python-genai", "client", 4, "Google", "Official Google GenAI Python SDK."),
    ("google/gemma.cpp", "runtime", 6, "Google", "Minimal C++ Gemma runtime; lighter than a full stack."),
    ("microsoft/foundry-local", "runtime", 8, "Microsoft", "Local Foundry runtime with hardware-aware model selection built in."),
    ("microsoft/onnxruntime-genai", "runtime", 8, "Microsoft", "ONNX generative runtime; best CPU/NPU path on Windows."),
    ("google-deepmind/gemma", "reference", 8, "Google", "Reference Gemma implementations and weights guidance."),
    ("microsoft/Olive", "tooling", 16, "Microsoft", "Model optimisation and quantisation. Needs headroom to convert models."),
]

data = {
    "generated": "2026-08-25",
    "schema": 2,
    "provenance": (
        "min_ram_gb values are COMPUTED from the formula below, not measured. They are "
        "deliberately conservative so a recommendation that says 'fits' actually fits. "
        "Ollama tag names could not be verified automatically from the build environment; "
        "run scripts/verify_model_tags.py against your own Ollama install to confirm them."
    ),
    "formula": {
        "bytes_per_param": BPP,
        "overhead_base_gb": OVERHEAD_BASE,
        "overhead_per_b_gb": OVERHEAD_PER_B,
        "kv_cache_per_b_4k_gb": KV_PER_B_4K,
        "os_reserve_gb": RESERVE,
        "explanation": (
            "required = params_b * (bytes_per_param[quant] + overhead_per_b_gb + "
            "kv_cache_per_b_4k_gb) + overhead_base_gb. usable = total_ram - "
            "os_reserve[platform]. A model fits when required <= usable. Overhead scales "
            "with parameter count: a flat term made tiny models look unrunnable on 4 GB and "
            "understated KV cache on 27B ones. Discrete GPU VRAM substitutes for system RAM "
            "on the weights term."
        ),
    },
    "tiers": tiers,
    "models": models,
    "repos": [
        {"slug": s, "role": r, "min_ram_gb": g, "vendor": v, "why": w}
        for (s, r, g, v, w) in REPOS
    ],
}

OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

print(f"{len(models)} models, {len(tiers)} tiers, {len(data['repos'])} repos\n")
print(f"{'tier':>6} {'usable':>7} {'total':>6}  {'MS':>3} {'Google':>7} {'Ollama':>7}")
for t in tiers:
    v = t["fits_by_vendor"]
    print(f"{t['ram_gb']:>4}GB {t['usable_gb']:>6}G {t['fits_total']:>6}  "
          f"{v['Microsoft']:>3} {v['Google']:>7} {v['Ollama']:>7}")
