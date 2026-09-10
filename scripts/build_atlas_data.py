#!/usr/bin/env python3
"""Generate atlas-data.json, the single data layer every atlas design reads.

All atlas designs share this file. Without it they drift, and a lane added to
one quietly goes missing from the others.

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
import sys
import re

from sync_project_skills import sync_project_skills
from capability_definitions import owned_agents

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts" / "hooks"))
import catalog_index_spec  # noqa: E402
import skill_pipeline  # noqa: E402

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
    # One command instead of thirty-five. Charles asked for the models to be in
    # the repository so nobody visits a model page; the weights cannot be (the
    # smallest is 2.6x GitHub's file limit and the set is 42x the repository
    # cap), so this is the command that does the same job from the repository,
    # pinned to the digests in docs/model-manifest.json and verified against them.
    _fetch = "vendor_models.py --fetch --auto-hardware"
    _plan = "vendor_models.py --plan --auto-hardware"
    setups.append(("fetch-all-models", "Fetch every model this machine can hold",
                   "models",
                   "Measures this machine's RAM, then pulls catalogued tags within that "
                   "limit and verifies their weight bytes against docs/model-manifest.json. Nothing "
                   "goes through Hugging Face, and afterwards the machine needs no "
                   "network for these.",
                   {"windows": f"python scripts/{_fetch}",
                    "wsl": f"python3 scripts/{_fetch}",
                    "linux": f"python3 scripts/{_fetch}",
                    "macos": f"python3 scripts/{_fetch}",
                    "other": f"python3 scripts/{_fetch}"}))
    setups.append(("plan-models", "See what would be fetched, and what it costs",
                   "models",
                   "Prints every model that fits, its size, whether it is licence-clean "
                   "to redistribute, and the total download. Downloads nothing.",
                   {"windows": f"python scripts/{_plan}",
                    "wsl": f"python3 scripts/{_plan}",
                    "linux": f"python3 scripts/{_plan}",
                    "macos": f"python3 scripts/{_plan}",
                    "other": f"python3 scripts/{_plan}"}))
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
     "Validates the standing pipeline and reads installed hook registrations without "
     "dumping private client settings. File registration does not prove a client has "
     "trusted or executed its hook; check that in the client's own interface.",
     _with_clone({
         "windows": "python (Join-Path $p 'scripts/auto_mode_harness.py') --check; python (Join-Path $p 'scripts/verify_auto_mode.py') --repo $p --installed-only",
         **{key: 'python3 "$p/scripts/auto_mode_harness.py" --check && python3 "$p/scripts/verify_auto_mode.py" --repo "$p" --installed-only'
            for key in ("wsl", "macos", "linux", "other")},
     })),

    # Verifies BOTH halves. The rules half is a block in a file; the skills half is
    # a directory of folders, and a setup that wrote the block and silently failed
    # to copy the skills would look identical without the second command.
    ("rules-verify", "Verify what was written", "instructions",
     "Reads back exact protected instruction blocks, every copied skill resource and "
     "client-specific hook schemas. Reports missing or changed files without editing "
     "anything or displaying credentials. Clients not installed are explicitly skipped.",
     _with_clone({
         "windows": "python (Join-Path $p 'scripts/verify_auto_mode.py') --repo $p --installed-only",
         **{key: 'python3 "$p/scripts/verify_auto_mode.py" --repo "$p" --installed-only'
            for key in ("wsl", "macos", "linux", "other")},
     })),
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

# --------------------------------------------------------- the harness family
#
# Five harnesses, and the differences are not cosmetic: each one stands in a
# different place, and the place decides what it can enforce. A page that listed
# them as four similar tools would hide the only thing worth knowing about them.
HARNESSES = [
    ("auto-mode-harness", "Surface harness", "scripts/auto_mode_harness.py",
     "Configures each surface by the strongest mechanism it supports: a hook where "
     "there is one, a request gateway for local models, a paste bundle for a browser "
     "product. Installs the enforced skills as folders where folders exist.",
     "Setting a machine up, or adding a new client. It also installs the "
     "computer-control and browser-automation skills, so the agents can reach "
     "Playwright and desktop control once you enable a host.",
     "Cannot reach a program that was already running, and cannot reach a browser "
     "tab at all except through text a person pastes.",
     "python scripts/auto_mode_harness.py --check"),

    ("harness-proxy", "Proxy harness", "scripts/harness_proxy.py",
     "An OpenAI and Ollama compatible proxy. Point any client's base URL at it and "
     "every request that client makes carries the pipeline, whether or not the "
     "program knows the rules exist.",
     "Anything talking to a local model that you cannot configure: an IDE plugin, a "
     "notebook, a desktop app, a script somebody wrote last year. A Playwright or "
     "agent run pointed at it inherits the rules without being told.",
     "Only covers traffic routed through it, and only for model servers speaking "
     "those two API shapes. It never logs prompts, so it cannot tell you what was asked.",
     "python scripts/harness_proxy.py --check"),

    ("harness-wrap", "Wrapper harness", "scripts/harness_wrap.py",
     "Wraps one command invocation and puts the rules in front of the prompt, by "
     "argument, standard input, a file path or an environment variable.",
     "A CLI client with no hook and no configurable base URL, which is most of them, "
     "including a Playwright runner, a desktop-control host, or an agent invoked "
     "as a one-off command.",
     "One invocation at a time, and a profile that has not been checked against a "
     "real client says so rather than guessing at its flags.",
     "python scripts/harness_wrap.py --check"),

    ("harness-goal", "Goal harness", "scripts/harness_goal.py",
     "The surface harness plus a standing goal that survives the turn. The goal is "
     "restated before the request is read, checked against the output before "
     "answering, and reported at the end. /goal, \\goal and goal: all set it.",
     "Work that spans more than one turn, which is when a session drifts from what "
     "it was for while nothing errors. It carries the goal into every agent, "
     "browser step and computer-control action too.",
     "Adds about 544 bytes to every prompt while a goal is set. Lifted only by the "
     "person who set it.",
     "python scripts/harness_goal.py --check"),

    ("harness-super", "Super harness", "scripts/harness_super.py",
     "One command that does what the other four do, by calling them rather than "
     "reimplementing any of them: installs every surface, serves the injecting "
     "proxy, wraps a single command, carries the standing goal, and routes "
     "computer-control and Playwright work. On top of that it injects a longer "
     "chain of ten named passes, adding architect before anything is produced, "
     "token reduction throughout, and an adversarial review before answering.",
     "Work that spans turns and touches more than one kind of task, on any model "
     "local or hosted, where you want one command instead of four and the model "
     "to name each pass it ran. Agents, browser steps and desktop control all "
     "inherit the same chain.",
     "It costs about three times the base pipeline per turn, roughly 1600 tokens "
     "with a goal set, because every pass is named explicitly on every prompt. "
     "It adds no reach the other four lack: what it cannot do, they cannot "
     "either, and a machine it has not installed is a machine it cannot enforce "
     "anything on.",
     "python scripts/harness_super.py --check")
]


# ------------------------------------------------------------------ the layers
#
# Parsed from skill_pipeline.CORE, never restated. The page showed the layers as
# hand-written prose once, and the prose said ten rules while the hook injected
# eleven the same afternoon. A page that describes a rule it does not read is a
# page that will eventually describe a rule that no longer exists.
#
# The same reasoning as catalog_index_spec: one source, parsed by everyone who
# needs it, so a change lands everywhere at once or nowhere.
LAYER_HEADER = re.compile(r"^LAYER (?P<number>\d), (?P<when>[^:]+):$")

# The rule name is the leading run of capitals; everything after it is the body.
# Three shapes exist and the first version of this pattern only read one:
#
#   "1. CAVEMAN. Compress ..."          name, full stop, body
#   "3. ANTI-SLOP. No em dashes ..."    a HYPHEN in the name
#   "10. NEVER COMPACT a skill ..."     no separator; the name is the sentence
#
# It matched nine of eleven rules and looked right, because nine rules rendered
# and nobody counts. The count assertion below is the part that actually guards
# this: a rule the hook injects and the page does not show is drift that no
# amount of reading the page reveals.
LAYER_RULE = re.compile(
    r"^(?P<number>\d+)\. (?P<name>[A-Z][A-Z0-9 \-]*[A-Z0-9])[.:]?\s+(?P<body>.+)$")

LAYER_PLAIN = {
    1: ("Before it reads what you asked",
        "Say it short, say all of it, and do not dress it up."),
    2: ("Before it makes anything",
        "Think it through first, and make it look like someone chose how it looks."),
    3: ("While it works, and again before it answers",
        "Pick the right tools, tidy what it wrote, then check the first layer again."),
}


def layer_rules() -> list[dict]:
    """Every layer and every rule inside it, read from the hook's own text."""
    layers, current = [], None
    for line in skill_pipeline.CORE.splitlines():
        line = line.strip()
        header = LAYER_HEADER.match(line)
        if header:
            number = int(header.group("number"))
            plain, simple = LAYER_PLAIN.get(number, ("", ""))
            current = {"number": number, "when": header.group("when").strip(),
                       "plain": plain, "simple": simple, "rules": []}
            layers.append(current)
            continue
        rule = LAYER_RULE.match(line)
        if rule and current is not None:
            current["rules"].append({
                "number": int(rule.group("number")),
                "name": rule.group("name").strip(),
                "body": rule.group("body").strip(),
            })
    # Count what the source has, then insist the parse found all of it. Nine of
    # eleven rules parsed cleanly and silently before this line existed.
    expected = len([line for line in skill_pipeline.CORE.splitlines()
                    if re.match(r"^\d+\. ", line.strip())])
    found = sum(len(layer["rules"]) for layer in layers)
    if found != expected:
        raise SystemExit(f"the layer parser read {found} of {expected} rules in "
                         f"skill_pipeline.CORE; the page would show fewer rules "
                         f"than the hook injects")
    return layers


