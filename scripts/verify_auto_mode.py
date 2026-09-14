#!/usr/bin/env python3
"""Read-only verification of Master Repo auto-mode installation.

The installer reports what it tried to write. This command reads the resulting
files back and checks the managed instruction blocks, copied skill resources,
and native hook schemas against the selected repository. It never registers a
hook, refreshes a skill, creates a backup, or changes trust state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Where the skills, the block and the hook scripts actually are. A checkout
# keeps them under the repository; a pip install keeps them in the package.
# Both are complete installs and both must verify.
import harness_paths  # noqa: E402
from install_auto_mode import accepted_legacy_representation  # noqa: E402


BEGIN = "<!-- MASTER-REPO-USE:BEGIN -->"
END = "<!-- MASTER-REPO-USE:END -->"
NO_COMPRESS_BEGIN = "<!-- NO-COMPRESS:BEGIN -->"
NO_COMPRESS_END = "<!-- NO-COMPRESS:END -->"

CLIENT_ORDER = ("claude", "codex", "gemini", "antigravity", "cursor", "copilot")
CLIENT_ALIASES = {
    "all": "all",
    "claude": "claude",
    "claude-code": "claude",
    "codex": "codex",
    "gpt": "codex",
    "chatgpt": "codex",
    "openai": "codex",
    "gemini": "gemini",
    "gemini-cli": "gemini",
    "antigravity": "antigravity",
    "ag": "antigravity",
    "google-antigravity": "antigravity",
    "cursor": "cursor",
    "copilot": "copilot",
    "copilot-cli": "copilot",
}

HOME_INSTRUCTIONS = {
    "claude": ".claude/CLAUDE.md",
    "codex": ".codex/AGENTS.md",
    "gemini": ".gemini/GEMINI.md",
    "antigravity": ".gemini/GEMINI.md",
    "copilot": ".copilot/copilot-instructions.md",
}

HOME_SKILLS = {
    "claude": (".claude/skills",),
    "codex": (".codex/skills", ".agents/skills"),
    "gemini": (".gemini/skills",),
    "antigravity": (".gemini/config/skills",),
    "cursor": (".cursor/skills",),
    "copilot": (".copilot/skills",),
}

PRIMARY_ARTIFACTS = {
    "claude": (".claude/CLAUDE.md", ".claude/settings.json", ".claude/skills"),
    "codex": (".codex/AGENTS.md", ".codex/hooks.json", ".codex/skills"),
    "gemini": (".gemini/settings.json", ".gemini/skills"),
    "antigravity": (".gemini/config/hooks.json", ".gemini/config/skills"),
    "cursor": (".cursor/rules/master-repo-auto.mdc", ".cursor/hooks.json",
               ".cursor/skills"),
    "copilot": (".copilot/copilot-instructions.md",
                ".copilot/hooks/master-repo-auto.json", ".copilot/skills"),
}

HOOK_FILES = ("skill_pipeline.py", "no_prune_guard.py", "no_compress_guard.py")
REQUIRED_SKILLS = (
    "master-repo-auto",
    "master-caveman",
    "master-token-reducer",
    "master-full-output",
    "master-anti-slop",
    "master-plan",
    "master-design-taste",
    "master-goal",
)


@dataclass(frozen=True)
class Check:
    status: str
    scope: str
    label: str
    detail: str


class Verifier:
    def __init__(self, repo: pathlib.Path, home: pathlib.Path,
                 clients: tuple[str, ...], installed_only: bool = False):
        self.repo = repo.expanduser().resolve()
        self.home = home.expanduser().resolve()
        self.clients = clients
        self.installed_only = installed_only
        self.results: list[Check] = []
        self.block = ""
        self.skills: tuple[pathlib.Path, ...] = ()

    def add(self, status: str, scope: str, label: str, detail: str) -> None:
        self.results.append(Check(status, scope, label, detail))

    def passed(self, scope: str, label: str, detail: str) -> None:
        self.add("PASS", scope, label, detail)

    def failed(self, scope: str, label: str, detail: str) -> None:
        self.add("FAIL", scope, label, detail)

    def warned(self, scope: str, label: str, detail: str) -> None:
        self.add("WARN", scope, label, detail)

    def skipped(self, scope: str, label: str, detail: str) -> None:
        self.add("SKIP", scope, label, detail)

    @staticmethod
    def _rel(root: pathlib.Path, relative: str) -> pathlib.Path:
        return root / pathlib.PurePosixPath(relative)

    @staticmethod
    def _compact(names: list[str]) -> str:
        if len(names) <= 5:
            return ", ".join(names)
        return ", ".join(names[:5]) + f", plus {len(names) - 5} more"

    def _read_text(self, path: pathlib.Path, scope: str,
                   label: str) -> str | None:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.failed(scope, label, f"missing {path}")
        except (OSError, UnicodeError) as exc:
            self.failed(scope, label, f"cannot read {path}: {exc}")
        return None

    def _read_json(self, path: pathlib.Path, scope: str,
                   label: str) -> dict | None:
        text = self._read_text(path, scope, label)
        if text is None:
            return None
        try:
            payload = json.loads(text)
        except ValueError as exc:
            self.failed(scope, label, f"invalid JSON in {path}: {exc}")
            return None
        if not isinstance(payload, dict):
            self.failed(scope, label, f"JSON root is not an object in {path}")
            return None
        return payload

    @staticmethod
    def _managed_block(text: str) -> str | None:
        if text.count(BEGIN) != 1 or text.count(END) != 1:
            return None
        start = text.index(BEGIN)
        stop = text.index(END, start) + len(END)
        return text[start:stop]

    def _expected_repo_block(self) -> str:
        return f"{BEGIN}\n{self.block.strip()}\n{END}"

    def _expected_home_block(self) -> str:
        # The header comes from harness_paths, which is also what wrote it.
        body = f"{harness_paths.block_header(self.repo)}\n{self.block.strip()}"
        return f"{BEGIN}\n{body}\n{END}"

    def _check_instruction(self, path: pathlib.Path, scope: str,
                           label: str, home_copy: bool) -> None:
        text = self._read_text(path, scope, label)
        if text is None:
            return
        actual = self._managed_block(text)
        if actual is None:
            self.failed(scope, label, f"managed markers are missing or duplicated in {path}")
            return
        expected = self._expected_home_block() if home_copy else self._expected_repo_block()
        if actual != expected:
            self.failed(scope, label, f"managed block does not match docs/auto-mode-block.txt in {path}")
            return
        self.passed(scope, label, f"exact managed block in {path}")

    def _canonical_skills(self) -> tuple[pathlib.Path, ...]:
        source = harness_paths.skills_dir()
        if not source.is_dir():
            self.failed("repo", "canonical skills", f"missing {source}")
            return ()
        skills = tuple(sorted(
            (path for path in source.iterdir()
             if path.is_dir() and (path / "SKILL.md").is_file()),
            key=lambda path: path.name.casefold(),
        ))
        if not skills:
            self.failed("repo", "canonical skills", f"no SKILL.md directories under {source}")
            return ()
        missing_required = [name for name in REQUIRED_SKILLS
                            if not (source / name / "SKILL.md").is_file()]
        if missing_required:
            self.failed("repo", "required skills",
                        "missing " + self._compact(missing_required))
        else:
            self.passed("repo", "required skills",
                        f"{len(REQUIRED_SKILLS)} standing-pipeline skills present")
        self.passed("repo", "canonical skills", f"{len(skills)} discoverable skills")
        return skills

    def _check_skill_tree(self, destination_root: pathlib.Path,
                          scope: str, label: str) -> None:
        if not destination_root.is_dir():
            self.failed(scope, label, f"missing {destination_root}")
            return
        missing: list[str] = []
        changed: list[str] = []
        legacy: list[str] = []
        known = {}
        try:
            root = destination_root.relative_to(self.home).as_posix()
            manifest = self.home / ".master-repo-auto" / (
                "skills-" + hashlib.sha256(root.encode()).hexdigest() + ".json")
            if manifest.is_file():
                known = json.loads(manifest.read_text(encoding="utf-8"))
                if not isinstance(known, dict):
                    self.failed(scope, label, "installed skill manifest must be an object")
                    return
        except ValueError:
            if destination_root.is_relative_to(self.home):
                self.failed(scope, label, "installed skill manifest is invalid")
                return
        except OSError:
            self.failed(scope, label, "installed skill manifest is unreadable")
            return
        files = 0
        for skill in self.skills:
            for source in skill.rglob("*"):
                if not source.is_file() or "__pycache__" in source.parts:
                    continue
                files += 1
                relative = source.relative_to(harness_paths.skills_dir())
                destination = destination_root / relative
                if not destination.is_file():
                    missing.append(relative.as_posix())
                    continue
                try:
                    if source.read_bytes() != destination.read_bytes():
                        if accepted_legacy_representation(source, destination,
                                                          known.get(relative.as_posix())):
                            legacy.append(relative.as_posix())
                        else:
                            changed.append(relative.as_posix())
                except OSError as exc:
                    changed.append(f"{relative.as_posix()} ({exc})")
        if missing or changed:
            details = []
            if missing:
                details.append("missing " + self._compact(missing))
            if changed:
                details.append("different " + self._compact(changed))
            self.failed(scope, label, "; ".join(details))
            return
        if legacy:
            self.warned(scope, label, "accepted legacy line-ending representation: " +
                        self._compact(legacy) + "; all other source files match exactly")
            return
        self.passed(scope, label, f"{len(self.skills)} skills and {files} source files match")

    def _check_repo_source(self) -> None:
        if not self.repo.is_dir():
            self.failed("repo", "repository", f"missing {self.repo}")
            return
        block_path = harness_paths.block_path()
        block = self._read_text(block_path, "repo", "canonical block")
        if block is not None:
            if (block.count(NO_COMPRESS_BEGIN) != 1 or
                    block.count(NO_COMPRESS_END) != 1):
                self.failed("repo", "canonical block",
                            "protected markers are missing or duplicated")
            else:
                self.block = block
                self.passed("repo", "canonical block",
                            f"protected source present at {block_path}")

        hook_root = harness_paths.hooks_dir()
        missing_hooks = [name for name in HOOK_FILES
                         if not (hook_root / name).is_file()]
        if missing_hooks:
            self.failed("repo", "hook sources", "missing " + self._compact(missing_hooks))
        else:
            self.passed("repo", "hook sources", f"{len(HOOK_FILES)} hook scripts present")

        self.skills = self._canonical_skills()
        if self.skills:
            self._check_skill_tree(self.repo / ".agents" / "skills",
                                   "repo", "project skill mirror")

        harnesses = [name for name in ("auto_mode_harness.py", "harness_proxy.py",
                                       "harness_wrap.py", "harness_goal.py")
                     if not (harness_paths.harness_modules_dir() / name).is_file()]
        if harnesses:
            self.failed("repo", "local harnesses", "missing " + self._compact(harnesses))
        else:
            self.passed("repo", "local harnesses",
                        f"harness entrypoints present in {harness_paths.harness_modules_dir()}")

    def _target_is_the_master_repo(self) -> bool:
        """Whether --repo names a Master-Repo checkout rather than any project.

        The project-scoped Cursor rule and the two project hook files are
        COMMITTED CONTENT of this repository, carrying relative paths into
        scripts/hooks/. They are not written by any installer and they mean
        nothing in a project that has no scripts/hooks/ to point at. Demanding
        them of an arbitrary project reported seven failures against an install
        that was complete and correct for that project.
        """
        return (self.repo / "scripts" / "hooks" / "skill_pipeline.py").is_file()

    def _installed(self, client: str) -> bool:
        return any(self._rel(self.home, relative).exists()
                   for relative in PRIMARY_ARTIFACTS[client])

    @staticmethod
    def _command_text(entry: dict) -> str:
        values = [entry.get(key, "") for key in
                  ("command", "commandWindows", "bash", "powershell", "exec")]
        args = entry.get("args", [])
        if isinstance(args, list):
            values.extend(args)
        return " ".join(str(value) for value in values)

    @staticmethod
    def _normalise_command(value: str) -> str:
        return value.replace("\\", "/").casefold()

    def _matches_script(self, entry: dict, script: str,
                        absolute: bool, flag: str | None = None) -> bool:
        command = self._normalise_command(self._command_text(entry))
        # An absolute registration is matched against the resolved hook
        # directory, which is scripts/hooks in a checkout and the package
        # directory in a pip install. The relative form only exists for a
        # checkout, where a client config may store a repo-relative path.
        expected = (harness_paths.hooks_dir() / script) if absolute else (
            pathlib.Path("scripts") / "hooks" / script)
        if self._normalise_command(str(expected)) not in command:
            return False
        return flag is None or flag.casefold() in command

    def _flat_events(self, data: dict, event: str, scope: str,
                     label: str) -> list[dict] | None:
        hooks = data.get("hooks")
        if not isinstance(hooks, dict):
            self.failed(scope, label, "hooks is not an object")
            return None
        entries = hooks.get(event)
        if not isinstance(entries, list) or any(not isinstance(item, dict) for item in entries):
            self.failed(scope, label, f"hooks.{event} is not an array of objects")
            return None
        return entries

    def _nested_events(self, data: dict, event: str, scope: str,
                       label: str) -> list[tuple[dict, dict]] | None:
        entries = self._flat_events(data, event, scope, label)
        if entries is None:
            return None
        handlers: list[tuple[dict, dict]] = []
        for entry in entries:
            nested = entry.get("hooks")
            if not isinstance(nested, list) or any(not isinstance(item, dict) for item in nested):
                self.failed(scope, label, f"hooks.{event} has invalid nested handlers")
                return None
            handlers.extend((entry, handler) for handler in nested)
        return handlers

    def _require_flat_hook(self, entries: list[dict], scope: str, label: str,
                           script: str, absolute: bool = True,
                           flag: str | None = None, matcher: str | None = None,
                           both_shells: bool = False) -> None:
        matches = [entry for entry in entries
                   if self._matches_script(entry, script, absolute, flag)]
        if len(matches) != 1:
            self.failed(scope, label,
                        f"expected one {script} entry, found {len(matches)}")
            return
        entry = matches[0]
        problems = []
        if entry.get("type", "command") != "command":
            problems.append("type is not command")
        if matcher is not None and entry.get("matcher") != matcher:
            problems.append(f"matcher is not {matcher}")
        if both_shells:
            for shell in ("bash", "powershell"):
                command = entry.get(shell)
                if not isinstance(command, str) or not command.strip():
                    problems.append(f"{shell} command is missing")
                elif not self._matches_script({shell: command}, script, absolute, flag):
                    problems.append(f"{shell} command points elsewhere")
        if problems:
            self.failed(scope, label, "; ".join(problems))
        else:
            self.passed(scope, label, f"{script} registered in the expected event")

    def _require_nested_hook(self, handlers: list[tuple[dict, dict]],
                             scope: str, label: str, script: str,
                             flag: str | None = None,
                             matcher: str | None = None) -> dict | None:
        matches = [(outer, handler) for outer, handler in handlers
                   if self._matches_script(handler, script, True, flag)]
        if len(matches) != 1:
            self.failed(scope, label,
                        f"expected one {script} handler, found {len(matches)}")
            return None
        outer, handler = matches[0]
        problems = []
        if handler.get("type") != "command":
            problems.append("type is not command")
        if matcher is None:
            if outer.get("matcher") not in (None, ""):
                problems.append("unexpected matcher")
        elif outer.get("matcher") != matcher:
            problems.append(f"matcher is not {matcher}")
        if problems:
            self.failed(scope, label, "; ".join(problems))
            return None
        self.passed(scope, label, f"{script} registered in the expected event")
        return handler

    def _check_claude_hooks(self, path: pathlib.Path) -> None:
        scope = "claude"
        data = self._read_json(path, scope, "hooks")
        if data is None:
            return
        prompt = self._nested_events(data, "UserPromptSubmit", scope, "prompt hook")
        tools = self._nested_events(data, "PreToolUse", scope, "tool hooks")
        if prompt is not None:
            self._require_nested_hook(prompt, scope, "prompt hook", "skill_pipeline.py")
        if tools is not None:
            for script in HOOK_FILES[1:]:
                self._require_nested_hook(tools, scope, f"guard {script}", script,
                                          matcher="Bash")

    def _check_codex_hooks(self, path: pathlib.Path) -> None:
        scope = "codex"
        data = self._read_json(path, scope, "hooks")
        if data is None:
            return
        prompt = self._nested_events(data, "UserPromptSubmit", scope, "prompt hook")
        tools = self._nested_events(data, "PreToolUse", scope, "tool hooks")
        if prompt is not None:
            handler = self._require_nested_hook(prompt, scope, "prompt hook",
                                                "skill_pipeline.py")
            if handler is not None and handler.get("additionalContextLimit") != 0:
                self.failed(scope, "prompt context", "additionalContextLimit is not 0")
            elif handler is not None:
                self.passed(scope, "prompt context", "additionalContextLimit preserves full output")
        if tools is not None:
            for script in HOOK_FILES[1:]:
                self._require_nested_hook(tools, scope, f"guard {script}", script,
                                          matcher="Bash")
        self.warned(scope, "hook trust",
                    "registration is readable, but Codex hook trust is only visible in its Hooks UI")

    def _check_gemini_hooks(self, path: pathlib.Path) -> None:
        scope = "gemini"
        data = self._read_json(path, scope, "hooks")
        if data is None:
            return
        prompt = self._nested_events(data, "BeforeAgent", scope, "prompt hook")
        tools = self._nested_events(data, "BeforeTool", scope, "tool hooks")
        if prompt is not None:
            self._require_nested_hook(prompt, scope, "prompt hook", "skill_pipeline.py",
                                      flag="--gemini")
        if tools is not None:
            for script in HOOK_FILES[1:]:
                self._require_nested_hook(tools, scope, f"guard {script}", script,
                                          matcher="run_shell_command")

    def _check_antigravity_hooks(self, path: pathlib.Path) -> None:
        scope = "antigravity"
        data = self._read_json(path, scope, "hooks")
        if data is None:
            return
        entry = data.get("master-repo-pipeline")
        if not isinstance(entry, dict):
            self.failed(scope, "prompt hook", "master-repo-pipeline is missing")
            return
        if entry.get("enabled") is not True:
            self.failed(scope, "prompt hook", "master-repo-pipeline is not enabled")
            return
        handlers = entry.get("PreInvocation")
        if not isinstance(handlers, list) or any(not isinstance(item, dict) for item in handlers):
            self.failed(scope, "prompt hook", "PreInvocation is not an array of objects")
            return
        self._require_flat_hook(handlers, scope, "prompt hook", "skill_pipeline.py",
                                flag="--antigravity")

    def _check_cursor_rule(self, path: pathlib.Path, home_copy: bool) -> None:
        scope = "cursor"
        text = self._read_text(path, scope, "always rule")
        if text is None:
            return
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            self.failed(scope, "always rule", "MDC frontmatter is missing")
            return
        frontmatter = text.split("---", 2)[1]
        if not any(line.strip().casefold() == "alwaysapply: true"
                   for line in frontmatter.splitlines()):
            self.failed(scope, "always rule", "alwaysApply: true is missing")
            return
        if home_copy:
            actual = self._managed_block(text)
            if actual != self._expected_home_block():
                self.failed(scope, "always rule",
                            "managed block does not match the selected repository")
                return
        else:
            required = ("@AGENTS.md", "@docs/auto-mode-block.txt")
            if any(item not in text for item in required):
                self.failed(scope, "project rule",
                            "project rule does not load AGENTS.md and docs/auto-mode-block.txt")
                return
        self.passed(scope, "always rule", f"always-applied rule present at {path}")

    def _check_cursor_hooks(self, path: pathlib.Path, project: bool = False) -> None:
        scope = "cursor project" if project else "cursor"
        data = self._read_json(path, scope, "hooks")
        if data is None:
            return
        if data.get("version") != 1:
            self.failed(scope, "hook version", "version is not 1")
        else:
            self.passed(scope, "hook version", "version 1")
        if not project:
            prompt = self._flat_events(data, "sessionStart", scope, "session hook")
            if prompt is not None:
                self._require_flat_hook(prompt, scope, "session hook", "skill_pipeline.py",
                                        flag="--cursor")
        tools = self._flat_events(data, "preToolUse", scope, "tool hooks")
        if tools is not None:
            for script in HOOK_FILES[1:]:
                self._require_flat_hook(tools, scope, f"guard {script}", script,
                                        absolute=not project, matcher="Shell")

    def _check_copilot_hooks(self, path: pathlib.Path, project: bool = False) -> None:
        scope = "copilot project" if project else "copilot"
        data = self._read_json(path, scope, "hooks")
        if data is None:
            return
        if data.get("version") != 1:
            self.failed(scope, "hook version", "version is not 1")
        else:
            self.passed(scope, "hook version", "version 1")
        absolute = not project
        prompt = self._flat_events(data, "userPromptTransformed", scope, "prompt hook")
        session = self._flat_events(data, "sessionStart", scope, "session hook")
        tools = self._flat_events(data, "preToolUse", scope, "tool hooks")
        if prompt is not None:
            self._require_flat_hook(prompt, scope, "prompt hook", "skill_pipeline.py",
                                    absolute=absolute, flag="--copilot-transform",
                                    both_shells=True)
        if session is not None:
            self._require_flat_hook(session, scope, "session hook", "skill_pipeline.py",
                                    absolute=absolute, flag="--copilot-session",
                                    both_shells=True)
        if tools is not None:
            for script in HOOK_FILES[1:]:
                self._require_flat_hook(tools, scope, f"guard {script}", script,
                                        absolute=absolute, matcher="Bash",
                                        both_shells=True)

    def _check_project_client(self, client: str) -> None:
        if not self.block:
            return
        if client == "claude":
            self._check_instruction(self.repo / "CLAUDE.md", "claude project",
                                    "repository instruction", home_copy=False)
        elif client == "codex":
            self._check_instruction(self.repo / "AGENTS.md", "codex project",
                                    "repository instruction", home_copy=False)
        elif client in ("gemini", "antigravity"):
            self._check_instruction(self.repo / "GEMINI.md", "gemini project",
                                    "repository instruction", home_copy=False)
            if client == "gemini":
                self._check_instruction(self.repo / ".gemini" / "styleguide.md",
                                        "gemini code assist", "review instruction",
                                        home_copy=False)
        elif client == "cursor":
            # The project rule and the project hooks are COMMITTED CONTENT of
            # this repository, carrying relative paths into scripts/hooks/.
            # Nothing installs them and they mean nothing in a project that
            # has no scripts/hooks/ to point at, so they are required of a
            # Master-Repo checkout and not of an arbitrary project. Asking
            # for them everywhere reported seven failures against an install
            # that was complete and correct for the project it set up.
            if self._target_is_the_master_repo():
                self._check_cursor_rule(self.repo / ".cursor" / "rules" /
                                        "master-repo-auto.mdc", home_copy=False)
                self._check_cursor_hooks(self.repo / ".cursor" / "hooks.json",
                                         project=True)
        elif client == "copilot":
            self._check_instruction(self.repo / ".github" / "copilot-instructions.md",
                                    "copilot project", "repository instruction",
                                    home_copy=False)
            if self._target_is_the_master_repo():
                self._check_copilot_hooks(self.repo / ".github" / "hooks" /
                                          "master-repo-auto.json", project=True)

    def _check_home_client(self, client: str) -> None:
        if client in HOME_INSTRUCTIONS and self.block:
            self._check_instruction(self._rel(self.home, HOME_INSTRUCTIONS[client]),
                                    client, "global instruction", home_copy=True)
        for relative in HOME_SKILLS[client]:
            self._check_skill_tree(self._rel(self.home, relative), client,
                                   f"skills {relative}")

        if client == "claude":
            self._check_claude_hooks(self._rel(self.home, ".claude/settings.json"))
        elif client == "codex":
            self._check_codex_hooks(self._rel(self.home, ".codex/hooks.json"))
        elif client == "gemini":
            self._check_gemini_hooks(self._rel(self.home, ".gemini/settings.json"))
        elif client == "antigravity":
            self._check_antigravity_hooks(self._rel(self.home,
                                                     ".gemini/config/hooks.json"))
        elif client == "cursor":
            self._check_cursor_rule(self._rel(
                self.home, ".cursor/rules/master-repo-auto.mdc"), home_copy=True)
            self._check_cursor_hooks(self._rel(self.home, ".cursor/hooks.json"))
        elif client == "copilot":
            self._check_copilot_hooks(self._rel(
                self.home, ".copilot/hooks/master-repo-auto.json"))

    def run(self) -> list[Check]:
        self._check_repo_source()
        for client in self.clients:
            self._check_project_client(client)
            if self.installed_only and not self._installed(client):
                self.skipped(client, "home installation",
                             "no client-specific managed artifact found under --home")
                continue
            self._check_home_client(client)
        return self.results


def parse_clients(values: list[str] | None) -> tuple[str, ...]:
    requested = []
    for value in values or ["all"]:
        requested.extend(part.strip().casefold() for part in value.split(",") if part.strip())
    unknown = [name for name in requested if name not in CLIENT_ALIASES]
    if unknown:
        raise ValueError("unknown client(s): " + ", ".join(unknown))
    selected = {CLIENT_ALIASES[name] for name in requested}
    if "all" in selected:
        return CLIENT_ORDER
    return tuple(client for client in CLIENT_ORDER if client in selected)


def print_report(results: list[Check]) -> int:
    for result in results:
        print(f"{result.status:<4} {result.scope:<18} {result.label}: {result.detail}")
    counts = {status: sum(result.status == status for result in results)
              for status in ("PASS", "WARN", "SKIP", "FAIL")}
    print("\n"
          f"Summary: {counts['PASS']} passed, {counts['WARN']} warnings, "
          f"{counts['SKIP']} skipped, {counts['FAIL']} failed")
    print("Note: this verifies files and schemas, not client execution, hosted-account "
          "settings, or hook trust.")
    print("Note: registration is client-scoped, not model-specific. A local wrapper or "
          "proxy only covers requests actually routed through it.")
    return 1 if counts["FAIL"] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo",
        default=str(pathlib.Path(__file__).resolve().parents[1]),
        help="Master Repo source used to validate managed copies",
    )
    parser.add_argument(
        "--home",
        default=str(pathlib.Path.home()),
        help="home directory containing client configuration",
    )
    parser.add_argument(
        "--client",
        action="append",
        help="client name, comma-separated names, or all; may be repeated",
    )
    parser.add_argument(
        "--installed-only",
        action="store_true",
        help="skip home checks for clients with no client-specific managed artifact",
    )
    args = parser.parse_args()
    try:
        clients = parse_clients(args.client)
    except ValueError as exc:
        parser.error(str(exc))
    verifier = Verifier(pathlib.Path(args.repo), pathlib.Path(args.home),
                        clients, installed_only=args.installed_only)
    return print_report(verifier.run())


if __name__ == "__main__":
    raise SystemExit(main())
