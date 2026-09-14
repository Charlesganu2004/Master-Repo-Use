#!/usr/bin/env python3
"""One command that puts auto mode on every surface, by whatever means that surface allows.

Charles asked for the harness to cover all of them: chat, code chat, cowork,
GitHub Copilot, ChatGPT, Codex, Claude, Gemini, Gemini Code Assist, Cursor,
Antigravity and local models, and to carry the enforced skills with it.

The surfaces do not accept the same thing, and pretending otherwise is how a
setup step ends up looking like configuration while doing nothing. There are
exactly three mechanisms available, and each surface gets the strongest one it
supports:

  HOOK      A local client that runs a program per turn. The pipeline arrives
            whether or not the model would have thought to look for it, and the
            skills install as folders. Claude Code, Codex, Gemini CLI,
            Antigravity, Cursor, Copilot CLI.

  GATEWAY   A local model has no client to hook, so the request path is the
            only place to stand. This sends the prompt to Ollama with the
            pipeline as the system message. It intercepts requests made THROUGH
            this command; it cannot intercept another application talking to
            Ollama directly, and does not claim to.

  BUNDLE    A browser product has no shell on this machine and no skill folder.
            The strongest available move is one file holding the pipeline and
            every enforced skill, pasted or attached where that product reads
            its standing instructions. ChatGPT, Claude.ai, Claude cowork,
            Gemini web, Copilot on github.com, Gemini Code Assist.

The last two of those are repository files rather than account settings, so they
are written into the repo and committed rather than pasted.

Usage:
    python scripts/auto_mode_harness.py --list
    python scripts/auto_mode_harness.py --check
    python scripts/auto_mode_harness.py --install all --dry-run
    python scripts/auto_mode_harness.py --install claude-code,cursor
    python scripts/auto_mode_harness.py --bundle chatgpt
    python scripts/auto_mode_harness.py --bundle all --out dist/
    python scripts/auto_mode_harness.py --model qwen3:4b --prompt "..."
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "scripts" / "hooks"))

# Where the skills, the block and the goal state actually live. Different in a
# checkout and in a wheel with no checkout anywhere, and this is the only module
# that knows the difference.
import harness_paths  # noqa: E402
import install_auto_mode  # noqa: E402
import sync_project_skills  # noqa: E402


import skill_pipeline  # noqa: E402

# Surface ids are the harness's vocabulary; --client is the installer's. They
# overlap enough to look interchangeable and differ exactly where it matters,
# so the mapping is explicit rather than inferred from a prefix. A surface with
# no entry passes its own id through and the installer validates it.
INSTALLER_CLIENTS = {
    "claude-code": "claude",
    "gemini-cli": "gemini",
    "copilot-cli": "copilot",
}

# The skills that must be present in every auto mode, in the order the pipeline
# applies them. master-repo-auto is the loader the standing block points at, so
# it leads. The rest are layers 1 and 2 of the pipeline made available as skills
# for clients that select by description rather than by hook.
ENFORCED_SKILLS = (
    "master-repo-auto",
    "master-caveman",
    "master-token-reducer",
    "master-full-output",
    "master-anti-slop",
    "master-plan",
    "master-design-taste",
    "master-computer-control",
    "master-graphify",
    "master-refactor",
    "master-refactor-ui",
    "master-architect",
    "master-review",
)

HOOK, GATEWAY, BUNDLE, REPO_FILE = "hook", "gateway", "bundle", "repo-file"

# Every surface Charles named, with what can actually be done to it. `target` is
# where the enforced material lands. A bundle surface names the setting the user
# pastes into, because "configure it in the product" is not an instruction.
SURFACES = {
    "claude-code": {
        "name": "Claude Code", "mechanism": HOOK, "group": "code",
        "target": "~/.claude/CLAUDE.md and ~/.claude/skills/",
        "detail": "UserPromptSubmit injects the pipeline; both PreToolUse guards install.",
    },
    "codex": {
        "name": "Codex", "mechanism": HOOK, "group": "code",
        "target": "~/.codex/AGENTS.md and ~/.codex/skills/",
        "detail": "Hooks require the client to accept their hash, so the written block carries the rules too.",
    },
    "gemini-cli": {
        "name": "Gemini CLI", "mechanism": HOOK, "group": "code",
        "target": "~/.gemini/GEMINI.md and ~/.gemini/skills/",
        "detail": "BeforeAgent returns hookSpecificOutput.additionalContext, appended to the prompt for that turn.",
    },
    "antigravity": {
        "name": "Google Antigravity", "mechanism": HOOK, "group": "code",
        "target": "~/.gemini/GEMINI.md and ~/.gemini/config/skills/",
        "detail": "PreInvocation returns injectSteps. Shares GEMINI.md with the Gemini CLI, so the block is written once.",
    },
    "cursor": {
        "name": "Cursor", "mechanism": HOOK, "group": "code",
        "target": "~/.cursor/hooks.json, ~/.cursor/skills/, .cursor/rules/",
        "detail": "beforeSubmitPrompt returns only continue and user_message, so the always-apply rule carries the per-turn layer and sessionStart reinforces it.",
    },
    "copilot-cli": {
        "name": "GitHub Copilot CLI", "mechanism": HOOK, "group": "code",
        "target": "~/.copilot/copilot-instructions.md, ~/.copilot/hooks/, .github/hooks/",
        "detail": "userPromptTransformed rewrites the model-facing prompt each turn; preToolUse carries the guards.",
    },
    "local-models": {
        "name": "Local models", "mechanism": GATEWAY, "group": "local",
        "target": "http://127.0.0.1:11434/api/chat",
        "detail": "Requests sent through this command carry the pipeline as the system message.",
    },
    "chatgpt": {
        "name": "ChatGPT", "mechanism": BUNDLE, "group": "chat",
        "target": "Settings, Personalization, Custom instructions; or a Project's instructions and files",
        "detail": "Paste the bundle into custom instructions, and attach it as a project file so the skills are retrievable.",
    },
    "claude-web": {
        "name": "Claude.ai", "mechanism": BUNDLE, "group": "chat",
        "target": "Project knowledge, and Settings, Preferences",
        "detail": "Preferences carry the pipeline; project knowledge carries the skills.",
    },
    "claude-cowork": {
        "name": "Claude cowork", "mechanism": BUNDLE, "group": "chat",
        "target": "The cowork space's project knowledge",
        "detail": "Same bundle as Claude.ai. A shared space has no per-user hook, so the standing text is the mechanism.",
    },
    "gemini-web": {
        "name": "Gemini", "mechanism": BUNDLE, "group": "chat",
        "target": "Saved info, or a Gem's instructions",
        "detail": "A Gem holds the whole bundle; Saved info holds the pipeline alone if space is tight.",
    },
    "copilot-web": {
        "name": "GitHub Copilot on github.com", "mechanism": REPO_FILE, "group": "chat",
        "target": ".github/copilot-instructions.md",
        "detail": "Repository-scoped and committed, so it applies to everyone working in this repository.",
    },
    "gemini-code-assist": {
        "name": "Gemini Code Assist", "mechanism": REPO_FILE, "group": "chat",
        "target": ".gemini/config.yaml and .gemini/styleguide.md",
        "detail": "Automated review reads the committed config rather than any home-directory file. It reviews; it never approves.",
    },
}

GROUPS = {
    "code": "Code clients on this machine",
    "local": "Local models",
    "chat": "Chat and review surfaces with no shell",
}


def block_text() -> str:
    """The always-loaded rules block, which is the same text on every surface."""
    return harness_paths.block_path().read_text(encoding="utf-8")


def skill_text(name: str) -> str:
    path = harness_paths.skill_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"enforced skill is missing: {path}")
    return path.read_text(encoding="utf-8")


def missing_skills() -> list[str]:
    return [name for name in ENFORCED_SKILLS
            if not harness_paths.skill_path(name).is_file()]


def build_bundle(surface_id: str, mode: str = "base") -> str:
    """One file carrying the pipeline and every enforced skill.

    A browser product cannot mount a skill folder, so the folder is flattened
    into a document it CAN hold. The skills keep their frontmatter: a client that
    does parse it gets a real skill, and one that does not gets a heading and a
    description, which is what it would have matched on anyway.

    mode="super" adds the ten-pass chain, the /token limit rule and the skills
    the chain names. A chat product has no hook, so the bundle is the only way
    the super harness reaches it at all; before this, `harness_super --bundle`
    wrote the base bundle and a ChatGPT project never saw the chain.
    """
    surface = SURFACES[surface_id]
    lines = [
        f"# Master Repo auto mode for {surface['name']}",
        "",
        f"Where this goes: {surface['target']}",
        "",
        surface["detail"],
        "",
        "This surface has no hook, so this text is not a reminder of the rules,",
        "it is the whole of the enforcement. Keep it in place and keep it whole.",
        "",
        "---",
        "",
        "## The standing rules, applied to every prompt",
        "",
        block_text().strip(),
        "",
        "---",
        "",
    ]
    names = list(ENFORCED_SKILLS)
    if mode == "super":
        import super_chain  # noqa: E402  (beside the hook; on sys.path above)
        lines += [
            "## The super harness, on every prompt",
            "",
            super_chain.super_block(),
            "",
            "### /token limit",
            "",
            "The one command this harness keeps. `/token limit 4000` sets a ceiling",
            "for every answer until `/token limit off`. Plan the answer to fit before",
            "writing, stop at the last clean break before the limit, and end with one",
            "line saying what was left out. This surface cannot cap tokens itself, so",
            "holding to it is on the model.",
            "",
            "---",
            "",
        ]
        names += [n for n in super_chain.EXTRA_SKILLS if n not in names]
    lines += [
        "## The enforced skills",
        "",
        "These are the skills the pipeline selects from. On a client with skill",
        "folders they install as directories; here they are inlined so the same",
        "instructions are available to a surface that can only hold text.",
        "",
    ]
    for name in names:
        lines += [f"### {name}", "", skill_text(name).strip(), "", "---", ""]
    return "\n".join(lines).rstrip() + "\n"


def write_bundles(ids: list[str], out_dir: pathlib.Path, dry: bool,
                  mode: str = "base") -> list[str]:
    results = []
    for surface_id in ids:
        body = build_bundle(surface_id, mode)
        path = out_dir / f"auto-mode-{surface_id}.md"
        if dry:
            results.append(f"would write {path} ({len(body)} bytes)")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        results.append(f"wrote {path} ({len(body)} bytes)")
    return results


# The two surfaces whose "settings" are committed files rather than anything in
# a home directory. They were the gap: both files existed and neither carried the
# block, so Copilot on github.com and Gemini Code Assist had no enforcement at
# all while every local client had two layers of it.
REPO_FILE_TARGETS = {
    "copilot-web": (".github/copilot-instructions.md",),
    "gemini-code-assist": (".gemini/styleguide.md",),
}

# The repository's OWN instruction files, which every hook client reads when it
# opens this repo. They carry the same managed block, verify_auto_mode requires
# them to match docs/auto-mode-block.txt, and until this constant existed nothing
# wrote them: the verifier demanded a file no command produced, so the only way
# to pass was to hand-edit three files in step with the source. That drifted the
# first time the block changed.
REPO_INSTRUCTION_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")


def install_repo_instructions(dry: bool) -> list[str]:
    """Refresh the managed block in this repository's own instruction files."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import install_auto_mode as installer  # noqa: E402

    # The project being set up, which is the checkout when there is one and the
    # caller's own directory when this is an installed copy. Writing these into
    # the package directory was the bug: they landed in site-packages, where
    # they instruct nothing and vanish on the next upgrade.
    project = harness_paths.project_dir()
    body = block_text().strip()
    return [f"{installer.upsert_block(project / name, body, dry)} the block in "
            f"{name} ({project})" for name in REPO_INSTRUCTION_FILES]


