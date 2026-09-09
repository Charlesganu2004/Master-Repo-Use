#!/usr/bin/env python3
"""Generate atlas-data.json, the single data layer every atlas design reads.

Five designs share this file. Without it they drift, and a lane added to one
quietly goes missing from the other four.

Every lane is grounded in a file that exists. Nothing here is invented to pad a
count: a lane is a catalog list, a script, a workflow, a test module, a document,
or a named stage of the runtime path. If the file is deleted the lane disappears
on the next build, which is the behaviour you want from a map.

Components inside a lane are its real contents: the slugs in a list, the CLI
flags of a script, the classes in a test module, the headings of a document.

Privacy. Catalog entries ARE emitted here, flagged ``private: true``, because the
local designs are useless without them. They are stripped by build_public_site.py
before anything is published, and verify() fails the build if one survives. The
file written here is a private working artifact; the published one is not the
same file.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re

from sync_project_skills import sync_project_skills

ROOT = pathlib.Path(__file__).resolve().parents[1]
# Written to both places on purpose. The designs fetch it relative to themselves,
# and a hand-copied second file is exactly the kind of thing that drifts silently.
OUT = ROOT / "atlas-data.json"
OUT_DESIGNS = ROOT / "designs" / "atlas-data.json"
# Also emitted as plain JS. A <script src> tag works over file://, where fetch()
# is blocked by the browser, so the designs open by double-click with no server.
OUT_DESIGNS_JS = ROOT / "designs" / "atlas-data.js"
SLUG_RE = re.compile(r"[\w.-]+/[\w.-]+")

# Not lanes: one is the union of every other list, one is a publish control file.
NOT_A_LANE = {"all-curated", "public-allowlist"}

# Build combinations consume reviewed setup recipes, not the older ``cmd``
# field. ``cmd`` describes how to use/run a component after it exists and may
# legitimately be a test, workflow dispatch, slash command or template. Keeping
# setup separate prevents a bare GitHub clone from being presented as a complete
# computer setup.

# Local model runtimes, and one setup recipe per model the hardware document has
# already vetted.
#
# The tag list is READ from docs/hardware-profiles.json rather than written here.
# The first version of this file hardcoded six tags and one of them, gemma2:2b,
# was not in the vetted set at all - the atlas was offering to pull something no
# document had ever checked. Deriving the list makes that class of drift
# impossible rather than merely unlikely.
#
# Catalog entries are reference-only by design: a repository URL is not a vetted
# install. These are different. Each names a runtime and an exact tag that the
# hardware document records, with no placeholder to fill in.
HARDWARE_PROFILES = json.loads(
    (ROOT / "docs" / "hardware-profiles.json").read_text(encoding="utf-8"))

OLLAMA_RUNTIME = (
    "ollama-runtime", "Ollama runtime", "models",
    "The local runtime every model tag below needs. Installs once, then serves on "
    "127.0.0.1:11434.",
    {"windows": "winget install --id Ollama.Ollama --accept-source-agreements --accept-package-agreements",
     "wsl": "curl -fsSL https://ollama.com/install.sh | sh",
     "linux": "curl -fsSL https://ollama.com/install.sh | sh",
     "macos": "brew install ollama && brew services start ollama",
     "other": "curl -fsSL https://ollama.com/install.sh | sh"})

LIST_INSTALLED = (
    "model-list-installed", "List installed models", "models",
    "What this machine already holds, and how much disk each one is using.",
    {k: "ollama list" for k in ("windows", "wsl", "linux", "macos", "other")})


def _model_slug(tag: str) -> str:
    return "model-" + re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")


def _model_setups() -> list[tuple]:
    """One entry per vetted ollama model, ordered smallest machine first."""
    models = [m for m in HARDWARE_PROFILES["models"] if m.get("runtime") == "ollama"]
    models.sort(key=lambda m: (m["min_ram_gb"], m["params_b"], m["tag"]))
    setups = [OLLAMA_RUNTIME]
    for model in models:
        detail = (f"{model['vendor']}, {model['params_b']}B at {model['quant']}, "
                  f"needs {model['min_ram_gb']} GB. {model['use']} Licence: {model['license']}.")
        setups.append((_model_slug(model["tag"]), model["tag"], "models", detail,
                       {k: f"ollama pull {model['tag']}"
                        for k in ("windows", "wsl", "linux", "macos", "other")}))
    setups.append(LIST_INSTALLED)
    return setups


MODEL_SETUPS = _model_setups()


def model_setup_recipes() -> list[dict]:
    """One reviewed recipe per runtime or tag, so Build can emit real commands."""
    return [{
        "id": f"setup-{ident}",
        "name": name,
        "kind": "setup",
        "state": "ready",
        "trust": "named-vendor-runtime",
        "detail": detail,
        "commands": commands,
    } for ident, name, _family, detail, commands in MODEL_SETUPS]


def model_setup_lane() -> tuple[list, list]:
    lanes = [lane("sys-model-setup", "Local model setup", "models", "model",
                  "runtime", "Reviewed install commands for local model runtimes and tags.",
                  len(MODEL_SETUPS))]
    comps = []
    for index, (ident, name, family, detail, commands) in enumerate(MODEL_SETUPS):
        comps.append({
            "id": ident, "name": name, "lane": "sys-model-setup", "family": family,
            "kind": "model", "detail": detail, "order": index, "cmd": dict(commands),
            "setupRecipe": f"setup-{ident}", "setupState": "ready",
        })
    return lanes, comps



# The global rules half of setup: which client instruction files carry the Master
# Repo contract and the protected auto-mode block.
#
# Split per client because the answer to "set up my rules" depends on which
# assistant is being set up, and writing all four when only one is installed
# leaves three orphan files that later look authoritative.
REPO_URL = "https://github.com/Charlesganu2004/Master-Repo-Use.git"
_PS_CLONE = ("$p=Join-Path $HOME 'Master-Repo-Use'; "
             "if (Test-Path (Join-Path $p '.git')) { git -C $p pull --ff-only } "
             f"else {{ git clone {REPO_URL} $p }}; ")
_SH_CLONE = ('p="$HOME/Master-Repo-Use"; if [ -d "$p/.git" ]; then git -C "$p" pull --ff-only; '
             f'else git clone {REPO_URL} "$p"; fi && ')

# Every owner recipe starts by making sure the repository is present and current.
# Each recipe stays standalone - the Build tab may run any one of them alone - but
# the preamble is recorded separately so a profile can print it once.
_CLONE_PREAMBLE = {"windows": _PS_CLONE, "wsl": _SH_CLONE, "macos": _SH_CLONE,
                   "linux": _SH_CLONE, "other": _SH_CLONE}


def _rules_bodies(client: str) -> dict:
    """The step itself, without the clone. Same intent on every platform."""
    ps = ("& (Join-Path $p 'scripts/setup-global-ai.ps1') -RepoPath $p "
          f"-Client {client} -AutoSkills")
    sh = f'bash "$p/scripts/setup-global-ai.sh" "$p" --client {client} --auto-skills'
    return {"windows": ps, "wsl": sh, "macos": sh, "linux": sh,
            "other": sh}


def _with_clone(bodies: dict) -> dict:
    """A standalone command: clone-or-refresh, then the body."""
    return {key: _CLONE_PREAMBLE[key] + body for key, body in bodies.items()}


LOCAL_HARNESS_RECIPE = {
    "id": "setup-local-model-harness",
    "name": "Verify the local-model auto-mode harness",
    "kind": "setup",
    "state": "ready",
    "trust": "owner-repository",
    "detail": "Clones or refreshes Master-Repo-Use and checks that all three standing layers are prepended before a raw Ollama request.",
    "commands": _with_clone({
        "windows": "python (Join-Path $p 'scripts/auto_mode_harness.py') --check",
        "wsl": 'python3 "$p/scripts/auto_mode_harness.py" --check',
        "macos": 'python3 "$p/scripts/auto_mode_harness.py" --check',
        "linux": 'python3 "$p/scripts/auto_mode_harness.py" --check',
        "other": 'python3 "$p/scripts/auto_mode_harness.py" --check',
    }),
}


def _rules_commands(client: str) -> dict:
    return _with_clone(_rules_bodies(client))


_GUARD_BODIES = {
    "windows": "python (Join-Path $p 'scripts/install_auto_mode.py') --repo $p",
    "wsl": 'python3 "$p/scripts/install_auto_mode.py" --repo "$p"',
    "macos": 'python3 "$p/scripts/install_auto_mode.py" --repo "$p"',
    "linux": 'python3 "$p/scripts/install_auto_mode.py" --repo "$p"',
    "other": 'python3 "$p/scripts/install_auto_mode.py" --repo "$p"',
}

GLOBAL_RULES_SETUPS = [
    ("rules-all-clients", "Global rules - every client", "instructions",
     "Writes the Master Repo contract and the protected auto-mode block to Claude, "
     "Codex, Gemini, Antigravity, Cursor and Copilot at once. The default: one rule set, no client left "
     "holding a contradicting copy.",
     _rules_commands("all")),

    ("rules-claude", "Global rules - Claude", "instructions",
     "~/.claude/CLAUDE.md only. Use when Claude Code is the only assistant installed.",
     _rules_commands("claude")),

    ("rules-codex", "Global rules - Codex (GPT)", "instructions",
     "~/.codex/AGENTS.md only. Codex is the GPT surface; --client gpt is accepted as an alias.",
     _rules_commands("codex")),

    ("rules-gemini", "Global rules - Gemini", "instructions",
     "~/.gemini/GEMINI.md only. Google Antigravity reads the same file, so this also "
     "gives Antigravity its rules; it just does not install the skill folders.",
     _rules_commands("gemini")),

    ("rules-antigravity", "Global rules - Google Antigravity", "instructions",
     "~/.gemini/GEMINI.md for the rules, plus every skill in this repository copied "
     "into ~/.gemini/config/skills/, which is Antigravity's documented global skill "
     "path and one the Gemini CLI does not read. Verified against "
     "antigravity.google/docs on 2026-09-04: there is no ~/.antigravity/ tree, and "
     "plugins and MCP config live beside the skills under ~/.gemini/config/.",
     _rules_commands("antigravity")),

    ("rules-copilot", "Global rules - Copilot", "instructions",
     "~/.copilot/copilot-instructions.md, plus the COPILOT_CUSTOM_INSTRUCTIONS_DIRS "
     "environment variable that makes Copilot read the repository.",
     _rules_commands("copilot")),

    ("rules-cursor", "Global rules - Cursor", "instructions",
     "Installs an always-applied rule into ~/.cursor/rules/master-repo-auto.mdc, "
     "skills into ~/.cursor/skills, and session context plus shell guards into ~/.cursor/hooks.json.",
     _rules_commands("cursor")),

    ("rules-guards", "Standing pipeline and guards", "instructions",
     "The one command that makes the rules hold outside the model. Installs every "
     "skill into Claude Code, Codex, Antigravity, Cursor and Copilot, the two PreToolUse guards, and the "
     "standing pipeline hook, which injects three layers into every prompt and every "
     "command with no slash needed. Layer 1 before the request is read: caveman, full "
     "output, anti-slop. Layer 2 before anything is produced: plan, design. Layer 3 "
     "while acting: pick and name the skills, tools, plugins and MCP servers that fit, "
     "fan independent work out to agents, then re-apply layer 1 to what came back. "
     "Claude Code and Codex use UserPromptSubmit, Antigravity uses PreInvocation, "
     "Copilot uses userPromptTransformed, and Cursor combines an always rule with sessionStart. "
     "Codex hooks require one-time client trust. Guards protect matching shell commands; "
     "they cannot prevent owner or administrator changes or host-managed context compaction.",
     _with_clone(_GUARD_BODIES)),

    ("rules-pipeline-check", "Show the pipeline that fires", "instructions",
     "Prints the exact text injected into every prompt, and which hook events are "
     "registered for it. A pipeline nobody can read is one nobody can trust: this is "
     "how you confirm it is actually running rather than assume it.",
     {"windows": "echo '{\"input\":{\"prompt\":\"check\"}}' | python (Join-Path $HOME 'Master-Repo-Use/scripts/hooks/skill_pipeline.py'); Get-Content $HOME\\.claude\\settings.json | Select-String skill_pipeline; Get-Content $HOME\\.gemini\\config\\hooks.json",
      "wsl": "echo '{\"input\":{\"prompt\":\"check\"}}' | python3 \"$HOME/Master-Repo-Use/scripts/hooks/skill_pipeline.py\"; grep -o 'skill_pipeline[^\"]*' ~/.claude/settings.json; cat ~/.gemini/config/hooks.json 2>/dev/null",
      "macos": "echo '{\"input\":{\"prompt\":\"check\"}}' | python3 \"$HOME/Master-Repo-Use/scripts/hooks/skill_pipeline.py\"; grep -o 'skill_pipeline[^\"]*' ~/.claude/settings.json; cat ~/.gemini/config/hooks.json 2>/dev/null",
      "linux": "echo '{\"input\":{\"prompt\":\"check\"}}' | python3 \"$HOME/Master-Repo-Use/scripts/hooks/skill_pipeline.py\"; grep -o 'skill_pipeline[^\"]*' ~/.claude/settings.json; cat ~/.gemini/config/hooks.json 2>/dev/null",
      "other": "echo '{\"input\":{\"prompt\":\"check\"}}' | python3 \"$HOME/Master-Repo-Use/scripts/hooks/skill_pipeline.py\"; grep -o 'skill_pipeline[^\"]*' ~/.claude/settings.json; cat ~/.gemini/config/hooks.json 2>/dev/null"}),

    # Verifies BOTH halves. The rules half is a block in a file; the skills half is
    # a directory of folders, and a setup that wrote the block and silently failed
    # to copy the skills would look identical without the second command.
    ("rules-verify", "Verify what was written", "instructions",
     "Lists the client files carrying the block, then the skill folders each client "
     "can actually see. A setup that wrote the rules and quietly failed to copy the "
     "skills looks complete until you check the second one.",
     {"windows": "Get-ChildItem $HOME\.claude\CLAUDE.md,$HOME\.codex\AGENTS.md,$HOME\.gemini\GEMINI.md,$HOME\.copilot\copilot-instructions.md -ErrorAction SilentlyContinue | Select-String -Pattern 'MASTER-REPO-USE:BEGIN'; Get-ChildItem $HOME\.claude\skills,$HOME\.codex\skills,$HOME\.gemini\config\skills -Directory -ErrorAction SilentlyContinue | Select-Object FullName",
      "wsl": "grep -l 'MASTER-REPO-USE:BEGIN' ~/.claude/CLAUDE.md ~/.codex/AGENTS.md ~/.gemini/GEMINI.md ~/.copilot/copilot-instructions.md 2>/dev/null; ls -d ~/.claude/skills/*/ ~/.codex/skills/*/ ~/.gemini/config/skills/*/ 2>/dev/null",
      "macos": "grep -l 'MASTER-REPO-USE:BEGIN' ~/.claude/CLAUDE.md ~/.codex/AGENTS.md ~/.gemini/GEMINI.md ~/.copilot/copilot-instructions.md 2>/dev/null; ls -d ~/.claude/skills/*/ ~/.codex/skills/*/ ~/.gemini/config/skills/*/ 2>/dev/null",
      "linux": "grep -l 'MASTER-REPO-USE:BEGIN' ~/.claude/CLAUDE.md ~/.codex/AGENTS.md ~/.gemini/GEMINI.md ~/.copilot/copilot-instructions.md 2>/dev/null; ls -d ~/.claude/skills/*/ ~/.codex/skills/*/ ~/.gemini/config/skills/*/ 2>/dev/null",
      "other": "grep -l 'MASTER-REPO-USE:BEGIN' ~/.claude/CLAUDE.md ~/.codex/AGENTS.md ~/.gemini/GEMINI.md ~/.copilot/copilot-instructions.md 2>/dev/null; ls -d ~/.claude/skills/*/ ~/.codex/skills/*/ ~/.gemini/config/skills/*/ 2>/dev/null"}),
]


def global_rules_recipes() -> list[dict]:
    recipes = []
    for ident, name, _family, detail, commands in GLOBAL_RULES_SETUPS:
        recipe = {
            "id": f"setup-{ident}",
            "name": name,
            "kind": "setup",
            "state": "ready",
            "trust": "owner-repository",
            "detail": detail,
            "commands": commands,
        }
        # Recorded only where it is genuinely the shared preamble, so a profile
        # can drop the repeat without any string matching at read time.
        if all(command.startswith(_CLONE_PREAMBLE[key])
               for key, command in commands.items()):
            recipe["preambles"] = dict(_CLONE_PREAMBLE)
            recipe["bodies"] = {key: command[len(_CLONE_PREAMBLE[key]):]
                                for key, command in commands.items()}
        recipes.append(recipe)
    return recipes


def global_rules_lane() -> tuple[list, list]:
    lanes = [lane("sys-global-rules", "Global rules setup", "instructions", "instruction",
                  "runtime", "Per-client commands that install the Master Repo contract "
                  "and the protected auto-mode block.", len(GLOBAL_RULES_SETUPS))]
    comps = [{
        "id": ident, "name": name, "lane": "sys-global-rules", "family": family,
        "kind": "instruction", "detail": detail, "order": index, "cmd": dict(commands),
        "setupRecipe": f"setup-{ident}", "setupState": "ready",
    } for index, (ident, name, family, detail, commands) in enumerate(GLOBAL_RULES_SETUPS)]
    return lanes, comps



# Easy Setup. Four answers to "I have a new machine, what do I run?"
#
# A profile is an ordered list of reviewed recipes, nothing more. It cannot
# install anything the Build tab could not already install one node at a time;
# it removes the need to know which nodes to pick and in what order.
#
# Two steps are written as tokens the client resolves rather than fixed ids:
#   rules:{client}  the client picker's answer (all, claude, codex, gemini, copilot)
#   model:{tier}    the largest tag the entered RAM can actually host
# Both fail visibly. An unresolved token is dropped from the script and named in
# the notes, instead of emitting a command with a placeholder still in it.
#
# No profile lists master-repo-global. It runs setup-global-ai with no client
# argument, which means all four, so following the client picker with it would
# silently undo the pick. The rules step already clones the repository and runs
# the same script with the chosen client, and everything else that script does is
# client-independent. master-repo-global stays available in Build for anyone who
# does want all four in one step.
PROFILES = [
    {
        "id": "rules-only",
        "name": "Global rules only",
        "summary": "The contract and the guards. No models, no clone beyond this repo.",
        "detail": "Writes the Master Repo contract and the protected auto-mode block into "
                  "the client you pick, then installs the no-prune and no-compress hooks so "
                  "the rules hold outside the model as well as inside it.",
        "bestFor": "An existing machine that already has its tooling and only needs the rules.",
        "steps": ["rules:{client}", "setup-rules-guards", "setup-rules-pipeline-check", "setup-rules-verify"],
    },
    {
        "id": "software-developer",
        "name": "Software developer",
        "summary": "Rules, the repository itself, and one local model that fits.",
        "detail": "Everything in Global rules, plus the Ollama runtime and the largest "
                  "model tag the entered RAM can host. The rules step already clones the "
                  "repository, so this does not clone it again. Enough to work offline.",
        "bestFor": "A new laptop that will write code and wants a local model for the cheap work.",
        "steps": ["rules:{client}", "setup-rules-guards",
                  "setup-ollama-runtime", "model:{tier}", "setup-rules-pipeline-check", "setup-rules-verify"],
    },
    {
        "id": "engineering",
        "name": "Engineering",
        "summary": "The developer profile plus a second model and the installed-model check.",
        "detail": "Adds a second local tag so routing has somewhere to go, and lists what is "
                  "installed at the end so the machine can be checked rather than assumed. "
                  "Aimed at a workstation that will run local inference regularly.",
        "bestFor": "A workstation with the memory to hold more than one model at a time.",
        "steps": ["rules:{client}", "setup-rules-guards",
                  "setup-ollama-runtime", "model:{tier}", "model:{tier2}",
                  "setup-model-list-installed", "setup-rules-pipeline-check", "setup-rules-verify"],
    },
    {
        "id": "everything",
        "name": "Everything ready",
        "summary": "Every reviewed recipe, in dependency order.",
        "detail": "Runs every setup-ready recipe this repository holds. Nothing here is "
                  "catalog code: catalog entries stay reference-only, so this installs the "
                  "runtime, the rules and the reviewed model tags, and nothing else.",
        "bestFor": "A machine being set up once, thoroughly, where disk is not the constraint.",
        "steps": ["rules:{client}", "setup-rules-guards",
                  "setup-ollama-runtime", "ALL_MODEL_TAGS",
                  "setup-model-list-installed", "setup-rules-pipeline-check", "setup-rules-verify"],
    },
]

# The client picker's options, in the order they are offered.
PROFILE_CLIENTS = [
    {"id": "all", "name": "All clients",
     "detail": "Claude, Codex, Gemini, Copilot, Antigravity and Cursor together."},
    {"id": "claude", "name": "Claude", "detail": "~/.claude/CLAUDE.md"},
    {"id": "codex", "name": "Codex (GPT)", "detail": "~/.codex/AGENTS.md"},
    {"id": "gemini", "name": "Gemini", "detail": "~/.gemini/GEMINI.md"},
    {"id": "copilot", "name": "Copilot", "detail": "~/.copilot/copilot-instructions.md"},
    {"id": "cursor", "name": "Cursor", "detail": "~/.cursor/rules/master-repo-auto.mdc + ~/.cursor/hooks.json"},
    # Same rules file as Gemini, plus the skills tree. Listed separately because
    # picking it does more than picking Gemini does, not less.
    {"id": "antigravity", "name": "Google Antigravity",
     "detail": "~/.gemini/GEMINI.md, plus skills into ~/.gemini/config/skills/"},
]

# Built from the same clone helpers the rules recipes use, so the preamble is
# byte-identical everywhere. Easy Setup relies on that: it prints the clone once
# and the bodies after it, instead of cloning the same repository three times.

# Google Antigravity. A hosted surface rather than a local runtime, so what is
# installable here is its CLI. Commands are the vendor's own, read from
# antigravity.google/download on 2026-09-04; the model list on the surface node
# comes from antigravity.google/docs/models the same day.
#
# These pipe a remote script into a shell, which is what Google documents. It is
# the same shape as the Ollama recipe and carries the same trust basis: a named
# vendor over TLS, and nothing pinned, because the vendor publishes no checksum.
ANTIGRAVITY_SETUPS = [
    ("antigravity-cli", "Antigravity CLI", "surfaces",
     "Google's agentic development CLI. Free for individual developers. Signs in with "
     "a Google account; no key to paste.",
     {"windows": "irm https://antigravity.google/cli/install.ps1 | iex",
      "wsl": "curl -fsSL https://antigravity.google/cli/install.sh | bash",
      "linux": "curl -fsSL https://antigravity.google/cli/install.sh | bash",
      "macos": "curl -fsSL https://antigravity.google/cli/install.sh | bash",
      "other": "curl -fsSL https://antigravity.google/cli/install.sh | bash"}),
]


def antigravity_recipes() -> list[dict]:
    return [{
        "id": f"setup-{ident}",
        "name": name,
        "kind": "setup",
        "state": "ready",
        "trust": "named-vendor-runtime",
        "detail": detail,
        "commands": commands,
    } for ident, name, _family, detail, commands in ANTIGRAVITY_SETUPS]


# The models Antigravity hosts, read from antigravity.google/docs/models on
# 2026-09-04. These are REFERENCE nodes, not setup recipes, and deliberately so:
# a hosted model has nothing to install. You sign in and pick it. Giving them a
# setup command would be inventing one.
#
# The plan column is the part worth having in the atlas. Charles runs a paid tier
# alongside local models, and the three non-Google models are the ones a plan
# change actually takes away.
#
# Version strings are the weakest fact here. They came from a rendered docs page
# rather than a raw read, so treat the minor digits as needing a re-check before
# anyone depends on an exact string.
ANTIGRAVITY_MODELS = [
    ("gemini-3-8-flash", "Gemini 3.8 Flash",
     "Google. Available on every plan including the free tier. The default for bulk work."),
    ("gemini-3-7-flash", "Gemini 3.7 Flash",
     "Google. Available on every plan. Previous Flash generation, kept selectable."),
    ("gemini-3-6-flash", "Gemini 3.6 Flash",
     "Google. Available on every plan. Two generations back."),
    ("gemini-3-1-pro", "Gemini 3.1 Pro",
     "Google. Available on every plan. The reasoning tier; draws on the same rate limit as "
     "Flash rather than a separate one."),
    ("claude-sonnet-4-6-thinking", "Claude Sonnet 4.6 (thinking)",
     "Anthropic, hosted inside Antigravity. Marked unavailable on the Enterprise plan."),
    ("claude-opus-4-6-thinking", "Claude Opus 4.6 (thinking)",
     "Anthropic, hosted inside Antigravity. Marked unavailable on the Enterprise plan."),
    ("gpt-oss-120b", "GPT-OSS-120b",
     "Open-weight, hosted inside Antigravity. Marked unavailable on the Enterprise plan."),
    ("nano-banana-2", "Nano Banana 2",
     "Google. Image work rather than reasoning. Available on every plan."),
]


def antigravity_model_lane() -> tuple[list, list]:
    """Hosted Antigravity models as reference nodes.

    Separate from sys-model-setup, which is local Ollama tags with a real
    ``ollama pull`` behind each one. Mixing the two would put a node offering an
    install command next to one that cannot have one, in the same lane, which is
    exactly the confusion the setup/reference split exists to prevent.
    """
    lanes = [lane("sys-antigravity-models", "Antigravity hosted models", "models", "model",
                  "runtime",
                  "Models Google Antigravity serves. Reference only: a hosted model is "
                  "selected in the client, not installed, so none of these carries a "
                  "setup command. Rate limits are a five-hour bucket inside a weekly "
                  "cap, published as percentages remaining rather than token counts.",
                  len(ANTIGRAVITY_MODELS))]
    comps = [{
        "id": f"ag-{ident}", "name": name, "lane": "sys-antigravity-models",
        "family": "models", "kind": "model", "detail": detail, "order": index,
        # Not "unavailable". Unavailable means a recipe is missing and should be
        # written. Hosted means no recipe can exist, and the two should not read
        # the same in the interface.
        "hosted": True,
    } for index, (ident, name, detail) in enumerate(ANTIGRAVITY_MODELS)]
    return lanes, comps


MASTER_SETUP_RECIPE = {
    "id": "master-repo-global",
    "name": "Master Repo global AI setup",
    "kind": "setup",
    "state": "ready",
    "trust": "owner-repository",
    "detail": "Clones or refreshes Master-Repo-Use and installs its global client pointers.",
    "preambles": dict(_CLONE_PREAMBLE),
    "bodies": {
        "windows": "& (Join-Path $p 'scripts/setup-global-ai.ps1') -RepoPath $p",
        "wsl": 'bash "$p/scripts/setup-global-ai.sh" "$p"',
        "macos": 'bash "$p/scripts/setup-global-ai.sh" "$p"',
        "linux": 'bash "$p/scripts/setup-global-ai.sh" "$p"',
        "other": 'sh "$p/scripts/setup-global-ai.sh" "$p"',
    },
}
MASTER_SETUP_RECIPE["commands"] = {
    key: _CLONE_PREAMBLE[key] + MASTER_SETUP_RECIPE["bodies"][key]
    for key in MASTER_SETUP_RECIPE["bodies"]
}

# These runtime nodes are implemented by the owner repository itself. Other
# runtime nodes name third-party CLIs or services and remain setup-unavailable
# until they receive a separately reviewed, pinned recipe.
MASTER_SETUP_STAGE_IDS = {
    "task-intake", "scope-resolver", "lane-match", "budget-check", "hardware-gate",
    "owner-approval-stage", "workspace-trust", "secret-scope", "master-repo-auto",
    "plugin-registry", "no-prune-hook", "branch-pr",
}

# Runtime stages that carry their own vendor recipe rather than the owner one.
STAGE_OWN_RECIPES = {"antigravity": "setup-antigravity-cli"}

FAMILIES = [
    ("intake", "Intake and routing", "instruction"),
    ("surfaces", "Client surfaces", "capability"),
    ("identity", "Identity and policy", "control"),
    ("instructions", "Instruction layer", "instruction"),
    ("skills", "Skills", "capability"),
    ("tools", "Tools", "capability"),
    ("mcp", "MCP and connectors", "capability"),
    ("agents", "Agents", "capability"),
    ("plugins", "Plugins", "capability"),
    ("knowledge", "Knowledge and retrieval", "knowledge"),
    ("models", "Models and serving", "model"),
    ("hybrid", "Hybrid routing", "model"),
    ("validation", "Validation and safety", "control"),
    ("observability", "Observability", "control"),
    ("automation", "Automation", "delivery"),
    ("delivery", "Delivery", "delivery"),
    ("domain", "Domain lanes", "knowledge"),
]

# Runtime stages: the path a task actually takes. Each carries the command a
# person would run, per platform where they differ.
STAGES = [
    ("intake", "task-intake", "Task intake", "Normalizes the request and starts the system trace.", None),
    ("intake", "scope-resolver", "Scope resolver", "Picks the smallest safe set of resources for the task.", None),
    ("intake", "lane-match", "Lane matcher", "Maps the task to a catalog lane before inventing a dependency.", "grep -ril '<topic>' repo-lists/"),
    ("intake", "budget-check", "Budget check", "Decides whether the work fits the session token target.", "cat docs/TOKEN-BUDGET.md"),
    ("intake", "hardware-gate", "Hardware gate", "Reads real RAM, GPU and disk before recommending a local model.", "python scripts/local_model_advisor.py"),
    ("surfaces", "claude-code", "Claude Code", "Terminal, desktop, web and IDE agent surface.", "claude"),
    ("surfaces", "codex", "Codex", "Repository aware coding and system work surface.", "codex"),
    ("surfaces", "copilot", "GitHub Copilot", "Native GitHub assistant surface.", "gh copilot explain"),
    ("surfaces", "gemini", "Gemini", "Multimodal and hosted model surface.", "gemini"),
    ("surfaces", "opencode", "OpenCode", "Multi-provider client surface.", None),
    ("surfaces", "antigravity", "Google Antigravity",
     "Google's agentic development platform: IDE, CLI and SDK. Free for individual "
     "developers. Hosts Gemini 3.8/3.7/3.6 Flash, Gemini 3.1 Pro, Claude Sonnet 4.6 and "
     "Opus 4.6 (thinking), GPT-OSS-120b, and Nano Banana 2 for image work. Rate limits "
     "are per plan, tracked as a weekly and a five-hour remaining count.",
     "antigravity"),
    ("identity", "owner-approval-stage", "Owner approval", "Only Charles approves, by passcode or by pinned revision.", "gh pr comment <n> --body 'I approve <passcode>'"),
    ("identity", "workspace-trust", "Workspace trust", "Binds access to the active repository and workspace.", None),
    ("identity", "secret-scope", "Secret scope", "Keeps credentials out of committed files and prompts.", None),
    ("skills", "caveman-compact", "caveman-ultra-compact", "Maximum compression pass over one natural-language file.", "/caveman-ultra-compact <file>"),
    ("skills", "caveman-repo", "caveman-ultra-compact-repo", "The same rules across a whole repository.", "/caveman-ultra-compact-repo"),
    ("skills", "master-repo-auto", "master-repo-auto", "Auto mode rules, loaded on demand rather than every session.", None),
    ("tools", "rtk", "rtk", "CLI proxy, 60-90 percent off common dev command output.", "rtk <command>"),
    ("tools", "rtt", "reducethemtokens", "Compresses a repo to a signature skeleton for orientation.", "rtt ."),
    ("mcp", "github-mcp", "github-mcp-server", "Official GitHub MCP server.", None),
    ("mcp", "merge-guard", "mcp-merge-guard", "Merge gating over MCP. Link only, no licence.", None),
    ("plugins", "plugin-registry", "Plugin registry", "Marketplaces and installed plugin state.", "claude plugin list"),
    ("validation", "no-prune-hook", "No-prune hook", "Blocks deletion of skills, tools, MCP and catalog paths.", None),
    ("observability", "token-gain", "Token savings", "What the reducers actually saved.", "rtk gain"),
    ("delivery", "branch-pr", "Branch and PR", "Every change lands on a branch, never straight to main.", "git switch -c feature/<name>"),
]

ROUTES = [
    ("local-first", "Local first, hosted on miss", "Small local model answers; escalate only when it cannot.",
     ["hardware-gate", "claude-code"], "cheapest", "8 GB RAM minimum"),
    ("draft-review", "Local draft, hosted review", "Local model drafts, hosted model reviews and corrects.",
     ["hardware-gate", "claude-code", "codex"], "balanced", "16 GB RAM"),
    ("parallel-vote", "Parallel then vote", "Several models answer independently; disagreement triggers a third.",
     ["claude-code", "codex", "gemini"], "highest confidence", "hosted only"),
    ("skeleton-retrieve", "Skeleton then retrieve", "rtt maps the repo, the model retrieves only what it names.",
     ["rtt", "lane-match", "claude-code"], "large repositories", "any"),
    ("compress-forward", "Compress then forward", "Compress context locally before spending hosted tokens.",
     ["caveman-compact", "rtk", "claude-code"], "long documents", "any"),
    ("guarded-write", "Guarded write", "Any deletion passes the hook before the model acts.",
     ["no-prune-hook", "branch-pr"], "safety critical", "any"),
    ("audit-approve", "Audit then approve", "Deterministic audit proposes; the owner approves by passcode.",
     ["owner-approval-stage", "branch-pr"], "maintenance", "any"),
    ("vision-route", "Multimodal split", "Vision to a multimodal model, reasoning to a text model.",
     ["gemini", "claude-code"], "image and document work", "hosted only"),
    ("budget-cap", "Budget capped", "Stop and report rather than silently overspending a token target.",
     ["budget-check", "token-gain"], "fixed budgets", "any"),
    ("offline", "Fully offline", "No hosted call at any stage. Quality is bounded by the machine.",
     ["hardware-gate", "rtt", "caveman-compact"], "air-gapped work", "16 GB RAM minimum"),
]

def tier_tags(gb: int, count: int = 2) -> list[str]:
    """The largest vetted tags this tier can host, from two different vendors.

    Read from docs/hardware-profiles.json rather than written out, so a tier can
    never come to name a tag the hardware document has not checked. Two vendors
    rather than the top two by size, because a tier offering two builds of the
    same family is a worse answer than one offering a choice.
    """
    fits = [(index, model) for index, model in enumerate(HARDWARE_PROFILES["models"])
            if model.get("runtime") == "ollama" and model["min_ram_gb"] <= gb]
    # Size decides; ties fall back to the order the hardware document lists them
    # in, which is the author's own ordering rather than an alphabetical accident.
    fits.sort(key=lambda pair: (-pair[1]["params_b"], pair[0]))
    chosen, vendors = [], set()
    for _index, model in fits:
        if model["vendor"] in vendors:
            continue
        vendors.add(model["vendor"])
        chosen.append(model["tag"])
        if len(chosen) == count:
            break
    return chosen


HARDWARE = [
    ("4gb", "4 GB RAM", "Hosted API only", 4,
     "Local inference will swap and thrash. That is the honest answer, not a limit to engineer around.", []),
    ("8gb", "8 GB RAM", "Smallest useful local tier", 8,
     "3B class models at 4-bit quantization, with headroom left for the OS.", tier_tags(8)),
    ("16gb", "16 GB RAM", "Comfortable local tier", 16,
     "7B to 8B class at 4-bit. The common developer laptop.", tier_tags(16)),
    ("32gb", "32 GB RAM", "Large local tier", 32,
     "13B to 14B class, or 7B at higher precision.", tier_tags(32)),
    ("apple", "Apple silicon", "Unified memory is shared", 0,
     "GPU and CPU draw on one pool, so usable model size sits below the headline number. Metal acceleration is automatic in Ollama.", []),
    ("gpu", "Discrete GPU", "VRAM is the real limit", 0,
     "System RAM does not substitute. A 12 GB card runs roughly what a 16 GB unified machine runs.", []),
]

FAMILY_HINTS = [
    (("mcp",), "mcp"), (("skill",), "skills"), (("agent", "adk"), "agents"),
    (("copilot", "client"), "surfaces"), (("local-models", "llm", "model"), "models"),
    (("rag", "knowledge", "live-rag", "multi-model"), "knowledge"),
    (("security", "observability"), "validation"),
    (("cost", "context", "token"), "hybrid"),
    (("design", "ui", "app-", "hackathon"), "delivery"),
]
KIND_HINTS = [
    (("security", "observability", "merge", "guardian", "approval", "freshness", "audit"), "control"),
    (("model", "llm", "hardware"), "model"),
    (("rag", "knowledge", "article", "spatial", "doc"), "knowledge"),
    (("design", "app-", "hackathon", "site", "pages"), "delivery"),
]


def pick(stem: str, hints, default: str) -> str:
    for needles, value in hints:
        if any(n in stem for n in needles):
            return value
    return default


def first_comment(path: pathlib.Path, markers: tuple[str, ...]) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            text = line.strip()
            for marker in markers:
                if text.startswith(marker) and len(text) > len(marker) + 3:
                    return text.lstrip(marker + " ").strip().rstrip(".") + "."
    except OSError:
        pass
    return ""


def lane(lid, name, family, kind, source, description, count, catalog=False) -> dict:
    return {"id": lid, "name": name, "family": family, "kind": kind, "source": source,
            "description": description or f"{name}.", "count": count, "catalog": catalog}


def catalog_lanes() -> tuple[list, list]:
    """Catalog lanes and the entries inside them.

    The entries carry real repository slugs, which are private: the catalog
    composition is not published. Each is flagged private=True and the public
    build strips them, so the local designs are useful and the published ones
    stay clean. build_public_site.verify() fails loudly if one slips through.

    Sub-categories come from the '# --- ' section headers the lists already use,
    so they are the author's own groupings rather than something inferred.
    """
    lanes, comps = [], []
    for path in sorted((ROOT / "repo-lists").glob("*.txt")):
        if path.stem in NOT_A_LANE:
            continue
        lid = f"cat-{path.stem}"
        family = pick(path.stem, FAMILY_HINTS, "domain")
        kind = pick(path.stem, KIND_HINTS, "capability")
        entries, section, sections = [], "", []
        # Clicking a sub-category should say what it is. The text comes from what
        # the author already wrote and is otherwise thrown away: the parenthetical
        # or colon clause in the header, plus any comment lines between the header
        # and its first entry. Nothing is synthesised - a sub-category with no
        # prose behind it gets no description rather than an invented one.
        blurbs: dict[str, list[str]] = {}
        awaiting_blurb = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if text.startswith("# ---"):
                full = text.lstrip("# -").strip().rstrip(".")
                # keep sub-category labels short enough to be a filter chip
                section = full.split(" (")[0].split(":")[0].strip()[:38]
                tail = full[len(full.split(" (")[0].split(":")[0]):].strip(" (:)").strip()
                if section and section not in sections:
                    sections.append(section)
                    blurbs[section] = [tail] if tail else []
                awaiting_blurb = section
                continue
            if not text:
                awaiting_blurb = ""
                continue
            if text.startswith("#"):
                # A comment directly under a header describes that header. One
                # further down is describing the entry above it instead.
                if awaiting_blurb:
                    blurbs.setdefault(awaiting_blurb, []).append(text.lstrip("# ").strip())
                continue
            candidate = text.split("#")[0].strip()
            if not SLUG_RE.fullmatch(candidate):
                continue
            note = text.split("#", 1)[1].strip() if "#" in text else ""
            # A list can name the same repository twice. Keep the first, since
            # ids are lane-scoped and a repeat would collide with itself.
            if any(existing == candidate for existing, _, _ in entries):
                continue
            entries.append((candidate, section, note))
            awaiting_blurb = ""

        entry = lane(lid, path.stem.replace("-", " ").title(), family, kind,
                     f"repo-lists/{path.name}", first_comment(path, ("#",)),
                     len(entries), catalog=True)
        entry["subcategories"] = sections
        counts: dict[str, int] = {}
        for _slug, sub, _note in entries:
            counts[sub or "Catalog"] = counts.get(sub or "Catalog", 0) + 1
        entry["subcategoryInfo"] = [{
            "name": name,
            "description": " ".join(" ".join(blurbs.get(name, [])).split()),
            "count": counts.get(name, 0),
        } for name in sections]
        lanes.append(entry)

        for index, (slug, sub, note) in enumerate(entries):
            owner, _, name = slug.partition("/")
            comps.append({
                # Lane-scoped: 94 repositories are cross-listed, and a bare
                # slug id collided for every one of them.
                "id": f"cat:{path.stem}:{slug}",
                "slug": slug,
                "name": name,
                "owner": owner,
                "lane": lid,
                "family": family,
                "kind": kind,
                "sub": sub or "Catalog",
                "detail": note or f"Catalogued in {path.name}.",
                "order": index,
                "private": True,          # stripped from the published artifact
                "sourceUrl": f"https://github.com/{slug}",
                "clone": {
                    "windows": f"git clone https://github.com/{slug}.git",
                    "wsl": f"git clone https://github.com/{slug}.git",
                    "macos": f"git clone https://github.com/{slug}.git",
                    "linux": f"git clone https://github.com/{slug}.git",
                },
                "setupState": "review-required",
            })
    return lanes, comps


def script_lanes() -> tuple[list, list]:
    """Each script is a capability. Its components are its CLI flags."""
    lanes, comps = [], []
    for path in sorted((ROOT / "scripts").glob("*.py")):
        if path.stem.startswith("_"):
            continue
        lid = f"tool-{path.stem}"
        flags = sorted(set(re.findall(r'add_argument\(\s*"(--[\w-]+)"', path.read_text(encoding="utf-8"))))
        fam = pick(path.stem, FAMILY_HINTS, "tools")
        kind = pick(path.stem, KIND_HINTS, "capability")
        lanes.append(lane(lid, path.stem.replace("_", " "), fam, kind,
                          f"scripts/{path.name}", first_comment(path, ('"""',)), len(flags) or 1))
        cmd = f"python scripts/{path.name}"
        comps.append({"id": f"{lid}-run", "name": f"run {path.stem}", "lane": lid, "family": fam,
                      "kind": kind, "detail": first_comment(path, ('"""',)) or f"Runs {path.name}.",
                      "cmd": {"windows": cmd, "wsl": f"python3 scripts/{path.name}",
                              "macos": f"python3 scripts/{path.name}", "linux": f"python3 scripts/{path.name}"}})
        for index, flag in enumerate(flags[:6]):
            comps.append({"id": f"{lid}{flag}", "name": flag, "lane": lid, "family": fam, "kind": kind,
                          "detail": f"Option of {path.name}.", "order": index + 1,
                          "cmd": {k: f"{cmd} {flag}" for k in ("windows", "wsl", "macos", "linux")}})
    return lanes, comps


