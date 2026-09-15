"""Render the exact prompt every benchmark arm sends, from the real sources.

Nothing here is paraphrased. Each arm's injected context is produced by the
code that injects it in real use:

    super       the repository's own per-prompt hook, scripts/hooks/skill_pipeline.py,
                in super mode against an empty goal store, so it is what a fresh
                Claude Code session receives on its first prompt
    ponytail    ponytail's own hooks/ponytail-instructions.js, level full
    caveman     caveman's own src/hooks/caveman-config.js ruleset loader, level full

Both third-party texts are rendered from the pinned commits in SOURCES by
running their JavaScript with node, so a later upstream change cannot silently
change what was measured. The "super without caveman" arm removes exactly the
three caveman lines from the super context and asserts that each edit landed.

    python benchmarks/2026-09-11/harness/build_arms.py

writes arms/<task>/<arm>.prompt.md, arms/sources/*.txt and arms/manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

BENCH = pathlib.Path(__file__).resolve().parents[1]
ROOT = BENCH.parents[1]
ARMS = BENCH / "arms"
HOOK = ROOT / "scripts" / "hooks" / "skill_pipeline.py"

SOURCES = {
    "ponytail": {
        "repo": "DietrichGebert/ponytail",
        "sha": "356918eba965ee1eac64bd3a7f0dd02108350de5",
        "licence": "MIT, Copyright (c) 2026 DietrichGebert",
        "files": ["hooks/ponytail-instructions.js", "hooks/ponytail-config.js",
                  "skills/ponytail/SKILL.md"],
        "render": ("process.stdout.write(require({module})"
                   ".getPonytailInstructions('full'))"),
        "module": "hooks/ponytail-instructions.js",
    },
    "caveman": {
        "repo": "JuliusBrussee/caveman",
        "sha": "15581d14007fd01fb3f132016741962f34936ca2",
        "licence": "MIT for skills/ and src/hooks/ (engine-linked directories are BSL-1.1 "
                   "and are not used here)",
        "files": ["src/hooks/caveman-config.js", "skills/caveman/SKILL.md"],
        "render": ("const c = require({module});"
                   "process.stdout.write(c.rulesetBanner('full') + '\\n\\n' + "
                   "c.loadFilteredRuleset('full', {hooksdir}))"),
        "module": "src/hooks/caveman-config.js",
    },
}

# The lines that make the super harness use caveman. Removed for the arm that
# keeps the super harness but swaps caveman for ponytail. Each must match once.
CAVEMAN_EDITS = [
    ("drop", "1. CAVEMAN."),
    ("replace", "RE-APPLY LAYER 1 to what you produced: caveman, full output, anti-slop, again.",
     "RE-APPLY LAYER 1 to what you produced: full output, anti-slop, again."),
    ("drop", "S1. CAVEMAN"),
]

ARM_ORDER = ["bare", "super", "super_ponytail_caveman", "super_ponytail_nocaveman",
             "ponytail", "caveman"]
ARM_LABELS = {
    "bare": "No harness",
    "super": "Super harness",
    "super_ponytail_caveman": "Super + ponytail + caveman",
    "super_ponytail_nocaveman": "Super + ponytail, no caveman",
    "ponytail": "Ponytail only",
    "caveman": "Caveman only",
}
# Arms that would not have the master skills installed in real use.
NO_SKILLS = {"bare", "ponytail", "caveman"}


def fetch_sources(cache: pathlib.Path) -> dict[str, pathlib.Path]:
    roots = {}
    for name, spec in SOURCES.items():
        root = cache / name
        for rel in spec["files"]:
            target = root / rel
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                url = f"https://raw.githubusercontent.com/{spec['repo']}/{spec['sha']}/{rel}"
                with urllib.request.urlopen(url, timeout=60) as response:
                    target.write_bytes(response.read())
        roots[name] = root
    return roots


def render_third_party(name: str, root: pathlib.Path, sandbox: pathlib.Path) -> str:
    """Run the project's own injection code. Config paths point into a sandbox
    so nothing these modules might write lands in the real home directory."""
    spec = SOURCES[name]
    module = root / spec["module"]
    script = spec["render"].format(module=json.dumps(module.as_posix()),
                                   hooksdir=json.dumps(module.parent.as_posix()))
    env = dict(os.environ, XDG_CONFIG_HOME=str(sandbox), APPDATA=str(sandbox),
               CLAUDE_CONFIG_DIR=str(sandbox), HOME=str(sandbox), USERPROFILE=str(sandbox))
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    out = subprocess.run(["node", "-e", script], env=env, capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    if not out.startswith(("PONYTAIL MODE ACTIVE", "CAVEMAN MODE ACTIVE")) or len(out) < 1500:
        raise SystemExit(f"{name}: unexpected render ({len(out)} chars): {out[:120]!r}")
    return out


def super_context(prompt: str, task: str) -> str:
    with tempfile.TemporaryDirectory(prefix="bench-goal-") as store:
        env = dict(os.environ, MASTER_REPO_GOAL_DIR=store, MASTER_HARNESS_MODE="super")
        payload = json.dumps({"prompt": prompt, "session_id": f"bench-{task}"})
        out = subprocess.run([sys.executable, str(HOOK)], input=payload, env=env,
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout
        context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        # A long goal is truncated to a pointer at the session file, which names
        # this temporary store by absolute path. That is the hook's real
        # behaviour; only the path is replaced, so the committed prompts carry
        # no local username and rebuild byte for byte.
        for variant in {store, os.path.normpath(store), pathlib.Path(store).as_posix()}:
            context = context.replace(variant, "<goal-store>")
    for required in ("Standing pipeline", "S10.", "STANDING GOAL"):
        if required not in context:
            raise SystemExit(f"super context for {task} is missing {required!r}")
    return context


def without_caveman(context: str) -> str:
    lines = context.split("\n")
    for edit in CAVEMAN_EDITS:
        if edit[0] == "drop":
            hits = [i for i, line in enumerate(lines) if line.startswith(edit[1])]
            if len(hits) != 1:
                raise SystemExit(f"expected one line starting {edit[1]!r}, found {len(hits)}")
            del lines[hits[0]]
        else:
            hits = [i for i, line in enumerate(lines) if edit[1] in line]
            if len(hits) != 1:
                raise SystemExit(f"expected one line containing {edit[1]!r}, found {len(hits)}")
            lines[hits[0]] = lines[hits[0]].replace(edit[1], edit[2])
    result = "\n".join(lines)
    if "caveman" in result.lower():
        raise SystemExit("the no-caveman super context still mentions caveman")
    return result


def wrap(context: str, task_prompt: str, delivery: str, no_skills: str | None) -> str:
    parts = []
    if context:
        # The shape Claude Code gives hook output: a system reminder on the turn.
        parts.append("<system-reminder>\nUserPromptSubmit hook additional context: "
                     + context + "\n</system-reminder>")
    parts.append(task_prompt)
    parts.append(delivery if not no_skills else delivery + " " + no_skills)
    return "\n\n".join(parts)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    config = json.loads((BENCH / "prompts" / "coding.json").read_text(encoding="utf-8"))
    (ARMS / "sources").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bench-vendor-") as tmp:
        cache = pathlib.Path(tmp)
        roots = fetch_sources(cache / "src")
        sandbox = cache / "sandbox"
        sandbox.mkdir()
        third = {name: render_third_party(name, root, sandbox) for name, root in roots.items()}
        stray = [p for p in sandbox.rglob("*") if p.is_file()]
        if stray:
            print(f"note: the render wrote {len(stray)} file(s) into the sandbox, not the home dir")
    for name, text in third.items():
        spec = SOURCES[name]
        header = (f"<!-- Rendered by {spec['repo']}@{spec['sha'][:12]}'s own hook code, level full. "
                  f"{spec['licence']}. -->\n")
        (ARMS / "sources" / f"{name}-full.txt").write_text(header + text, encoding="utf-8")

    manifest = {"sources": {n: {k: v for k, v in s.items() if k not in ("render", "module")}
                            for n, s in SOURCES.items()},
                "caveman_edits": [list(e) for e in CAVEMAN_EDITS],
                "arms": ARM_ORDER, "labels": ARM_LABELS, "no_skills": sorted(NO_SKILLS),
                "tasks": {}}
    for task, spec in config["tasks"].items():
        sup = super_context(spec["prompt"], task)
        contexts = {
            "bare": "",
            "super": sup,
            "super_ponytail_caveman": sup + "\n\n" + third["ponytail"] + "\n\n" + third["caveman"],
            "super_ponytail_nocaveman": without_caveman(sup) + "\n\n" + third["ponytail"],
            "ponytail": third["ponytail"],
            "caveman": third["caveman"],
        }
        (ARMS / task).mkdir(parents=True, exist_ok=True)
        manifest["tasks"][task] = {}
        for arm in ARM_ORDER:
            prompt = wrap(contexts[arm], spec["prompt"], config["delivery"],
                          config["no_skills"] if arm in NO_SKILLS else None)
            (ARMS / task / f"{arm}.prompt.md").write_text(prompt, encoding="utf-8")
            manifest["tasks"][task][arm] = {
                "contextBytes": len(contexts[arm].encode("utf-8")),
                "promptBytes": len(prompt.encode("utf-8")),
                "sha256": sha(prompt),
            }
    (ARMS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for task, arms in manifest["tasks"].items():
        print(task, {arm: data["contextBytes"] for arm, data in arms.items()})


if __name__ == "__main__":
    main()