def install_repo_files(ids: list[str], dry: bool) -> list[str]:
    """Upsert the standing block into the committed instruction files.

    Same marker pair and same in-place replacement the home-directory files use,
    so a refresh never duplicates the block and never disturbs the prose the file
    already carries. That prose is the repository's own style guidance and is not
    ours to rewrite.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import install_auto_mode as installer  # noqa: E402

    results = []
    body = block_text().strip()
    project = harness_paths.project_dir()
    for surface_id in ids:
        for relative in REPO_FILE_TARGETS.get(surface_id, ()):
            path = project / relative
            action = installer.upsert_block(path, body, dry)
            results.append(f"{action} the block in {relative}")
    return results


def install_project_files(dry: bool) -> list[str]:
    """Mirror the skills into the project's shared discovery path.

    WHAT THIS DELIBERATELY DOES NOT DO, and why, because the first version did
    it and it was wrong twice over.

    This repository carries .cursor/hooks.json, .cursor/rules/master-repo-auto.mdc
    and .github/hooks/master-repo-auto.json. They are project-scoped client
    configs and they are committed with RELATIVE paths, `python
    scripts/hooks/no_prune_guard.py`, so they work for anyone who clones this
    repository.

    Writing them into someone else's project makes no sense: there is no
    scripts/hooks/ there for a relative path to reach, and the rule's text
    points at AGENTS.md and docs/auto-mode-block.txt, which that project does
    not have either. Rewriting them with absolute paths instead, which is what
    the first version did, replaced a portable committed config with one naming
    a single machine's Python and home directory, inside a change whose whole
    purpose was working on other machines.

    A project installing from the package gets its enforcement from the
    HOME-scoped hooks, which are already installed and point at the package by
    absolute path because that is where the code actually is.

    The skill mirror is different and is done here: .agents/skills is a shared
    discovery path that any project benefits from, the merge never deletes, and
    a project with its own skills keeps every one of them.
    """
    project = harness_paths.project_dir()
    if dry:
        return [f"would mirror skills into {project / '.agents' / 'skills'}"]
    destinations = sync_project_skills.sync_project_skills(
        project, source=harness_paths.skills_dir())
    return [f"mirrored {len(destinations)} skills into "
            f"{project / '.agents' / 'skills'}"]


def install_surfaces(ids: list[str], dry: bool) -> int:
    """Hand the hook and skill installs to the installer that already does them.

    Not reimplemented here. install_auto_mode.py backs settings up, refuses to
    overwrite a file it cannot parse, and merges rather than replacing, and a
    second implementation of that would be a second set of those decisions to
    get wrong.
    """
    # install_auto_mode writes client config that POINTS AT this repository, so
    # it needs one. An installed wheel has no checkout to point at; saying that
    # plainly beats writing paths into site-packages that break on the next
    # upgrade. The hook command for a standalone install is the console script,
    # which harness_paths already reports and `master-harness-where` prints.
    # Works with or without a checkout. install_auto_mode resolves the hook
    # scripts through harness_paths, so an installed copy registers the hooks
    # bundled beside it and a checkout registers the ones in scripts/hooks.
    # --repo still names the project the client configs describe.
    project = harness_paths.project_dir()
    installer = pathlib.Path(install_auto_mode.__file__).resolve()
    if not installer.is_file():
        print(f"installer missing: {installer}", file=sys.stderr)
        return 1
    # One installer run per selected client. The earlier version built a single
    # command with no --client at all, so the installer fell back to its "all"
    # default and picking one surface quietly installed six. The ids are already
    # validated by the caller, and install_auto_mode rejects an unknown --client
    # itself, so a bad id fails loudly here rather than silently widening.
    print(f"Installing hooks and skills for: {', '.join(ids)}")
    failed = 0
    for surface in ids:
        client = INSTALLER_CLIENTS.get(surface, surface)
        command = [sys.executable, str(installer), "--repo", str(project),
                   "--client", client]
        if dry:
            command.append("--dry-run")
        print(f"  {' '.join(command)}")
        failed |= subprocess.run(command).returncode
    return failed


def check() -> int:
    """Verify without changing what is being verified.

    Rendering the pipeline captures a goal from the fixture prompt, so a check
    run against the real store would leave "Plan and design a small interface."
    standing as this session's objective. It happened once; this is why it
    cannot happen again.
    """
    with skill_pipeline.isolated_store():
        return _check_isolated()


def _check_isolated() -> int:
    """Prove the pipeline is reachable for every mechanism, and say what is not."""
    failures = []

    probe = skill_pipeline.context_for("Plan and design a small interface.")
    required = ("LAYER 1", "LAYER 2", "LAYER 3", "FULL OUTPUT", "ANTI-SLOP", "NEVER COMPACT")
    absent = [item for item in required if item not in probe]
    if absent:
        failures.append("pipeline is missing: " + ", ".join(absent))
    print(f"pipeline           {len(probe)} bytes, all three layers"
          if not absent else "pipeline           INCOMPLETE")

    gone = missing_skills()
    if gone:
        failures.append("enforced skills missing: " + ", ".join(gone))
    print(f"enforced skills    {len(ENFORCED_SKILLS) - len(gone)} of {len(ENFORCED_SKILLS)} present")

    # Every client output shape, exercised rather than asserted. A shape that
    # stopped parsing is a client that silently stopped being enforced.
    shapes = {
        "claude-code": ([], {"prompt": "check"}),
        "antigravity": (["--antigravity"], {"prompt": "check"}),
        "gemini-cli": (["--gemini"], {"prompt": "check"}),
        "cursor": (["--cursor"], {"session_id": "x"}),
        "copilot-cli": (["--copilot-session"], {"initialPrompt": "check"}),
        "copilot-cli transform": (["--copilot-transform"],
                                  {"prompt": "check", "transformedPrompt": "check"}),
    }
    # The hook file itself, wherever it is. In a checkout that is
    # scripts/hooks/; in a wheel it sits beside this module. Resolved from the
    # imported module rather than assumed, so the shapes below are exercised
    # against the file that will actually run.
    hook = pathlib.Path(skill_pipeline.__file__).resolve()
    for label, (flags, event) in shapes.items():
        proc = subprocess.run([sys.executable, str(hook), *flags],
                              input=json.dumps(event).encode(), capture_output=True)
        out = proc.stdout.decode("utf-8", "replace").strip()
        ok = proc.returncode == 0 and (not out or out == "{}" or _carries_rules(out))
        if not ok:
            failures.append(f"{label} produced no usable output")
        print(f"{label:<22}{'ok' if ok else 'FAILED'}")

    for surface_id in SURFACES:
        try:
            build_bundle(surface_id)
        except (FileNotFoundError, OSError) as exc:
            failures.append(f"bundle for {surface_id}: {exc}")
    print(f"bundles            {len(SURFACES)} surfaces build")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("\nauto mode is reachable on every surface listed by --list")
    return 0


def _carries_rules(output: str) -> bool:
    try:
        data = json.loads(output)
    except ValueError:
        return False
    return "LAYER 1" in json.dumps(data)


def show_list() -> int:
    for group, title in GROUPS.items():
        rows = [(i, s) for i, s in SURFACES.items() if s["group"] == group]
        print(f"\n{title}")
        for surface_id, surface in rows:
            print(f"  {surface_id:<20} {surface['mechanism']:<10} {surface['name']}")
            print(f"  {'':<20} {'':<10} {surface['target']}")
    print()
    return 0


def resolve(selection: str, mechanisms: tuple[str, ...] | None = None) -> list[str]:
    if selection.strip().lower() == "all":
        ids = list(SURFACES)
    else:
        ids = [part.strip() for part in selection.split(",") if part.strip()]
        unknown = [i for i in ids if i not in SURFACES]
        if unknown:
            raise SystemExit(f"unknown surface(s): {', '.join(unknown)}. "
                             f"Run --list to see the names.")
    if mechanisms:
        ids = [i for i in ids if SURFACES[i]["mechanism"] in mechanisms]
    return ids


def request_payload(model: str, prompt: str) -> dict:
    """Build the exact non-streaming Ollama chat request."""
    return {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": skill_pipeline.context_for(prompt)},
            {"role": "user", "content": prompt},
        ],
    }


def send(host: str, payload: dict, timeout: int) -> str:
    endpoint = host.rstrip("/") + "/api/chat"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    message = result.get("message") or {}
    content = message.get("content")
    if not isinstance(content, str):
        raise ValueError("Ollama response has no message.content string")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Put Master Repo auto mode on every surface it can reach.")
    parser.add_argument("--list", action="store_true",
                        help="show every surface and the mechanism it supports")
    parser.add_argument("--check", action="store_true",
                        help="verify the pipeline, the enforced skills and every client output shape")
    parser.add_argument("--install", metavar="SURFACES",
                        help="'all' or a comma separated list; installs hooks and skill folders")
    parser.add_argument("--bundle", metavar="SURFACES",
                        help="'all' or a comma separated list; writes the paste file for surfaces with no hook")
    parser.add_argument("--out", default="dist/auto-mode",
                        help="directory for --bundle output (default dist/auto-mode)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would happen and change nothing")
    parser.add_argument("--model", help="Exact installed Ollama tag, for example qwen3:4b")
    parser.add_argument("--prompt", help="Prompt text. If omitted, read it from standard input.")
    parser.add_argument("--host", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--show-request", action="store_true",
                        help="print the JSON request and do not contact Ollama")
    args = parser.parse_args()

    if args.list:
        return show_list()

    if args.check:
        return check()

    if args.install:
        hooked = resolve(args.install, mechanisms=(HOOK,))
        committed = resolve(args.install, mechanisms=(REPO_FILE,))
        if not hooked and not committed:
            print("nothing to install: those surfaces take neither a hook nor a "
                  "committed instruction file. Use --bundle for them.", file=sys.stderr)
            return 1
        status = 0
        if hooked:
            status = install_surfaces(hooked, args.dry_run)
        for line in install_repo_files(committed, args.dry_run):
            print(line)
        for line in install_repo_instructions(args.dry_run):
            print(line)
        for line in install_project_files(args.dry_run):
            print(line)
        return status

    if args.bundle:
        gone = missing_skills()
        if gone:
            print("refusing to build a bundle with skills missing: " + ", ".join(gone),
                  file=sys.stderr)
            return 1
        ids = resolve(args.bundle, mechanisms=(BUNDLE, REPO_FILE))
        if not ids:
            print("nothing to bundle: those surfaces take a hook instead. "
                  "Use --install for them.", file=sys.stderr)
            return 1
        for line in write_bundles(ids, pathlib.Path(args.out), args.dry_run):
            print(line)
        return 0

    if not args.model:
        parser.error("give --list, --check, --install, --bundle, or --model")
    prompt = args.prompt if args.prompt is not None else sys.stdin.read()
    if not prompt.strip():
        parser.error("provide --prompt or pipe prompt text on standard input")
    payload = request_payload(args.model, prompt)
    if args.show_request:
        print(json.dumps(payload, indent=2))
        return 0
    try:
        print(send(args.host, payload, args.timeout))
    except urllib.error.URLError as error:
        print(f"Ollama request failed at {args.host}: {error.reason}", file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError) as error:
        print(f"Ollama returned an invalid response: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