def workflow_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        lid = f"flow-{path.stem}"
        text = path.read_text(encoding="utf-8")
        jobs = re.findall(r"^  ([a-z][\w-]*):\s*$", text, re.M)
        name = re.search(r"^name:\s*(.+)$", text, re.M)
        lanes.append(lane(lid, (name.group(1).strip() if name else path.stem), "automation", "control",
                          f".github/workflows/{path.name}",
                          f"GitHub Actions workflow with {len(jobs)} job(s).", len(jobs) or 1))
        for index, job in enumerate(jobs[:8]):
            comps.append({"id": f"{lid}-{job}", "name": job, "lane": lid, "family": "automation",
                          "kind": "control", "detail": f"Job in {path.name}.", "order": index,
                          "cmd": {k: f"gh workflow run {path.name}" for k in ("windows", "wsl", "macos", "linux")}})
    return lanes, comps


def test_lanes() -> tuple[list, list]:
    """Each test module is a guarantee. Its components are its test classes."""
    lanes, comps = [], []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        lid = f"test-{path.stem}"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        doc = (ast.get_docstring(tree) or "").split("\n")[0]
        lanes.append(lane(lid, path.stem.replace("test_", "").replace("_", " "),
                          "validation", "control", f"tests/{path.name}", doc, len(classes) or 1))
        for index, cls in enumerate(classes):
            comps.append({"id": f"{lid}-{cls}", "name": cls, "lane": lid, "family": "validation",
                          "kind": "control", "detail": f"Guarantee pinned by {path.name}.", "order": index,
                          "cmd": {k: f"python -m unittest tests.{path.stem}" for k in ("windows", "wsl", "macos", "linux")}})
    return lanes, comps