def super_chain_payload() -> dict:
    """The super harness's extra passes, read from the script that injects them."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import harness_super  # noqa: E402

    return {
        "name": "Super harness",
        "file": "scripts/harness_super.py",
        "check": "python scripts/harness_super.py --check",
        "note": "One command that calls the other four, plus a longer chain of "
                "named passes on top of the three layers.",
        "passes": [{
            "step": index,
            "label": label,
            "skill": skill,
            "when": when,
            # A pass that extends a base rule points at its number; only a pass
            # that adds something carries its own text.
            "baseRule": base_rule,
            "rule": rule,
        } for index, (label, skill, base_rule, when, rule)
            in enumerate(harness_super.PASSES, start=1)],
    }


def layer_payload() -> dict:
    """The layers, the lanes that attach on top, and the commands that run them.

    Every command here is one that exists and passes its own check. A page that
    prints a command nobody ran is the failure this repository keeps hitting.
    """
    layers = layer_rules()
    total = sum(len(layer["rules"]) for layer in layers)
    return {
        "layers": layers,
        "ruleCount": total,
        "byteCount": len(skill_pipeline.CORE.encode("utf-8")),
        "source": "scripts/hooks/skill_pipeline.py",
        "note": "Parsed from the hook's own text. Nothing on this page restates a rule.",
        "goal": {
            "captured": True,
            "detail": "The first substantive prompt of a session becomes the standing "
                      "goal with nothing typed, and rides every turn until the work is "
                      "finished or it is lifted. Continuations, one-word replies and "
                      "questions ending in a question mark are skipped, because they "
                      "serve the goal already standing rather than replacing it.",
            "spellings": ["/goal <text>", "\\goal <text>", "/mastergoal <text>",
                          "goal: <text>"],
            "clear": "goal clear",
            "override": "A goal set with one of those spellings is marked explicit, and "
                        "an explicit goal is never replaced by capture.",
            "store": ".auto-mode/goal.json, which is not tracked. "
                     "docs/auto-mode-goal.json is the committed seed.",
        },
        "lanes": [{"line": line.split(": ", 1)[0].split(". ", 1)[-1],
                   "detail": line.split(": ", 1)[1] if ": " in line else line}
                  for _pattern, line in skill_pipeline.LANES],
        # The super harness chain, read from harness_super rather than retyped.
        # Same rule as the layers directly above: a page that restates a rule
        # drifts from it silently, and this repository has paid for that twice.
        "superChain": super_chain_payload(),
        "commands": [
            {"label": "See exactly what a prompt would inject",
             "command": "python scripts/harness_goal.py --context \"refactor the retry module\""},
            {"label": "Check the hook end to end",
             "command": "echo '{\"input\": {\"prompt\": \"plan a page\"}}' | "
                        "python scripts/hooks/skill_pipeline.py"},
            {"label": "Show the standing goal",
             "command": "python scripts/harness_goal.py --show"},
            {"label": "Set one deliberately",
             "command": "python scripts/harness_goal.py --set \"finish the designs\""},
            {"label": "Lift it",
             "command": "python scripts/harness_goal.py --clear"},
            {"label": "Install every surface",
             "command": "python scripts/auto_mode_harness.py --install all"},
            {"label": "Verify the install",
             "command": "python scripts/verify_auto_mode.py"},
        ],
    }


def harness_entries() -> list[dict]:
    return [{"id": h[0], "name": h[1], "file": h[2], "detail": h[3],
             "useWhen": h[4], "limit": h[5], "check": h[6],
             "computerControl": {
                 "skill": "master-computer-control",
                 "file": "scripts/harness_computer.py",
                 "check": "python scripts/harness_computer.py --check",
                 "routes": ["native", "browser-js", "browser-rust"],
                 "kind": "capability-router",
                 "name": "Computer-control availability check",
                 "detail": "All four injection harnesses route screen and browser requests through "
                           "the same capability skill. The check reads local evidence; "
                           "it does not grant tools, install packages or control an app.",
             }} for h in HARNESSES]


# ------------------------------------------------------- more runtime stages
#
# Every entry below is a file or capability that exists in this repository. The
# atlas is a map of what is here, so a component that names something aspirational
# would make the map lie in the direction that costs the most: you would go
# looking for it.
EXTRA_STAGES = [
    # Intake and routing
    ("intake", "goal-gate", "Goal gate", "Carries the session goal into every prompt and checks the answer against it.", "python scripts/harness_goal.py --show"),
    ("intake", "prompt-shape", "Prompt shape", "Decides whether a request is one task or several, which is what triggers fan-out.", None),
    ("intake", "retrieval-first", "Retrieval before assert", "Anything that changes gets looked up rather than recalled.", None),

    # Client surfaces
    ("surfaces", "cursor", "Cursor", "Editor surface. Rules arrive by an always-apply rule; the guards run on preToolUse.", "cursor"),
    ("surfaces", "chatgpt-web", "ChatGPT", "Browser surface. No shell, so the rules and skills arrive as a pasted bundle.", None),
    ("surfaces", "claude-web", "Claude on the web", "Browser surface. Preferences carry the pipeline, project knowledge carries the skills.", None),
    ("surfaces", "claude-cowork", "Claude cowork", "Shared space. No per-user hook, so the standing text is the whole mechanism.", None),
    ("surfaces", "gemini-code-assist", "Gemini Code Assist", "Automated review. Reads committed .gemini config; it reviews and never approves.", None),

    # Harnesses, as runtime stages rather than only as documentation
    ("intake", "harness-surface", "Surface harness", "Installs hooks, skills and bundles for every surface that accepts one.", "python scripts/auto_mode_harness.py --check"),
    ("intake", "harness-proxy-stage", "Proxy harness", "Injects the pipeline into every request routed through it.", "python scripts/harness_proxy.py --check"),
    ("intake", "harness-wrap-stage", "Wrapper harness", "Puts the rules in front of one wrapped command.", "python scripts/harness_wrap.py --check"),
    ("intake", "harness-goal-stage", "Goal harness", "Carries a standing goal across turns and checks the work against it.", "python scripts/harness_goal.py --check"),
    ("intake", "computer-control-router", "Computer-control routes", "Read-only availability checks for native Computer Use, official Playwright and a Rust application browser-testing route. Skills describe use; only the host can grant actual tools and permissions.", "python scripts/harness_computer.py --check"),

    # Skills that the pipeline actually enforces
    ("skills", "master-caveman", "master-caveman", "Layer 1 compression, applied to every build, command and lane.", None),
    ("skills", "master-token-reducer", "master-token-reducer", "Compact retrieval packets for large repositories.", None),
    ("skills", "master-full-output", "master-full-output", "Finish the deliverable; no skeleton where an implementation was asked for.", None),
    ("skills", "master-anti-slop", "master-anti-slop", "One theme, one accent, one radius scale, and no em dashes.", None),
    ("skills", "master-plan", "master-plan", "State the read and the approach before producing anything.", None),
    ("skills", "master-design-taste", "master-design-taste", "Design read and dials before any visible surface is built.", None),
    ("skills", "master-goal", "master-goal", "The goal survives the turn, and only the person who set it lifts it.", None),
    ("skills", "verify-before-complete", "verify-before-complete", "Run the check and quote real output before claiming a result.", None),
    ("skills", "cite-or-abstain", "cite-or-abstain", "Cite what was read, or say the claim is unverified.", None),
    ("skills", "scope-guard", "scope-guard", "Deliver the scope asked for, no wider and no narrower.", None),
    ("skills", "dep-audit", "dep-audit", "What to read before adding anything third-party.", None),

    # Tools
    ("tools", "catalog-skill-install", "install_catalog_skill", "The reviewed route into a skill root. Refuses an uncatalogued slug.", "python scripts/install_catalog_skill.py --list"),
    ("tools", "watch-sources", "watch_sources", "Polls agentskill.sh for candidates and scans them. Writes a queue, never the catalog.", "python scripts/watch_sources.py --report"),
    ("tools", "local-advisor", "local_model_advisor", "Reads real memory and reports which tags this machine can host.", "python scripts/local_model_advisor.py"),
    ("tools", "verify-tags", "verify_model_tags", "Checks every model tag in the catalog against the vendor list.", "python scripts/verify_model_tags.py"),
    ("tools", "build-atlas", "build_atlas_data", "Regenerates the atlas payload. The site is generated, never hand-edited.", "python scripts/build_atlas_data.py"),
    ("tools", "build-site", "build_public_site", "Builds the published gallery in privacy mode.", "python scripts/build_public_site.py"),
    ("tools", "sync-skills", "sync_project_skills", "Mirrors skills/ into the shared .agents/skills discovery path.", "python scripts/sync_project_skills.py --repo ."),
    ("tools", "store-indexes", "monitor-indexes", "Creates the seven indexes the activity store queries against.", "mongosh monitor --file scripts/monitor-indexes.js"),

    # Validation and safety
    ("validation", "no-compress-hook", "No-compress hook", "Blocks a compressor or a truncating write aimed at a capability definition.", None),
    ("validation", "pipeline-hook", "Standing pipeline hook", "Injects the three layers on every prompt, for five clients.", "echo '{}' | python scripts/hooks/skill_pipeline.py"),
    ("validation", "catalog-security", "catalog_security", "The scanners and the redaction rules every intake path shares.", None),
    ("validation", "static-audit", "static_audit", "Deterministic checks that need no model and no network.", "python scripts/static_audit.py"),
    ("validation", "freshness-gate", "catalog_freshness_gate", "Fails the build when the catalog status is too old to trust.", "python scripts/catalog_freshness_gate.py"),

    # Observability
    ("observability", "security-trail", "security_trail", "Append-only record of what was scanned, when, and with what result.", "python scripts/security_trail.py --tail"),
    ("observability", "catalog-status", "Catalog status", "Healthy, stale, review and remove counts across the whole catalog.", "python scripts/check_freshness.py"),
    ("observability", "actions-budget", "actions_budget", "What the scheduled workflows cost in minutes.", "python scripts/actions_budget.py"),

    # Automation
    ("automation", "guardian-job", "Catalog Guardian", "Weekly metadata pass plus a rotating deep scan. Opens an issue; never merges.", None),
    ("automation", "watch-job", "Watch Sources", "Weekly poll of the watched sources, with the scan and the queue commit.", None),
    ("automation", "pages-job", "Pages", "Publishes the gallery when the designs or the atlas data change.", None),
    ("automation", "approval-job", "Owner approval", "The passcode gate on anything that changes the catalog.", None),

    # Knowledge and retrieval
    ("knowledge", "activity-store", "Activity store", "MongoDB collections for events, summaries and consent, with a TTL on events only.", "mongosh monitor --file scripts/monitor-indexes.js"),
    ("knowledge", "hardware-profiles", "Hardware profiles", "The vetted table of model tags and the memory each one needs.", "python scripts/generate_hardware_profiles.py"),

    # Delivery
    ("delivery", "bundle-out", "Paste bundle", "One file carrying the rules and every enforced skill, for a surface with no hook.", "python scripts/auto_mode_harness.py --bundle chatgpt"),
    ("delivery", "repo-instructions", "Committed instructions", "The two instruction files that are versioned rather than set per account.", "python scripts/auto_mode_harness.py --install copilot-web,gemini-code-assist"),
]


# ---------------------------------------------------------- more hybrid routes
#
# A route is a real division of labour, not a preset. Each names the pieces it
# needs and the condition under which it is the right answer, because a route
# recommended outside its condition is worse than no route.
EXTRA_ROUTES = [
    ("goal-carried", "Goal carried across turns",
     "The goal rides every prompt and the answer is checked against it, not against the last message.",
     ["goal-gate", "harness-goal-stage", "claude-code"], "multi-turn work", "any"),
    ("proxy-everything", "Proxy every local client",
     "One proxy in front of the model server, so programs you cannot configure still get the rules.",
     ["harness-proxy-stage", "hardware-gate"], "mixed local tooling", "8 GB RAM minimum"),
    ("wrap-one-tool", "Wrap a single tool",
     "For a CLI with no hook: the rules go in front of the prompt for that one invocation.",
     ["harness-wrap-stage", "claude-code"], "an unhooked client", "any"),
    ("bundle-browser", "Bundle for a browser surface",
     "No shell to run against, so the rules and every enforced skill go in as one pasted file.",
     ["bundle-out", "chatgpt-web", "claude-web"], "chat-only surfaces", "any"),
    ("cowork-shared", "Shared space, shared rules",
     "A cowork space has no per-user hook, so the standing text in project knowledge is the mechanism.",
     ["bundle-out", "claude-cowork"], "a team space", "any"),
    ("review-committed", "Review from committed config",
     "Automated review reads what is in the repository, so the rules ship with the branch.",
     ["repo-instructions", "gemini-code-assist", "branch-pr"], "pull request review", "any"),
    ("scan-before-adopt", "Scan before adopting",
     "A candidate is cloned read-only, scanned by every installed scanner, and queued rather than installed.",
     ["watch-sources", "catalog-security", "catalog-skill-install"], "third-party skills", "any"),
    ("guarded-compress", "Compress under guard",
     "Compression runs, and the no-compress guard refuses anything aimed at a capability definition.",
     ["caveman-compact", "no-compress-hook", "token-gain"], "long context", "any"),
    ("retrieve-then-answer", "Retrieve then answer",
     "Anything that changes is looked up and cited rather than recalled.",
     ["retrieval-first", "lane-match", "cite-or-abstain"], "version and pricing questions", "any"),
    ("plan-verify-loop", "Plan, act, verify",
     "The plan is written down first and the claim is checked against real output before it is made.",
     ["master-plan", "verify-before-complete", "branch-pr"], "anything multi-step", "any"),
    ("design-taste-pass", "Design read before build",
     "A visible surface gets an audit and a stated aesthetic before anything is replaced.",
     ["master-design-taste", "master-anti-slop"], "UI work", "any"),
    ("tier-two-models", "Two local models",
     "A small model drafts and a larger local model reviews, with no hosted call at any point.",
     ["hardware-gate", "harness-proxy-stage"], "offline with memory to spare", "32 GB RAM"),
    ("embed-and-search", "Embed then search",
     "Local embeddings feed the activity store, and search runs against the index rather than the transcript.",
     ["activity-store", "store-indexes"], "monitor and summary work", "8 GB RAM minimum"),
    ("audit-trail", "Scan, record, report",
     "Every scan appends to the trail, so a finding can be traced to the run that produced it.",
     ["catalog-security", "security-trail", "catalog-status"], "security review", "any"),
    ("budget-then-fan", "Budget, then fan out",
     "The token target is checked first, and only what fits is parallelised.",
     ["budget-check", "actions-budget", "token-gain"], "fixed budgets", "any"),
    ("full-machine-setup", "Whole machine, one pass",
     "Every hooked client, the committed files, and the models this machine can hold.",
     ["harness-surface", "hardware-gate", "repo-instructions"], "a new laptop", "16 GB RAM"),
    ("ui-build-review", "Design, build, test, review",
     "Maxwell scopes the work, Canvas defines the visible flow, Atlas builds it, Probe tests it and Sentinel reviews permissions. A handoff plan, not an unattended launch.",
     ["agent-orchestrator-maxwell", "agent-ui-canvas", "agent-fullstack-atlas", "agent-tester-probe", "agent-security-sentinel"], "interactive UI releases", "any"),
    ("catalog-to-library", "Catalog into a private library",
     "Schema defines the collections, Dex prepares reviewed records, Vector checks retrieval and Lock checks for secrets before an owner-approved upload.",
     ["agent-data-arch-schema", "agent-data-dex", "agent-rag-vector", "agent-secret-scanner-lock"], "private MongoDB catalog", "any"),
    ("incident-debug-test", "Reproduce, diagnose, verify",
     "Pulse records impact, Trace isolates the fault and Probe turns the reproduction into a regression test before a fix is released.",
     ["agent-incident-pulse", "agent-debugger-trace", "agent-tester-probe"], "broken buttons or failed commands", "any"),
    ("source-audit-adopt", "Research before adoption",
     "Aria checks primary sources, Vault performs static intake, Delta checks dependency health and Sentinel reviews remaining risk. No candidate code runs during intake.",
     ["agent-research-aria", "agent-scanner-vault", "agent-dependency-watch-delta", "agent-security-sentinel"], "new tools and skills", "any"),
    ("mcp-bounded-connect", "Connect with least privilege",
     "Forge selects the MCP adapter, Weave maps its interface and Sentinel checks directory and tool scopes. Credentials stay in backend environment variables.",
     ["agent-mcp-forge", "agent-connector-weave", "agent-security-sentinel"], "MCP and API integration", "any"),
    ("hardware-cost-review", "Size before serving",
     "The hardware gate supplies measured memory, Model Picker chooses compatible candidates, Tempo measures latency and Penny tracks token cost.",
     ["hardware-gate", "agent-model-picker", "agent-perf-bench-tempo", "agent-token-penny"], "local and hosted model selection", "any"),
    ("docs-release-sync", "Docs stay with the release",
     "Echo compares instructions with behavior, Quill updates setup guidance and Relay checks the release handoff against verified output.",
     ["agent-doc-drift-echo", "agent-writer-quill", "agent-handoff-relay"], "documentation and release handoff", "any"),
    ("memory-cite-answer", "Retrieve, cite, preserve",
     "Recall finds project evidence, Memo organizes it and Aria checks source-backed claims. Capability definitions remain whole; only ordinary prose may be shortened.",
     ["agent-memory-recall", "agent-knowledge-memo", "agent-research-aria"], "long-running projects", "any"),
    ("release-security-gate", "Test, scan, publish",
     "Vera challenges coverage, Probe runs checks, Lock scans outbound artifacts and Volt prepares deployment. Publishing still follows owner approval gates.",
     ["agent-test-analyst-vera", "agent-tester-probe", "agent-secret-scanner-lock", "agent-devops-volt"], "production releases", "any"),
    ("first-run-onboarding", "From empty screen to first command",
     "Guide designs the first-run path, Canvas makes controls discoverable and Help checks the wording and recovery instructions.",
     ["agent-onboarding-guide", "agent-ui-canvas", "agent-support-help"], "new-user setup", "any"),
    ("cost-aware-cloud", "Architecture with a cost check",
     "Nimbus proposes the deployment boundary, Cirrus evaluates operating cost and Tempo checks throughput assumptions before any paid resource is created.",
     ["agent-cloud-arch-nimbus", "agent-cost-cirrus", "agent-perf-bench-tempo"], "cloud planning", "any"),
    ("adversarial-goal-check", "Goal and evidence review",
     "Maxwell records acceptance criteria, Lens checks context integrity, Ghost challenges unsupported claims and Vera checks that tests cover the actual goal.",
     ["agent-orchestrator-maxwell", "agent-context-auditor-lens", "agent-redteam-ghost", "agent-test-analyst-vera"], "multi-turn completion audits", "any"),
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
] + EXTRA_STAGES

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
] + EXTRA_ROUTES

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
                # An entry whose slug is too long for the note column has its
                # note on the NEXT line instead, and it was being dropped: the
                # page showed "Catalogued in <file>" where a measurement was
                # written. Seven entries across the catalog were in that state,
                # and the shape is invisible in the file because the note is
                # right there, one line down. Only the first such line is taken,
                # matching the inline convention where the rest is continuation.
                elif entries and not entries[-1][2]:
                    slug, sub, _empty = entries[-1]
                    entries[-1] = (slug, sub, text.lstrip("# ").strip())
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


def agent_lanes() -> tuple[list, list]:
    """Real role contracts, not just upstream agent frameworks or heading counts."""
    lanes, comps = [], []
    for agent in owned_agents(ROOT):
        lid = f"role-{agent['id']}"
        lanes.append(lane(lid, agent["name"], "agents", "capability", agent["path"], agent["detail"], 1))
        path = agent["path"]
        comps.append({"id": agent["id"], "name": agent["name"], "lane": lid,
                      "family": "agents", "kind": "capability", "order": 0,
                      "sub": agent["category"], "detail": agent["detail"],
                      "definitionPath": path, "role": agent["role"],
                      "cmd": {key: (f"Get-Content -LiteralPath '{path}' -Raw" if key == "windows"
                                     else f"cat '{path}'")
                              for key in ("windows", "wsl", "linux", "macos", "other")}})
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
    """Parse the real createIndex calls so the page cannot drift from the file.

    Same shared parser as the catalog store, pointed at a different file. This
    was the third hand-rolled copy of the same regex in the repository, and two
    of the three grew an identical dotted-key bug that had to be fixed twice.

    Only the question and the why are added here. Those are this page's own
    writing about an index; everything factual about the index comes from the
    file, including the TTL flag, because only this store expires anything and
    the catalog is rewritten wholesale.
    """
    out = []
    for index in catalog_index_spec.parse(STORE_INDEX_FILE):
        question, why = INDEX_QUESTIONS.get(index["name"], ("", ""))
        out.append({
            "collection": index["collection"],
            "name": index["name"],
            "keys": index["keys"],
            "unique": index["unique"],
            "ttl": index["ttl"],
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


# ------------------------------------------------------- the catalog in MongoDB
#
# Charles asked to see the atlas index backed by MongoDB. The index definitions
# live in scripts/catalog-indexes.js and are parsed here rather than restated, on
# the same principle as the monitor store: a page that describes a store drifts
# from it the moment anyone edits the definitions, and nothing notices.
#
# scripts/load_catalog_mongo.py --check verifies every claim below against the
# real documents. It caught two mistakes in the first draft of that file: a unique
# index that would have failed on load because fifteen runtime lanes share one
# sentinel source, and a sparse flag on a field every document carries.

CATALOG_INDEX_FILE = ROOT / "scripts" / "catalog-indexes.js"

# The collections the catalog loads into, and why each one is a collection rather
# than a field on another. Counts come from the payload itself at build time.
# Nine collections, and the first four are the ones Charles asked to be able to
# open. They could have been a family filter over components, and were, but then
# `show collections` answers with one bucket you have to already know the field
# name to search. A collection you can see is worth the duplication.
CATALOG_COLLECTIONS = {
    "skills": ("Every indexed skill. Definitions this repository owns carry their whole "
               "SKILL.md in definition.body; the catalogued ones carry the "
               "record and never the code."),
    "agents": ("Owned specialist roles carry complete contracts and checksums. Catalogued "
               "frameworks carry source references and the health last recorded."),
    "tools": ("Scripts and binaries. All of these are ours, so each names the "
              "file it lives in and the command that runs it."),
    "mcp": ("MCP servers and connectors, two local against the rest catalogued."),
    "components": ("Every capability in one place, including the four above. "
                   "Kept for the queries that cross families."),
    "lanes": ("The groups components sit in. A lane is backed by a file, except "
              "the runtime stages, which carry the sentinel source \"runtime\"."),
    "routes": ("Hybrid routes. members and lanes are arrays, so the indexes over "
               "them are multikey."),
    "surfaces": ("Clients, chat surfaces and local model tags, which is what the "
                 "setup picker reads."),
    "recipes": ("The reviewed commands. Fetched by id constantly, so _id "
                "already carries most of the load."),
}

# What each index is FOR, in the question it answers. Keyed by index name so a
# rename surfaces as a missing explanation rather than the wrong one attached to
# new keys, the same way the monitor store does it.
CATALOG_QUESTIONS = {
    "family_kind": (
        "Which components are in this family, and of this kind?",
        "The two rows of filter chips on every design. One index serves both, "
        "because a compound index answers its own leading prefix: no separate "
        "family-only index is needed and adding one would only cost writes."),
    "lane_order": (
        "What is inside this lane, in the author's order?",
        "Clicking a lane. order is the second key so the sort comes off the "
        "index; without it MongoDB would fetch then sort in memory."),
    "component_search": (
        "Which components mention this word?",
        "The search box. A text index rather than a regex, because a regex "
        "without a left anchor cannot use a btree at all. Weighted 10 to 2 so a "
        "name match outranks a description match."),
    "by_recipe": (
        "Which components can actually be set up?",
        "What the Build basket collects. Sparse: {recipeCoverage} carry a recipe, "
        "so the index skips the rest instead of storing a null for each."),
    "lane_family_size": (
        "Which lanes are in this family, biggest first?",
        "count descends in the index itself, so the ordering is free."),
    "lane_source": (
        "Which lane came from this file?",
        "Unique, but partial. {runtimeLanes} runtime lanes share the sentinel source "
        "\"runtime\", so a plain unique index rejects the load on the second one. "
        "The loader marks real files with isFileSource: true. Include that predicate "
        "in file lookups so MongoDB may use the partial index."),
    "route_members": (
        "Which hybrid routes touch this component?",
        "members is an array, so this is multikey: a route naming four "
        "components gets four index entries and matches on any of them."),
    "route_lanes": (
        "Which routes cross this lane?",
        "The same multikey shape over the lanes array."),
    "surface_group_ram": (
        "Which surfaces are in this group, and which fit this memory?",
        "Not sparse, though minRamGb is missing on {ramMissing}. A compound sparse "
        "index only skips a document missing EVERY indexed field, and group is "
        "on all of them, so sparse would skip nothing while claiming otherwise."),
    "skill_origin": (
        "What do we own, and what are we only pointing at?",
        "origin leads because it is the line that matters: a local skill carries "
        "its full text, a catalogued one carries a record and never its code."),
    "agent_origin": (
        "Which agents are ours and which are catalogued?",
        "Separates local role contracts from referenced upstream agent frameworks."),
    "tool_origin": (
        "Which tools are ours and which are catalogued?",
        "Filters tools by owned implementation or catalog reference, then name."),
    "mcp_origin": (
        "Which MCP servers are ours and which are catalogued?",
        "Finds owned MCP adapters separately from catalogued upstream servers."),
    "skill_health": (
        "Which catalogued skills have gone stale or failed a scan?",
        "Sparse: documents without recorded upstream health are omitted."),
    "agent_health": (
        "Which agent repositories have gone stale or failed a scan?",
        "Sparse: owned agent contracts have no upstream lifecycle record, while "
        "catalogued frameworks may carry one."),
    "mcp_health": (
        "Which MCP servers have gone stale or failed a scan?",
        "Sparse: local adapters without upstream health are omitted."),
    "skill_fulltext": (
        "Which skill actually says this?",
        "Searches the whole SKILL.md, not a one-line summary, which is the "
        "difference between a catalog and a library. Weighted 10, 4, 1 so a name "
        "beats a description and a description beats the body."),
    "skill_lane": (
        "Which skills come from this lane?",
        "The lane is what vouches for a catalogued entry."),
    "agent_lane": ("Which agents come from this lane?",
                   "The lane is what vouches for a catalogued entry."),
    "tool_lane": ("Which tools come from this lane?",
                  "The lane is the file or script the tool was read from."),
    "mcp_lane": ("Which MCP servers come from this lane?",
                 "The lane is what vouches for a catalogued entry."),
    "recipe_ready": (
        "Which recipes are reviewed and ready?",
        "kind then state, because every query filters kind first."),
}

# The queries the interface really makes, each named with the index that serves
# it. This is the list load_catalog_mongo.py --check validates.
CATALOG_QUERIES = [
    ("components", "family_kind", "{ family: 'skills' }"),
    ("components", "family_kind", "{ family: 'skills', kind: 'capability' }"),
    ("components", "lane_order", "{ lane: 'sys-intake' }"),
    ("components", "by_recipe", "{ setupRecipe: { $exists: true } }"),
    ("components", "component_search", "{ $text: { $search: 'caveman' } }"),
    ("lanes", "lane_family_size", "{ family: 'knowledge' }"),
    ("lanes", "lane_source", "{ source: 'repo-lists/agent-skills.txt', isFileSource: true }"),
    ("routes", "route_members", "{ members: 'claude-code' }"),
    ("routes", "route_lanes", "{ lanes: 'sys-skills' }"),
    ("surfaces", "surface_group_ram", "{ group: 'local-model', minRamGb: { $lte: 16 } }"),
    ("recipes", "recipe_ready", "{ kind: 'setup', state: 'ready' }"),
]


def catalog_indexes() -> list[dict]:
    """Parse the real createIndex calls so the page cannot drift from the file.

    Parsing is catalog_index_spec's job, shared with load_catalog_mongo.py. This
    file had its own copy, and the two copies grew the same dotted-key bug: a
    quoted path like "health.status" matched no field, so every nested index came
    through with an empty field list. Found once, fixed twice. Only the page's
    own additions, the question and the why, are attached here.
    """
    out = []
    for index in catalog_index_spec.parse(CATALOG_INDEX_FILE):
        question, why = CATALOG_QUESTIONS.get(index["name"], ("", ""))
        out.append(dict(index, question=question, why=why))
    return out


# ------------------------------------------------------- the plain-language layer
#
# Charles asked that every design be understandable by a non-technical reader, a
# beginner engineer, and an experienced one, all from the same page.
#
# The audit that prompted this: 17 families shipped with ZERO descriptions, so
# every design showed a chip reading "Intake and routing" with nothing to say what
# that meant. Lane descriptions existed but were circular stubs, "Runtime stage:
# intake and routing", which explains nothing to anyone. Meanwhile the word "lane"
# appeared 1,523 times in the shipped data, "recipe" 784, "MCP" 649.
#
# The answer is not to simplify the technical text. An experienced engineer needs
# "a compound index answers its own leading prefix" and a first-time visitor needs
# "this is a list of things the computer can do". Writing one sentence that serves
# both serves neither.
#
# So every explained thing carries TWO registers, and the reader picks:
#
#   plain      No jargon at all. What it is, in the words someone would use who
#              has never opened a terminal. One or two sentences.
#   technical  What it actually is, with the real names, for someone who will go
#              on to run the commands.
#
# GLOSSARY covers the words that cannot be avoided, because they are the names of
# the things. A reader meets "lane" 1,523 times; it has to be defined once,
# somewhere they will find it.

# The six kinds a component can be. These are the coarsest cut in the whole
# system, so they are the first thing that has to make sense.
KIND_PLAIN = {
    "instruction": (
        "Rules that tell an AI assistant how to work.",
        "Written guidance loaded into the model's context: standing rules, "
        "prompt-level policy and the pipeline that enforces them."),
    "capability": (
        "Something that does a job. A tool, an assistant, or an add-on.",
        "Executable capability: a skill pack, a CLI tool, an agent framework or "
        "an MCP server the client can call."),
    "knowledge": (
        "Reference material. Things to look something up in.",
        "Retrieval surfaces and reference corpora: catalogs, indexes, embedding "
        "stores and the documents behind them."),
    "control": (
        "Safety checks. Things that stop a mistake before it happens.",
        "Policy and verification: guards, approval gates, scanners and the hooks "
        "that block a destructive call before it runs."),
    "model": (
        "The AI models themselves, and what your computer can run.",
        "Inference runtimes and model tags, sized against real memory by the "
        "hardware advisor."),
    "delivery": (
        "Getting finished work out: builds, branches and publishing.",
        "Build, review and publish workflows, including the branch and pull "
        "request path every change takes."),
}

# The 17 families. Every design renders these as filter chips, and until now not
# one of them said what it was.
FAMILY_PLAIN = {
    "intake": (
        "Where a request arrives and gets sorted before any work starts.",
        "Request normalisation, scope resolution, lane matching, budget and "
        "hardware gating. Everything that runs before the model reads the task."),
    "surfaces": (
        "The apps you actually type into: Claude, ChatGPT, Copilot, Gemini and the rest.",
        "Client surfaces, each with its own instruction file, hook mechanism and "
        "skill directory. Where the standing rules have to be installed."),
    "identity": (
        "Who is allowed to approve what, and keeping passwords out of the code.",
        "Owner approval gates, workspace trust and secret scoping. Only Charles "
        "approves catalog maintenance, by passcode."),
    "instructions": (
        "The written rules every assistant follows on every message.",
        "The always-loaded instruction layer: the protected block, the three "
        "layers and the no-compaction policy."),
    "skills": (
        "Instruction packs an assistant loads when they fit the job.",
        "Skill definitions with frontmatter, discovered by name and description, "
        "loaded on demand rather than every session."),
    "tools": (
        "Programs you run directly from a terminal.",
        "Scripts and binaries in this repository plus catalogued third-party "
        "tools, each with the exact command per platform."),
    "mcp": (
        "Connectors that let an assistant reach another program or service.",
        "Model Context Protocol servers: the standard way a client exposes "
        "external tools and data to a model."),
    "agents": (
        "Assistants that carry out a multi-step job on their own.",
        "Agent frameworks and kits, catalogued with licence and health, for work "
        "that fans out rather than running in one pass."),
    "plugins": (
        "Add-ons installed into an assistant to extend it.",
        "Marketplace and installed plugin state for clients that support them."),
    "knowledge": (
        "Places to look things up: catalogs, search indexes and stored documents.",
        "Retrieval and reference: the repository catalog, the activity store and "
        "the embedding models that search them."),
    "models": (
        "The AI models, and which ones your computer has the memory to run.",
        "Model tags and serving runtimes, filtered by a real memory floor rather "
        "than offered and left to swap."),
    "hybrid": (
        "Ways to split one job across several models to save money or improve answers.",
        "Hybrid routes: local-first with hosted escalation, draft and review, "
        "parallel voting, and the conditions each is correct under."),
    "validation": (
        "Checks that catch problems: security scans and rules that block mistakes.",
        "Guards, scanners and verification: the no-prune and no-compress hooks, "
        "the security scanners and the freshness gate."),
    "observability": (
        "Seeing what happened: what was saved, what was scanned, what it cost.",
        "Token savings, catalog status, the security trail and the workflow "
        "minute budget."),
    "automation": (
        "Jobs that run on a schedule without anyone starting them.",
        "Scheduled GitHub Actions: the catalog guardian, the source poller, the "
        "Pages publish and the owner approval gate."),
    "delivery": (
        "Publishing finished work and getting it reviewed.",
        "Branch, pull request and publish workflows. Nothing lands on main "
        "without review."),
    "domain": (
        "Collections for specific subjects, like trading or design.",
        "Subject-specific catalog lanes grouped away from the system lanes."),
}

# The words a reader cannot avoid, because they are the names of the things.
GLOSSARY = [
    ("lane", "A group of related things, like a shelf in a library.",
     "A catalog grouping, backed by a file in repo-lists/ or generated from a "
     "script. Every component belongs to exactly one."),
    ("component", "One single thing in the catalog: a tool, a skill, a model.",
     "One catalog entry. Carries an id, a lane, a family, a kind, a description "
     "and often a command per platform."),
    ("family", "A broad category that groups lanes together.",
     "One of 17 top-level groupings. Drives the first row of filter chips."),
    ("harness", "The thing that makes the rules apply automatically, without you asking.",
     "The mechanism that injects the standing pipeline into every request: a "
     "client hook, a request proxy, a command wrapper or a standing goal."),
    ("skill", "A set of instructions an assistant loads when it fits the job.",
     "A directory holding a SKILL.md with name and description frontmatter, "
     "discovered and loaded on demand by the client."),
    ("MCP", "A standard plug that lets an assistant talk to another program.",
     "Model Context Protocol. A server exposes tools and resources; the client "
     "presents them to the model."),
    ("hybrid route", "A plan for splitting work between a local model and a paid one.",
     "A named division of labour across models, with the condition it is correct "
     "under and the hardware it needs."),
    ("recipe", "A ready-made command that sets something up for you.",
     "A reviewed setup command per platform, with a state of ready or "
     "review-required. Only ready recipes reach the Build script."),
    ("hook", "A small program that runs automatically at a set moment.",
     "A client lifecycle callback. UserPromptSubmit injects context; PreToolUse "
     "can block a call before it runs."),
    ("local model", "An AI model that runs on your own computer instead of over the internet.",
     "An Ollama tag served locally, gated on a measured memory floor."),
    ("index", "A shortcut that makes searching fast, like a book's index.",
     "A database index. Without one a query reads every document; with one it "
     "reads only the matching range."),
]

# What each of the fifteen tabs is for, in both registers. The hint already
# existed as a title attribute, which a touch user never sees and a screen reader
# announces inconsistently.
TAB_PLAIN = {
    "map": ("A picture of the whole system.",
            "The full component graph, drawn by whichever design you opened."),
    "index": ("A searchable list of everything.",
              "Flat directory of lanes and components with filters and search."),
    "commands": ("Every command, ready to copy.",
                 "The full command directory for the selected platform, setup and "
                 "run labelled separately."),
    "agents": ("Assistants that do multi-step jobs.",
               "Agent frameworks and the jobs that act on them."),
    "skills": ("Instruction packs, loaded when they fit.",
               "Skill definitions discovered by description."),
    "tools": ("Programs you run yourself.",
              "Scripts and binaries with their exact commands."),
    "plugins": ("Add-ons for your assistant.",
                "Marketplace and installed plugin state."),
    "mcp": ("Connectors to other programs.",
            "Model Context Protocol servers and connectors."),
    "harness": ("How the rules get applied automatically.",
                "The three layers, the five harnesses that deliver them, and every check command."),
    "routes": ("Ways to split work between models.",
               "Hybrid routes with their conditions and hardware floors."),
    "hardware": ("What your computer can run.",
                 "Memory-based tiering against the vetted model list."),
    "easy": ("Set everything up in a few clicks.",
             "Pick your surfaces and depth; it writes only those commands."),
    "build": ("Collect what you want, get one script.",
              "The basket, combined into one commands-only script per platform."),
    "custom": ("Add your own groups.",
               "Lanes you define, stored in this browser only."),
    "suggest": ("Suggest something to add.",
                "Local suggestion queue; nothing is sent anywhere."),
}


def plain_payload() -> dict:
    """Both registers for everything a reader meets, plus the glossary."""
    return {
        "kinds": {k: {"plain": v[0], "technical": v[1]} for k, v in KIND_PLAIN.items()},
        "families": {k: {"plain": v[0], "technical": v[1]} for k, v in FAMILY_PLAIN.items()},
        "tabs": {k: {"plain": v[0], "technical": v[1]} for k, v in TAB_PLAIN.items()},
        "glossary": [{"term": t, "plain": p, "technical": x} for t, p, x in GLOSSARY],
        "orientation": {
            "plain": (
                "This page lists everything this system can do, and gives you the "
                "exact command to set each piece up. Start with Easy setup: tick "
                "the apps you use and it writes the commands for you. Nothing here "
                "runs on its own, and nothing is sent anywhere."),
            "technical": (
                "A generated catalog of 1,190 components across 238 lanes, with "
                "per-platform setup recipes, hybrid routes and a hardware advisor. "
                "The payload is built by scripts/build_atlas_data.py and every "
                "lane is grounded in a file that exists."),
        },
    }


def orphan_skill_count(comps: list[dict]) -> int:
    """Skills this repository owns that no component names.

    Three of the fifteen were in that position, and the loader adds them to the
    skills collection so a skill we wrote is never missing from the database.
    Written as a rule rather than the number three, because the number is right
    until somebody writes a sixteenth skill.
    """
    named = {c["id"] for c in comps} | {c["name"] for c in comps}
    orphans = 0
    for path in sorted((ROOT / "skills").iterdir()):
        definition = path / "SKILL.md"
        if not path.is_dir() or not definition.is_file():
            continue
        declared = ""
        for line in definition.read_text(encoding="utf-8").splitlines()[:12]:
            if line.startswith("name:"):
                declared = line.split(":", 1)[1].strip()
                break
        if path.name not in named and declared not in named:
            orphans += 1
    return orphans


def catalog_store_payload(counts: dict, facts: dict) -> dict:
    """facts carries the counts the prose quotes, so a number on the page cannot
    disagree with the catalog it describes. The first draft said "593 of 1120"
    against a catalog of 1126."""
    indexes = catalog_indexes()
    for index in indexes:
        index["why"] = index["why"].format(**facts)
    by_name = {i["name"]: i for i in indexes}
    queries = []
    for collection, index_name, filter_text in CATALOG_QUERIES:
        index = by_name.get(index_name)
        queries.append({
            "collection": collection,
            "index": index_name,
            "filter": filter_text,
            "keys": index["keys"] if index else "",
            "stage": "TEXT" if index and index["text"] else "IXSCAN",
            "scanned": counts.get(collection, 0),
        })
    return {
        "file": "scripts/catalog-indexes.js",
        "loader": "scripts/load_catalog_mongo.py",
        "createCommand": "mongosh atlas --file scripts/catalog-indexes.js",
        "loadCommand": "python scripts/load_catalog_mongo.py --load",
        "checkCommand": "python scripts/load_catalog_mongo.py --check",
        "collections": [
            {"name": name, "count": counts.get(name, 0), "detail": detail,
             "indexes": [i["name"] for i in indexes if i["collection"] == name]}
            for name, detail in CATALOG_COLLECTIONS.items()
        ],
        "indexes": indexes,
        "queries": queries,
        "totalDocuments": sum(counts.values()),
    }


# Who each design suits, and how to move around it, in plain words.
#
# The <meta name="description"> on each page says WHAT it is, in the vocabulary
# of someone who already reads interfaces: "conic specular rim", "orthogonal
# traces", "tonal layers". That is accurate and it is useless to a reader who
# has not met those words, which is most readers.
#
# So every design carries a second line aimed at the person deciding whether to
# open it: who it fits, and the one thing to do first. Keyed by filename so a
# renamed page loses its entry loudly rather than silently keeping the wrong one.
#
# AUDIENCE is one of four, in the order Charles named them, and it is a floor
# rather than a ceiling: an experienced engineer can use the "new to this" ones
# perfectly well, but someone new cannot use the dense ones.
NEW = "New to this"
SOME = "Some technical background"
DEV = "Comfortable with code"
EXPERT = "Reads interfaces for a living"

DESIGN_AUDIENCE = {
    "d3-console.html": (DEV, "Everything on one screen, like a system log. Use the search box; arrows move, enter opens."),
    "d4-orbital.html": (SOME, "Rings of related things. Click any dot to see what it connects to."),
    "d5-blueprint.html": (DEV, "A wiring diagram you can pan and zoom. Drag to move, scroll to zoom, click a box to read it."),
    "d6-graphite.html": (NEW, "A plain stacked list that opens in place. Start at the top and expand what looks relevant."),
    "d7-material.html": (NEW, "Cards and buttons that behave the way a phone app does. Use the side rail to change section."),
    "d8-dossier.html": (NEW, "One subject per page, lots of white space, made for reading rather than hunting."),
    "d8-metro.html": (NEW, "A transit map. Follow one coloured line end to end to see a single path through the system."),
    "d9-workbench.html": (DEV, "Laid out like a code editor: tree on the left, detail on the right, tabs across the top."),
    "d10-journal.html": (NEW, "Reads like an article. Scroll from the top and it explains itself in order."),
    "d11-command.html": (DEV, "A control room. Every tab is a different view of the same catalog; Commands is the useful one."),
    "d12-index.html": (SOME, "Index cards you flip through. Good for browsing when you do not know the name yet."),
    "d13-skill-tree.html": (SOME, "A game-style skill tree. Follow a branch to see what depends on what."),
    "d14-river.html": (SOME, "Work flowing through stages. Follow the current to see the order things happen in."),
    "d15-city.html": (SOME, "A city map. Districts are families; streets connect the things that talk to each other."),
    "d16-declassified.html": (SOME, "A photocopied case file. Click a redaction bar to uncover what is under it."),
    "d17-spatial.html": (SOME, "Frosted glass panels floating over colour. Hover to bring one forward."),
    "d18-boresight.html": (DEV, "A targeting reticle. Everything sits by angle from the centre rather than in rows."),
    "d19-vitrine.html": (NEW, "One object at a time under a museum light. Deliberately shows very little at once."),
    "d20-tube.html": (SOME, "An old curved television. The look is the point; the controls underneath are the standard ones."),
    "d21-poster.html": (NEW, "A printed poster on a strict grid. Flat, bold, nothing moves. Easiest to read at a glance."),
    "d22-membrane.html": (SOME, "Soft cells with no straight lines, breathing slowly. Click a cell to open it."),
    "d23-panes.html": (EXPERT, "Tiled panes snapped to a character cell, one pixel apart. Dense; built for people who like tiling windows."),
    "d24-plate.html": (SOME, "A photographic star plate. Brighter points are used more; click one to read its entry."),
    "d25-riso.html": (SOME, "Printed poster style in two inks. Bold and simple; click any block to open it."),
    "d26-stage.html": (NEW, "A dark stage with one spotlight. Whatever is lit is what you are looking at."),
    "d27-machined.html": (SOME, "A brushed metal instrument face with engraved markings. Reads like a physical control panel."),
    "d28-depth.html": (SOME, "Three layers separated by blur. What is sharp is in front; click to bring a layer forward."),
    "d29-reactor.html": (DEV, "Glowing geometry with a real bloom filter. Heavy on effects; the data underneath is the same."),
    "d30-atrium.html": (NEW, "A bright open space with the content in the shaded part, so the text stays easy on the eyes."),
    "d31-mycelium.html": (SOME, "A root system. Choose a root and it branches into the real lanes underneath it."),
    "d32-broadsheet.html": (NEW, "A newspaper front page. Headlines first, detail below, columns to scan."),
    "d33-switchboard.html": (DEV, "A patch bay. Twelve jacks select real lanes; each jack is also a keyboard button."),
    "d34-bathysphere.html": (SOME, "A descent through water. Items hang at depths; the porthole keeps the text readable."),
    "d35-prism.html": (SOME, "One beam split into colours. Each band is a different way of slicing the same catalog."),
    "d36-mongo.html": (EXPERT, "The catalog as a database console. Three columns, monospace, every number read from the payload."),
}

AUDIENCE_ORDER = (NEW, SOME, DEV, EXPERT)


def design_audience(filename: str) -> tuple[str, str]:
    """(audience, how to use it) for one design, or empty strings.

    Empty rather than invented: a design with no entry says nothing on the page
    instead of guessing, and the test fails so the entry gets written.
    """
    return DESIGN_AUDIENCE.get(filename, ("", ""))


def audience_keys_that_name_nothing() -> list[str]:
    """Entries pointing at a design file that does not exist.

    Fifteen of the first thirty-six did. Each one was written from a name that
    sounded like a design in this repository, every one of them silently did
    nothing, and the page looked correct because a missing key returns empty
    strings on purpose. A wrong key is invisible; only counting catches it.
    """
    real = {path.name for path in (ROOT / "designs").glob("d*.html")}
    return sorted(key for key in DESIGN_AUDIENCE if key not in real)


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
        audience, howto = design_audience(path.name)
        pages.append({
            "file": f"designs/{path.name}",
            "name": name,
            "detail": (note.group(1).strip() if note else ""),
            # The plain layer. `detail` is what it is, in interface vocabulary;
            # these two are who it suits and what to do first.
            "audience": audience,
            "howto": howto,
        })
    return pages


def build() -> dict:
    lanes, comps = [], []
    for producer in (stage_lanes, model_setup_lane, antigravity_model_lane, global_rules_lane,
                 catalog_lanes, script_lanes, workflow_lanes,
                 test_lanes, doc_lanes, hook_lanes, skill_lanes, agent_lanes):
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

    # Bound once so the catalog store counts the list the payload actually ships
    # rather than recomputing it from the producers and landing one short.
    recipes = ([MASTER_SETUP_RECIPE] + model_setup_recipes() + [LOCAL_HARNESS_RECIPE]
               + global_rules_recipes() + antigravity_recipes())

    return {
        "meta": {"lanes": len(lanes), "components": len(comps), "routes": len(routes),
                 "families": len(FAMILIES),
                 "note": "Generated by scripts/build_atlas_data.py. Do not hand-edit."},
        # Both registers travel with the family, so no design has to look them
        # up and none can render a chip with nothing behind it. Seventeen
        # families shipped with no description at all until 2026-09-09.
        "families": [{"id": f, "name": n, "kind": k,
                      "plain": FAMILY_PLAIN.get(f, ("", ""))[0],
                      "technical": FAMILY_PLAIN.get(f, ("", ""))[1]}
                     for f, n, k in FAMILIES],
        "lanes": lanes,
        "components": comps,
        "setupRecipes": recipes,
        "designs": design_pages(),
        "store": store_payload(),
        "harnesses": harness_entries(),
        "pipeline": layer_payload(),
        "plain": plain_payload(),
        "catalogStore": catalog_store_payload({
            "components": len(comps), "lanes": len(lanes), "routes": len(routes),
            "surfaces": len(surface_entries()) + len(local_model_surfaces()),
            "recipes": len(recipes),
            # The four family collections are a slice of components, counted the
            # same way the loader slices them so the page cannot disagree.
            "skills": (sum(1 for c in comps if c["family"] == "skills")
                       + orphan_skill_count(comps)),
            "agents": sum(1 for c in comps if c["family"] == "agents"),
            "tools": sum(1 for c in comps if c["family"] == "tools"),
            "mcp": sum(1 for c in comps if c["family"] == "mcp"),
        }, {
            "recipeCoverage": (f"{sum(1 for c in comps if c.get('setupRecipe'))} "
                               f"of {len(comps)}"),
            "ramMissing": (f"{sum(1 for s in surface_entries() + local_model_surfaces() if not s.get('minRamGb'))} "
                           f"of {len(surface_entries()) + len(local_model_surfaces())}"),
            "runtimeLanes": sum(1 for l in lanes if l.get("source") == "runtime"),
        }),
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
