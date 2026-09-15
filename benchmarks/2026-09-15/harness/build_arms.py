"""Render the four arms of the graphify experiment, from the real hook.

Every harness arm's context is produced by scripts/hooks/skill_pipeline.py in the
mode that arm names, against an empty goal store, with the prompt the arm sends,
so the /token limit 400 command is parsed by the real parser and rule 15 is the
real rule 15. Nothing here restates the harness.

    python benchmarks/2026-09-15/harness/build_arms.py

writes arms/<task>/<arm>.prompt.md and arms/manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile

BENCH = pathlib.Path(__file__).resolve().parents[1]
ROOT = BENCH.parents[1]
HOOK = ROOT / "scripts" / "hooks" / "skill_pipeline.py"
ARMS = BENCH / "arms"
GRAPHIFY = pathlib.Path.home() / ".graphify" / "venv" / "Scripts" / "graphify.exe"


def hook_context(prompt: str, mode: str, session: str) -> str:
    with tempfile.TemporaryDirectory(prefix="graphify-bench-") as store:
        env = dict(os.environ, MASTER_REPO_GOAL_DIR=store, MASTER_HARNESS_MODE=mode)
        payload = json.dumps({"prompt": prompt, "session_id": session})
        out = subprocess.run([sys.executable, str(HOOK)], input=payload, env=env,
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        for variant in {store, os.path.normpath(store), pathlib.Path(store).as_posix()}:
            context = context.replace(variant, "<goal-store>")
    for required in ("Standing pipeline", "TOKEN LIMIT: 400"):
        if required not in context:
            raise SystemExit(f"{mode} context is missing {required!r}")
    if mode == "super" and "S10." not in context:
        raise SystemExit("super context is missing the chain")
    return context


def main() -> None:
    config = json.loads((BENCH / "prompts" / "tasks.json").read_text(encoding="utf-8"))
    if not GRAPHIFY.exists():
        raise SystemExit(f"graphify is not installed at {GRAPHIFY}")
    tool_card = config["tool_card"].replace("{GRAPHIFY}", str(GRAPHIFY))
    manifest = {"limit": config["limit"], "graphify": str(GRAPHIFY), "tasks": {}}
    for task, spec in config["tasks"].items():
        question = spec["prompt"].replace("{REPO}", config["repo"])
        (ARMS / task).mkdir(parents=True, exist_ok=True)
        manifest["tasks"][task] = {}
        for arm, arm_spec in config["arms"].items():
            parts = []
            if arm_spec["harness"]:
                # What the user types is the command plus the question; the hook
                # sees exactly that and answers with the context it would inject.
                typed = config["limit_command"] + question
                context = hook_context(typed, arm_spec["harness"], f"bench-{task}-{arm}")
                parts.append("<system-reminder>\nUserPromptSubmit hook additional context: "
                             + context + "\n</system-reminder>")
                parts.append(typed)
            else:
                parts.append(question)
                parts.append(config["limit_plain"])
            if arm_spec["graphify"]:
                parts.append(tool_card)
            if arm_spec.get("forbid_graphify"):
                parts.append(config["forbid_line"])
            parts.append(config["delivery"])
            prompt = "\n\n".join(parts)
            (ARMS / task / f"{arm}.prompt.md").write_text(prompt, encoding="utf-8")
            manifest["tasks"][task][arm] = {
                "promptBytes": len(prompt.encode("utf-8")),
                "contextBytes": len(parts[0].encode("utf-8")) if arm_spec["harness"] else 0,
                "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            }
    (ARMS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for task, arms in manifest["tasks"].items():
        print(task, {arm: data["promptBytes"] for arm, data in arms.items()})


if __name__ == "__main__":
    main()