def doc_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / "docs").glob("*.md")):
        lid = f"doc-{path.stem.lower()}"
        text = path.read_text(encoding="utf-8", errors="replace")
        heads = re.findall(r"^##\s+(.+)$", text, re.M)
        title = re.search(r"^#\s+(.+)$", text, re.M)
        lanes.append(lane(lid, (title.group(1).strip() if title else path.stem), "knowledge", "knowledge",
                          f"docs/{path.name}", f"Reference document with {len(heads)} section(s).",
                          len(heads) or 1))
        for index, head in enumerate(heads[:6]):
            comps.append({"id": f"{lid}-{index}", "name": head[:48], "lane": lid, "family": "knowledge",
                          "kind": "knowledge", "detail": f"Section of {path.name}.", "order": index})
    return lanes, comps


def stage_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    grouped: dict[str, list] = {}
    for family, cid, name, detail, cmd in STAGES:
        grouped.setdefault(family, []).append((cid, name, detail, cmd))
    fam_names = {f: n for f, n, _ in FAMILIES}
    fam_kinds = {f: k for f, _, k in FAMILIES}
    for family, entries in grouped.items():
        lid = f"sys-{family}"
        lanes.append(lane(lid, fam_names.get(family, family), family, fam_kinds.get(family, "capability"),
                          "runtime", f"Runtime stage: {fam_names.get(family, family).lower()}.", len(entries)))
        for index, (cid, name, detail, cmd) in enumerate(entries):
            comps.append({"id": cid, "name": name, "lane": lid, "family": family,
                          "kind": fam_kinds.get(family, "capability"), "detail": detail, "order": index,
                          "cmd": {k: cmd for k in ("windows", "wsl", "macos", "linux")} if cmd else None})
    return lanes, comps


