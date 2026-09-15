"""Render the four arms of the 600-token test, from this repository's real hook.

Run setup first (setup.ps1 or setup.sh); it installs graphify, indexes this
repository and calls this script.

    python benchmarks/run-it-yourself/harness/build_arms.py

writes arms/<task>/<arm>.prompt.md, one file per arm per task. Each file is the
complete prompt: paste it into any assistant, or feed it to a CLI.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

KIT = pathlib.Path(__file__).resolve().parents[1]
ROOT = KIT.parents[1]
HOOK = ROOT / "scripts" / "hooks" / "skill_pipeline.py"
ARMS = KIT / "arms"


def graphify_path() -> str:
    found = shutil.which("graphify")
    if found:
        return found
    for candidate in (pathlib.Path.home() / ".graphify" / "venv" / "Scripts" / "graphify.exe",
                      pathlib.Path.home() / ".graphify" / "venv" / "bin" / "graphify",
                      pathlib.Path.home() / ".local" / "bin" / "graphify"):
        if candidate.exists():
            return str(candidate)
    return "graphify"          # on PATH once installed; the card still reads correctly


def hook_context(prompt: str, mode: str, session: str) -> str:
    """Ask the repository's own hook what it would inject for this prompt."""
    with tempfile.TemporaryDirectory(prefix="riy-") as store:
        env = dict(os.environ, MASTER_REPO_GOAL_DIR=store, MASTER_HARNESS_MODE=mode)
        payload = json.dumps({"prompt": prompt, "session_id": session})
        out = subprocess.run([sys.executable, str(HOOK)], input=payload, env=env,
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        for variant in {store, os.path.normpath(store), pathlib.Path(store).as_posix()}:
            context = context.replace(variant, "<goal-store>")
    for required in ("Standing pipeline", "TOKEN LIMIT: 600"):
        if required not in context:
            raise SystemExit(f"the {mode} context is missing {required!r}; is the repo intact?")
    return context


def main() -> None:
    config = json.loads((KIT / "prompts" / "tasks.json").read_text(encoding="utf-8"))
    card = config["tool_card"].replace("{GRAPHIFY}", graphify_path())
    manifest = {"limit": config["limit"], "tasks": {}}
    for task, spec in config["tasks"].items():
        (ARMS / task).mkdir(parents=True, exist_ok=True)
        manifest["tasks"][task] = {}
        for arm, arm_spec in config["arms"].items():
            parts = []
            if arm_spec["harness"]:
                typed = config["limit_command"] + spec["prompt"]
                parts.append("<system-reminder>\nUserPromptSubmit hook additional context: "
                             + hook_context(typed, arm_spec["harness"], f"riy-{task}-{arm}")
                             + "\n</system-reminder>")
                parts.append(typed)
            else:
                parts.append(spec["prompt"])
                parts.append(config["limit_plain"])
            if arm_spec["graphify"]:
                parts.append(card)
            if arm_spec.get("forbid_graphify"):
                parts.append(config["forbid_line"])
            parts.append(config["delivery"])
            prompt = "\n\n".join(parts)
            (ARMS / task / f"{arm}.prompt.md").write_text(prompt, encoding="utf-8")
            manifest["tasks"][task][arm] = {
                "bytes": len(prompt.encode("utf-8")),
                "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            }
    (ARMS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for task, arms in manifest["tasks"].items():
        print(task, {arm: data["bytes"] for arm, data in arms.items()})
    print(f"\nprompts written to {ARMS}")
    print("paste one into any assistant, save the reply under answers/, then run harness/score.py")


if __name__ == "__main__":
    main()
