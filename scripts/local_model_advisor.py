#!/usr/bin/env python3
"""Inspect this machine, recommend a local model, and install it safely.

    python scripts/local_model_advisor.py                 # inspect + recommend
    python scripts/local_model_advisor.py --install       # install the recommendation
    python scripts/local_model_advisor.py --install gemma3:12b
    python scripts/local_model_advisor.py --list

Safety model, in two tiers:

  Tier 1 -- the recommendation, and anything else that FITS this machine.
            Installs after a normal y/N confirmation.

  Tier 2 -- anything that does NOT fit. Blocked by default. Requires BOTH
            --i-accept-the-risk AND typing the exact acceptance phrase, and prints
            what will actually go wrong first.

The second tier exists because the failure mode is genuinely nasty: an oversized
model does not politely refuse, it swaps. On Windows that can mean minutes of an
unresponsive desktop. Someone should have to mean it.

Sizing comes from docs/hardware-profiles.json, the same data the web advisor uses.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = ROOT / "docs" / "hardware-profiles.json"
ACCEPT_PHRASE = "I ACCEPT THE RISK"

BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"
GREEN, AMBER, RED = "\033[32m", "\033[33m", "\033[31m"


def colour(text: str, code: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"{code}{text}{RESET}"


# --------------------------------------------------------------------- system probe
def total_ram_gb() -> float | None:
    """Installed RAM, without requiring psutil."""
    try:  # Linux / WSL
        meminfo = pathlib.Path("/proc/meminfo")
        if meminfo.exists():
            for line in meminfo.read_text().splitlines():
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) / (1024 ** 2)
    except OSError:
        pass

    system = platform.system()
    try:
        if system == "Windows":
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
                capture_output=True, text=True, timeout=25)
            value = out.stdout.strip()
            if value.isdigit():
                return int(value) / (1024 ** 3)
        elif system == "Darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"],
                                 capture_output=True, text=True, timeout=15)
            if out.stdout.strip().isdigit():
                return int(out.stdout.strip()) / (1024 ** 3)
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def gpu_vram_gb() -> tuple[str | None, float | None]:
    """Discrete GPU name and VRAM, if nvidia-smi can tell us. Best effort."""
    if not shutil.which("nvidia-smi"):
        return None, None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
        first = out.stdout.strip().splitlines()[0]
        name, mib = [p.strip() for p in first.split(",")]
        return name, int(mib) / 1024
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None, None


def free_disk_gb() -> float | None:
    try:
        return shutil.disk_usage(pathlib.Path.home()).free / (1024 ** 3)
    except OSError:
        return None


def platform_key() -> str:
    return {"Windows": "windows", "Darwin": "macos"}.get(platform.system(), "linux")


def ollama_state() -> str:
    if not shutil.which("ollama"):
        return "not installed"
    try:
        subprocess.run(["ollama", "list"], capture_output=True, timeout=10, check=True)
        return "running"
    except subprocess.CalledProcessError:
        return "installed, daemon not responding"
    except (OSError, subprocess.SubprocessError):
        return "installed, status unknown"


# --------------------------------------------------------------------- sizing
def load_profiles() -> dict:
    if not PROFILES.exists():
        sys.exit(f"error: {PROFILES} is missing")
    return json.loads(PROFILES.read_text(encoding="utf-8"))


def required_gb(model: dict, formula: dict) -> float:
    per_b = (formula["bytes_per_param"][model["quant"]]
             + formula["overhead_per_b_gb"] + formula["kv_cache_per_b_4k_gb"])
    return model["params_b"] * per_b + formula["overhead_base_gb"]


def usable_gb(ram: float, formula: dict, key: str, vram: float | None) -> float:
    # VRAM substitutes for system RAM on the weights term, so a discrete GPU
    # effectively enlarges the budget. Counted conservatively at 85%.
    base = ram - formula["os_reserve_gb"][key]
    return base + (vram * 0.85 if vram else 0.0)


def fits(model: dict, budget: float, formula: dict, ram: float) -> bool:
    if model.get("why_special"):
        return model["min_ram_gb"] <= ram
    return required_gb(model, formula) <= budget


# --------------------------------------------------------------------- reporting
def describe_system(data: dict) -> dict:
    ram = total_ram_gb()
    if ram is None:
        sys.exit("error: could not determine installed RAM on this system")
    key = platform_key()
    gpu_name, vram = gpu_vram_gb()
    formula = data["formula"]
    budget = usable_gb(ram, formula, key, vram)
    disk = free_disk_gb()

    print(f"\n{colour('System', BOLD)}")
    print(f"  OS               {platform.system()} {platform.release()} ({key})")
    print(f"  CPU              {platform.processor() or platform.machine()}")
    print(f"  Installed RAM    {ram:.1f} GB")
    print(f"  OS reserve       {formula['os_reserve_gb'][key]} GB")
    if gpu_name:
        print(f"  GPU              {gpu_name} ({vram:.1f} GB VRAM)")
    else:
        print(f"  GPU              {colour('none detected', DIM)} "
              f"{colour('(CPU inference only)', DIM)}")
    print(f"  Free disk        {f'{disk:.0f} GB' if disk else 'unknown'}")
    print(f"  Ollama           {ollama_state()}")
    print(f"  {colour('Budget for a model', BOLD)}  {budget:.1f} GB")
    return {"ram": ram, "key": key, "vram": vram, "budget": budget, "disk": disk}


def recommend(data: dict, env: dict) -> dict | None:
    """Largest chat model that fits. Size correlates with capability within a tier."""
    formula = data["formula"]
    chat = [m for m in data["models"]
            if m["id"] not in {"nomic-embed", "embeddinggemma"}
            and m["runtime"] == "ollama"]
    fitting = [m for m in chat if fits(m, env["budget"], formula, env["ram"])]
    if not fitting:
        return None
    return max(fitting, key=lambda m: m["params_b"])


def report(data: dict, env: dict) -> dict | None:
    formula = data["formula"]
    pick = recommend(data, env)

    print(f"\n{colour('Recommendation', BOLD)}")
    if not pick:
        print(colour("  No local chat model fits this machine.", RED))
        print("  After the OS takes its share there is not enough memory left for even")
        print("  the smallest conversational model. This is the honest answer, not a")
        print("  configuration problem.")
        print(f"\n  {colour('Use a hosted model instead:', BOLD)}  npx https://github.com/google-gemini/gemini-cli")
        return None

    need = required_gb(pick, formula)
    print(f"  {colour(pick['tag'], GREEN)}  ({pick['params_b']}B {pick['quant'].upper()}, {pick['vendor']})")
    print(f"  {pick['use']}")
    print(f"  Needs ~{need:.1f} GB of your {env['budget']:.1f} GB budget · {pick['license']}")
    print(f"\n  {colour('Install it:', BOLD)}  python scripts/local_model_advisor.py --install")

    by_vendor: dict[str, list[str]] = {}
    for model in data["models"]:
        if fits(model, env["budget"], formula, env["ram"]):
            by_vendor.setdefault(model["vendor"], []).append(model["tag"])
    print(f"\n{colour('Also fits', BOLD)}")
    for vendor in ("Microsoft", "Google", "Ollama"):
        tags = by_vendor.get(vendor, [])
        print(f"  {vendor:<10} {', '.join(tags) if tags else colour('nothing at this size', DIM)}")
    return pick


# --------------------------------------------------------------------- install
def run_install(tag: str) -> int:
    if not shutil.which("ollama"):
        print(colour("\nOllama is not installed.", RED))
        print("  Windows:  winget install Ollama.Ollama")
        print("  macOS:    brew install ollama")
        print("  Linux:    curl -fsSL https://ollama.com/install.sh | sh")
        return 1
    print(f"\n$ ollama pull {tag}\n")
    try:
        return subprocess.run(["ollama", "pull", tag]).returncode
    except (OSError, subprocess.SubprocessError) as exc:
        print(colour(f"install failed: {exc}", RED))
        return 1


def confirm(prompt: str) -> bool:
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in {"y", "yes"}
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def oversized_gate(model: dict, env: dict, need: float, accepted_flag: bool) -> bool:
    """Tier 2. Everything here is designed to be hard to do by accident."""
    over = need - env["budget"]
    print(f"\n{colour('=' * 68, RED)}")
    print(colour("  THIS MODEL DOES NOT FIT THIS MACHINE", RED))
    print(colour("=" * 68, RED))
    print(f"\n  {model['tag']} needs ~{need:.1f} GB. You have ~{env['budget']:.1f} GB.")
    print(f"  Short by {colour(f'{over:.1f} GB', RED)}.\n")
    print("  What will actually happen:")
    print("    - The OS falls back to swapping to disk to make room.")
    print("    - Generation drops from words-per-second to seconds-per-word.")
    if env["key"] == "windows":
        print("    - On Windows the desktop can become unresponsive for minutes.")
    print("    - Other applications may be killed by the memory manager.")
    print("    - Heavy sustained writes to your system drive.\n")
    print("  This is not a warning you can shrug off: it is the documented behaviour")
    print("  of loading weights larger than available memory.\n")

    if not accepted_flag:
        print(colour("  Blocked.", RED)
              + " Re-run with --i-accept-the-risk if you still want to proceed.")
        return False

    print(f"  To continue, type exactly:  {colour(ACCEPT_PHRASE, BOLD)}")
    try:
        typed = input("  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if typed != ACCEPT_PHRASE:
        print(colour("  Phrase did not match. Nothing was installed.", RED))
        return False
    print(colour("\n  Risk accepted. Proceeding.\n", AMBER))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--install", nargs="?", const="__recommended__", metavar="TAG",
                        help="install the recommendation, or a specific tag")
    parser.add_argument("--list", action="store_true", help="list every known model and whether it fits")
    parser.add_argument("--i-accept-the-risk", action="store_true", dest="accept",
                        help="permit installing a model too large for this machine")
    parser.add_argument("--yes", "-y", action="store_true", help="skip the confirmation for a model that fits")
    args = parser.parse_args()

    data = load_profiles()
    formula = data["formula"]
    env = describe_system(data)

    if args.list:
        print(f"\n{colour('All known models', BOLD)}")
        for model in sorted(data["models"], key=lambda m: m["params_b"]):
            ok = fits(model, env["budget"], formula, env["ram"])
            mark = colour("fits", GREEN) if ok else colour("too big", RED)
            need = required_gb(model, formula)
            print(f"  {mark:<18} {model['tag']:<26} {model['params_b']:>5}B  ~{need:5.1f} GB  {model['vendor']}")
        return 0

    pick = report(data, env)
    if args.install is None:
        return 0

    if args.install == "__recommended__":
        if not pick:
            print(colour("\nNothing to install: no model fits this machine.", RED))
            return 1
        target = pick
    else:
        target = next((m for m in data["models"] if m["tag"] == args.install), None)
        if target is None:
            print(colour(f"\nUnknown model tag: {args.install}", RED))
            print("Run --list to see every tag this advisor knows about.")
            return 1

    need = required_gb(target, formula)
    if fits(target, env["budget"], formula, env["ram"]):
        print(f"\n{colour('Ready to install', BOLD)}  {target['tag']}  "
              f"(~{need:.1f} GB of {env['budget']:.1f} GB) · {target['license']}")
        if not args.yes and not confirm("Proceed?"):
            print("Cancelled.")
            return 0
    elif not oversized_gate(target, env, need, args.accept):
        return 1

    return run_install(target["tag"])


if __name__ == "__main__":
    sys.exit(main())