def hook_lanes() -> tuple[list, list]:
    """Hooks are the zero-token enforcement layer, so they get their own lanes."""
    lanes, comps = [], []
    for path in sorted((ROOT / "scripts" / "hooks").glob("*.py")):
        lid = f"hook-{path.stem}"
        text = path.read_text(encoding="utf-8")
        guards = sorted(set(re.findall(r"^([A-Z_]{4,})\s*=", text, re.M)))
        lanes.append(lane(lid, path.stem.replace("_", " "), "validation", "control",
                          f"scripts/hooks/{path.name}", first_comment(path, ('"""',)),
                          len(guards) or 1))
        for index, guard in enumerate(guards[:6]):
            comps.append({"id": f"{lid}-{guard}", "name": guard, "lane": lid, "family": "validation",
                          "kind": "control", "detail": f"Rule table in {path.name}.", "order": index})
    return lanes, comps


def skill_lanes() -> tuple[list, list]:
    lanes, comps = [], []
    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        lid = f"skill-{path.parent.name}"
        text = path.read_text(encoding="utf-8")
        heads = re.findall(r"^##\s+(.+)$", text, re.M)
        desc = re.search(r"^description:\s*(.+)$", text, re.M)
        lanes.append(lane(lid, path.parent.name, "skills", "capability",
                          f"skills/{path.parent.name}/SKILL.md",
                          (desc.group(1).strip() if desc else ""), len(heads) or 1))
        for index, head in enumerate(heads[:6]):
            comps.append({"id": f"{lid}-{index}", "name": head[:48], "lane": lid, "family": "skills",
                          "kind": "capability", "detail": f"Rule group in {path.parent.name}.",
                          "order": index})
    return lanes, comps


# Every surface a person might actually be sitting in front of, grouped by what
# you can DO to it, which is the distinction the old single-select client picker
# could not make.
#
# The honest split is not vendor, it is whether a shell command reaches it:
#
#   local-client  a CLI on this machine. A command configures it.
#   web-chat      a browser product. NO command reaches it, and offering one
#                 would be a lie. These get a connect-or-paste instruction, and
#                 the instructions come from docs/GLOBAL-AI-SETUP.md rather than
#                 being invented here.
#   local-model   a model this machine can host. Gated by the RAM scan, because
#                 offering `ollama pull` for a tag that will swap is worse than
#                 offering nothing.
#
# Charles runs several of these at once, so the picker is multi-select and the
# output is grouped by what each selection can actually receive.
SURFACES = [
    ("claude-code", "Claude Code", "local-client", "shell",
     "setup-rules-claude", "~/.claude/CLAUDE.md",
     "Terminal, desktop and IDE. Also gets the skills and both PreToolUse guards."),
    ("codex", "Codex (GPT)", "local-client", "shell",
     "setup-rules-codex", "~/.codex/AGENTS.md",
     "The GPT coding surface. --client gpt is accepted as an alias."),
    ("copilot-cli", "GitHub Copilot CLI", "local-client", "shell",
     "setup-rules-copilot", "~/.copilot/copilot-instructions.md",
     "Also sets COPILOT_CUSTOM_INSTRUCTIONS_DIRS so Copilot reads the repository."),
    ("gemini-cli", "Gemini CLI", "local-client", "shell",
     "setup-rules-gemini", "~/.gemini/GEMINI.md",
     "Shares its rules file with Antigravity, which reads the same path."),
    ("antigravity", "Google Antigravity, local or paid model", "local-client", "shell",
     "setup-rules-antigravity", "~/.gemini/GEMINI.md + ~/.gemini/config/skills/",
     "The same client setup covers a paid Google model or a local model. It installs "
     "the shared rules, every skill and the PreInvocation prompt hook."),
    ("cursor", "Cursor, desktop and CLI", "local-client", "shell",
     "setup-rules-cursor", "~/.cursor/rules/ + ~/.cursor/skills/ + ~/.cursor/hooks.json",
     "Agent chat and code share the always-applied rules and skills. Session context and shell guards reinforce them."),

    ("chatgpt-web", "ChatGPT, web and app chat", "web-chat", "connect", None,
     "Account and project instructions",
     "No shell command reaches a browser product. Connect GitHub with access to "
     "Charlesganu2004/Master-Repo-Use, reference it for repository work, and put "
     "the auto-mode block in your account or project instructions. Never secrets."),
    ("claude-web", "Claude, web chat and Cowork", "web-chat", "connect", None,
     "Project knowledge and preferences",
     "Add the private repository to the relevant Claude project, or use Claude "
     "Code on the web against it. CLAUDE.md stays committed so repo-aware "
     "sessions get the same rules. Profile preferences carry the rest."),
    ("gemini-web", "Gemini, web and app chat", "web-chat", "connect", None,
     "Saved info and Gems",
     "Paste the auto-mode block into saved info, or into a Gem for work that "
     "should always carry it. The committed GEMINI.md covers the CLI, not this."),
    ("copilot-web", "GitHub Copilot, web and IDE chat", "web-code", "connect", None,
     ".github/copilot-instructions.md",
     "Repository-aware Copilot reads the committed instructions file when it "
     "operates on this repository. Reach from other repositories depends on that "
     "session's permissions, so it is not something this setup can grant."),
    ("copilot-agent", "GitHub Copilot coding agent", "web-code", "connect", None,
     ".github/hooks/master-repo-auto.json + .github/copilot-instructions.md",
     "Repository hooks inject the pipeline and check shell calls in the coding agent's Linux job. Requires this repository in scope."),
    ("cursor-web", "Cursor Cloud Agents", "web-code", "connect", None,
     ".cursor/rules/master-repo-auto.mdc + .cursor/hooks.json",
     "Tracked rules and guards travel with the repository. Enable Sync Skills for Cloud Agents in Cursor settings to carry personal skills too."),
    ("codex-web", "Codex web", "web-code", "connect", None,
     "AGENTS.md + project skills",
     "Connect this repository to the cloud task. Its committed instructions apply; local home-directory hooks do not transfer to a hosted worker."),
    ("gemini-code-assist", "Gemini Code Assist", "web-code", "connect", None,
     ".gemini/config.yaml + .gemini/styleguide.md",
     "Automated pull request review reads the committed .gemini config rather "
     "than any home directory file. It reviews; it never approves."),
]


# Say what can truly be enforced for each surface. A global instructions file is
# persistent, but it is not the same mechanism as a native per-prompt hook. The
# web UI exposes this distinction so it never promises a hook a product lacks.
SURFACE_ENFORCEMENT = {
    "claude-code": {
        "kind": "native-hook", "label": "Every-prompt hook",
        "detail": "UserPromptSubmit injects the standing pipeline before every prompt and slash command.",
    },
    "antigravity": {
        "kind": "native-hook", "label": "Every-prompt hook",
        "detail": "PreInvocation injects the same pipeline before local-model and paid-model calls.",
    },
    "codex": {
        "kind": "native-hook", "label": "Prompt hook, trust required",
        "detail": "AGENTS.md persists globally. Review installed UserPromptSubmit and PreToolUse definitions in Codex's Hooks UI before they execute.",
    },
    "copilot-cli": {
        "kind": "native-hook", "label": "Every-prompt hook",
        "detail": "userPromptTransformed prepends the pipeline, sessionStart reinforces it, and PreToolUse guards matching shell commands.",
    },
    "cursor": {
        "kind": "session-hook-rules", "label": "Always rule + session hook",
        "detail": "The alwaysApply rule covers Agent chat and code. sessionStart injects context; preToolUse guards shell commands. Cursor Tab is separate.",
    },
    "gemini-cli": {
        "kind": "global-rules", "label": "Global instructions",
        "detail": "GEMINI.md carries the standing rules for every CLI session.",
    },
    "chatgpt-web": {
        "kind": "web-instructions", "label": "Account or project rules",
        "detail": "Paste the exact protected block into account or project instructions.",
    },
    "claude-web": {
        "kind": "web-instructions", "label": "Project rules",
        "detail": "Project knowledge and preferences carry the block in hosted chat.",
    },
    "gemini-web": {
        "kind": "web-instructions", "label": "Saved info or Gem",
        "detail": "Saved info or a dedicated Gem carries the block in hosted chat.",
    },
    "copilot-web": {
        "kind": "repo-instructions", "label": "Repository rules",
        "detail": "The committed Copilot instructions apply when this repository is in scope.",
    },
    "copilot-agent": {
        "kind": "native-hook", "label": "Repository hooks",
        "detail": "The coding agent loads committed prompt and tool hooks for this repository; ordinary web chat does not run them.",
    },
    "cursor-web": {
        "kind": "repo-instructions", "label": "Project rule + tool guards",
        "detail": "The cloud worker loads tracked always rules and preToolUse guards, plus project skills or explicitly synced personal skills.",
    },
    "codex-web": {
        "kind": "repo-instructions", "label": "Repository instructions",
        "detail": "The connected repository supplies AGENTS.md and project skills; local user hooks remain on the local machine.",
    },
    "gemini-code-assist": {
        "kind": "repo-instructions", "label": "Repository rules",
        "detail": "Committed Gemini configuration applies to repository review work.",
    },
}

AUTO_MODE_FILE = ROOT / "docs" / "auto-mode-block.txt"


def surface_entries() -> list[dict]:
    """The two fixed groups. Local models are added by the client after the scan."""
    return [{
        "id": ident, "name": name, "group": group, "runs": runs,
        "setupRecipe": recipe, "target": target, "detail": detail,
        "enforcement": SURFACE_ENFORCEMENT[ident],
    } for ident, name, group, runs, recipe, target, detail in SURFACES]


def local_model_surfaces() -> list[dict]:
    """Every vetted ollama tag, carrying the RAM floor the client gates on.

    Emitted in full and filtered in the browser rather than filtered here,
    because the machine doing the build is not the machine being set up.
    """
    models = [m for m in HARDWARE_PROFILES["models"] if m.get("runtime") == "ollama"]
    models.sort(key=lambda m: (m["min_ram_gb"], m["params_b"], m["tag"]))
    return [{
        "id": _model_slug(m["tag"]),
        "name": m["tag"],
        "group": "local-model",
        "runs": "shell",
        "setupRecipe": f"setup-{_model_slug(m['tag'])}",
        "target": f"{m['vendor']}, {m['params_b']}B at {m['quant']}",
        "minRamGb": m["min_ram_gb"],
        "detail": f"{m['use']} Licence: {m['license']}.",
        "launchCommands": {
            "windows": (f"$prompt=Read-Host 'Prompt'; $prompt | python "
                        f"(Join-Path $HOME 'Master-Repo-Use/scripts/auto_mode_harness.py') --model {m['tag']}"),
            "wsl": (f"read -r -p 'Prompt: ' prompt; printf '%s' \"$prompt\" | python3 "
                    f"\"$HOME/Master-Repo-Use/scripts/auto_mode_harness.py\" --model {m['tag']}"),
            "macos": (f"read -r -p 'Prompt: ' prompt; printf '%s' \"$prompt\" | python3 "
                      f"\"$HOME/Master-Repo-Use/scripts/auto_mode_harness.py\" --model {m['tag']}"),
            "linux": (f"read -r -p 'Prompt: ' prompt; printf '%s' \"$prompt\" | python3 "
                      f"\"$HOME/Master-Repo-Use/scripts/auto_mode_harness.py\" --model {m['tag']}"),
            "other": (f"printf '%s' \"$PROMPT\" | python3 "
                      f"\"$HOME/Master-Repo-Use/scripts/auto_mode_harness.py\" --model {m['tag']}"),
        },
        "enforcement": {
            "kind": "runtime-command", "label": "RAM-gated runtime",
            "detail": "The generated command installs this vetted Ollama tag. Tick Antigravity separately when it is the client that will use it.",
        },
    } for m in models]


# --------------------------------------------------------------- the store
#
# Charles asked to be shown what "indexed" and "the MongoDB store" actually
# mean, rather than told. The honest way to show it is to render the index
# definitions that scripts/monitor-indexes.js really creates, so the page cannot
# drift into describing a store that does not exist. This parses that file
# instead of restating it: change the file and the page follows.

STORE_INDEX_FILE = ROOT / "scripts" / "monitor-indexes.js"

_CREATE_RE = re.compile(
    r"db\.(\w+)\.createIndex\(\s*(\{.*?\})\s*,\s*(\{.*?\})\s*\)\s*;",
    re.DOTALL)

# What each index is FOR, in the words of the question it answers. The comments
# in the .js file say this too, but a comment is prose above a statement and this
# has to survive as a field. Keyed by index name so a renamed index fails loudly
# in the test rather than rendering an empty cell.
INDEX_QUESTIONS = {
    "actor_recent": (
        "What did this person do in the last hour?",
        "Walks one actor's events newest first. Without it, answering for one "
        "person reads every event ever captured and sorts the lot in memory."),
    "project_recent": (
        "What happened on this repository today?",
        "The same walk keyed by project, which is the query behind a standup "
        "rollup for a team rather than a person."),
    "source_unique": (
        "Has this capture already been ingested?",
        "Unique, so a restarted capture agent re-ingesting a window is a no-op. "
        "Without it the day silently doubles and every count built on it is wrong."),
    "events_ttl": (
        "What is old enough to delete?",
        "expireAfterSeconds: 0 means expire at the moment stored in expires_at, "
        "so retention is a property of the document. A shorter window for one "
        "person needs no index change. The field must be a Date and the index "
        "must stay single-field; MongoDB silently never expires anything if "
        "either is wrong."),
    "scope_period": (
        "Which summary covers last week for this scope?",
        "Summaries deliberately have no TTL. They outlive the events they were "
        "built from, which is the entire reason for summarising."),
    "project_period": (
        "Which summaries mention this project?",
        "projects is an array field, so this is a multikey index: one document "
        "with four projects gets four index entries and matches any of them."),
    "consent_lookup": (
        "Is capture currently permitted for this person and scope?",
        "One indexed lookup. A permission check that costs a collection scan "
        "becomes a permission check somebody caches, and then it is an "
        "assumption rather than a check."),
}

# One captured event, with the fields that make the indexes above work. Shown as
# the shape rather than described, because "a document store" means nothing until
# you have seen a document.
STORE_DOCUMENT = {
    "collection": "events",
    "fields": [
        ("_id", "ObjectId", "Assigned by MongoDB."),
        ("source_id", "string",
         "Stable id from the capture agent: machine, stream and frame. The unique index is on this."),
        ("actor", "string", "Who was at the keyboard. Indexed with ts."),
        ("project", "string", "Repository or working directory. Indexed with ts."),
        ("ts", "Date", "When it happened. The -1 half of both compound indexes."),
        ("kind", "string", "chat, commit, terminal, window or ocr."),
        ("text", "string", "The transcribed or captured text. This is the part that needs redaction."),
        ("expires_at", "Date",
         "When this document deletes itself. Must be a Date; a string or an epoch number "
         "means the TTL index quietly never fires."),
    ],
}

# Search is the question that gets answered wrong most often, so the two facts
# that actually decide the architecture are recorded with their date.
STORE_SEARCH = [
    ("Regular queries and the indexes above",
     "Every MongoDB edition, including a single local mongod. This is what the "
     "monitor needs for summaries, rollups and retention."),
    ("$search, full text",
     "Was Atlas only. Self-managed from MongoDB 8.2, which runs a separate mongot "
     "binary alongside mongod and requires a replica set, even a single-node one. "
     "Checked 2026-09-04."),
    ("$vectorSearch, semantic",
     "Same mechanism and the same mongot requirement. Wanted only if summaries "
     "should be searchable by meaning rather than by actor, project and time."),
]


def store_indexes() -> list[dict]:
    """Parse the real createIndex calls so the page cannot drift from the file."""
    text = STORE_INDEX_FILE.read_text(encoding="utf-8")
    out = []
    for collection, keys, options in _CREATE_RE.findall(text):
        name = re.search(r'name:\s*"([^"]+)"', options)
        name = name.group(1) if name else "unnamed"
        keys = " ".join(keys.split())
        question, why = INDEX_QUESTIONS.get(name, ("", ""))
        out.append({
            "collection": collection,
            "name": name,
            "keys": keys,
            "unique": "unique: true" in options,
            "ttl": "expireAfterSeconds" in options,
            "question": question,
            "why": why,
        })
    return out


def store_payload() -> dict:
    return {
        "file": "scripts/monitor-indexes.js",
        "doc": "docs/CHAT-CODE-MONITOR.md",
        "command": "mongosh monitor --file scripts/monitor-indexes.js",
        "document": STORE_DOCUMENT,
        "indexes": store_indexes(),
        "search": [{"mode": m, "detail": d} for m, d in STORE_SEARCH],
    }


def design_pages() -> list[dict]:
    """Every interactive design, read from the files rather than listed by hand.

    The root index.html had no link to designs/ at all, so twenty-eight working
    designs were published and unreachable. Fixing that by hand-listing them in
    two places is how the list goes stale on the twenty-ninth, so the list is
    derived: filename, plus the <title> the page already declares.
    """
    pages = []
    for path in sorted((ROOT / "designs").glob("d*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        title = re.search(r"<title>(.*?)</title>", text, re.S)
        note = re.search(r'<meta name="description" content="(.*?)"', text, re.S)
        if not title:
            continue                  # not a design page if it does not name itself
        name = title.group(1).split("|")[0].strip()
        pages.append({
            "file": f"designs/{path.name}",
            "name": name,
            "detail": (note.group(1).strip() if note else ""),
        })
    return pages


def build() -> dict:
    lanes, comps = [], []
    for producer in (stage_lanes, model_setup_lane, antigravity_model_lane, global_rules_lane,
                 catalog_lanes, script_lanes, workflow_lanes,
                 test_lanes, doc_lanes, hook_lanes, skill_lanes):
        l, c = producer()
        lanes.extend(l)
        comps.extend(c)

    # Every locally generated lane is part of Master-Repo-Use and shares one
    # idempotent setup recipe. Catalog repositories and named third-party
    # runtime surfaces fail closed until a vetted recipe is recorded.
    for component in comps:
        if component.get("slug"):
            component["action"] = {"kind": "reference", "state": "review-required"}
            continue
        # A hosted model is signed into, not installed. It is not fail-closed and
        # it is not pending a recipe: there is nothing for a recipe to do.
        if component.get("hosted"):
            component["setupState"] = "hosted"
            component["action"] = {"kind": "reference", "state": "hosted"}
            continue
        own = STAGE_OWN_RECIPES.get(component["id"])
        if own:
            component["setupRecipe"] = own
        is_runtime_stage = component.get("lane", "").startswith("sys-")
        # A component that already carries its own reviewed recipe keeps it. The
        # model tags are runtime nodes by lane prefix but are not fail-closed:
        # each one names a vendor runtime and an exact tag, already reviewed.
        if component.get("setupRecipe"):
            component["setupState"] = "ready"
        elif not is_runtime_stage or component["id"] in MASTER_SETUP_STAGE_IDS:
            component["setupRecipe"] = MASTER_SETUP_RECIPE["id"]
            component["setupState"] = "ready"
        else:
            component["setupState"] = "unavailable"
        component["action"] = {
            "kind": "operation" if component.get("cmd") else "roadmap",
            "state": "ready" if component.get("cmd") else "reference",
        }

    routes = [{"id": r[0], "name": r[1], "detail": r[2], "members": r[3],
               "bestFor": r[4], "requires": r[5]} for r in ROUTES]

    # Cross-listed catalog entries: say so rather than looking like duplicates.
    lane_of = {c["id"]: c["lane"] for c in comps}
    homes: dict[str, list[str]] = {}
    for component in comps:
        slug = component.get("slug")
        if slug:
            homes.setdefault(slug, []).append(component["lane"])
    for component in comps:
        slug = component.get("slug")
        if slug and len(homes[slug]) > 1:
            others = [l for l in homes[slug] if l != component["lane"]]
            component["alsoIn"] = others
            component["detail"] = (component["detail"].rstrip(".")
                                   + f". Also listed in {len(others)} other lane(s).")

    by_id = {c["id"]: c for c in comps}
    for route in routes:
        for member in route["members"]:
            if member in by_id:
                by_id[member].setdefault("routes", []).append(route["id"])
        for a, b in zip(route["members"], route["members"][1:]):
            for x, y in ((a, b), (b, a)):
                if x in by_id and y != x:
                    by_id[x].setdefault("connects", [])
                    if y not in by_id[x]["connects"]:
                        by_id[x]["connects"].append(y)

    # Lane level connections, so a design can draw lane-to-lane wiring.
    lane_of = {c["id"]: c["lane"] for c in comps}
    for route in routes:
        route["lanes"] = sorted({lane_of[m] for m in route["members"] if m in lane_of})

    return {
        "meta": {"lanes": len(lanes), "components": len(comps), "routes": len(routes),
                 "families": len(FAMILIES),
                 "note": "Generated by scripts/build_atlas_data.py. Do not hand-edit."},
        "families": [{"id": f, "name": n, "kind": k} for f, n, k in FAMILIES],
        "lanes": lanes,
        "components": comps,
        "setupRecipes": ([MASTER_SETUP_RECIPE] + model_setup_recipes() + [LOCAL_HARNESS_RECIPE]
                     + global_rules_recipes() + antigravity_recipes()),
        "designs": design_pages(),
        "store": store_payload(),
        "autoMode": {
            "source": "docs/auto-mode-block.txt",
            "summary": "The exact protected rules used by installers and hosted-web setup.",
            "text": AUTO_MODE_FILE.read_text(encoding="utf-8"),
        },
        "surfaces": surface_entries() + local_model_surfaces(),
        "surfaceGroups": [
            {"id": "local-client", "name": "Code, CLI and desktop agents",
             "note": "Select every client you use. Setup commands install its rules, skills and supported hooks for chat and code."},
            {"id": "web-chat", "name": "Web and app chat",
             "note": "Configure account or project instructions once in each product. Local shell commands cannot change a hosted chat account."},
            {"id": "web-code", "name": "Web coding and IDE assistants",
             "note": "Connect the repository so committed rules and supported cloud hooks apply. Personal skills may need a separate sync."},
            {"id": "local-model", "name": "Local models",
             "note": "Filtered by the memory you enter above. A tag your machine cannot hold is not offered, because a model that swaps is worse than no model."},
        ],
        "profiles": PROFILES,
        "profileClients": PROFILE_CLIENTS,
        "routes": routes,
        "hardware": [{"id": i, "label": l, "verdict": v, "gb": g, "detail": d, "models": m}
                     for i, l, v, g, d, m in HARDWARE],
    }


def main() -> int:
    mirrored_skills = sync_project_skills(ROOT)
    data = build()
    payload = json.dumps(data, indent=1)
    OUT.write_text(payload, encoding="utf-8")
    if OUT_DESIGNS.parent.is_dir():
        OUT_DESIGNS.write_text(payload, encoding="utf-8")
        banner = (
            "/* Generated by scripts/build_atlas_data.py. Do not hand-edit.\n"
            "   Exists so the designs work from file://, where fetch is blocked\n"
            "   outright but a <script src> tag still loads. */\n"
        )
        OUT_DESIGNS_JS.write_text(
            banner + "window.__ATLAS_DATA__ = " + payload + ";\n", encoding="utf-8")
    m = data["meta"]
    print("atlas-data.json written to root and designs/")
    print(f"  project skills {len(mirrored_skills)} mirrored into .agents/skills")
    for key in ("lanes", "components", "routes", "families"):
        print(f"  {key:<11}{m[key]}")
    families: dict[str, int] = {}
    for entry in data["lanes"]:
        families[entry["family"]] = families.get(entry["family"], 0) + 1
    print("  lanes per family:", ", ".join(f"{k} {v}" for k, v in sorted(families.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
