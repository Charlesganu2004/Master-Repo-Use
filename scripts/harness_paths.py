#!/usr/bin/env python3
"""Where the harness reads its skills, its block and its state.

One module, because the answer differs between two ways of running and every
harness needs it:

  REPO MODE       a checkout of Master-Repo-Use. skills/ and
                  docs/auto-mode-block.txt sit at the root, and the goal state
                  goes in .auto-mode/ beside them.

  INSTALLED MODE  a wheel installed with pip or pipx, no checkout anywhere. The
                  skills and the block travel inside the package as _skills/ and
                  _data/. State goes to a per-user directory, because
                  site-packages is not writable on a normal install and a
                  harness that cannot record a goal is not carrying one.

Every harness asks this module and gets a path. That is the point: each one
resolving its own paths is the same rule written seven times, and the same rule
written twice is the drift this repository keeps paying for.

WHY IT LIVES IN scripts/ RATHER THAN IN THE PACKAGE. It has to be importable by
the harness modules in both modes, and in a checkout they import each other by
bare name off scripts/. Putting the logic in master_harness/resources.py and
importing it from here would work in a wheel and fail in a checkout, which is
the half that is exercised every day. So the logic is here, and resources.py is
a thin re-export of it for anything importing the package directly.

The mode is DETECTED, not configured. A checkout is identifiable by what it
contains. Asking for an environment variable to say where we are would be a
question whose answer is already on disk. MASTER_REPO_PATH exists anyway, for
the case where someone has a checkout somewhere unusual and wants it used.
"""
from __future__ import annotations

import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

ENV_REPO = "MASTER_REPO_PATH"
ENV_STATE = "MASTER_REPO_GOAL_DIR"

# When this file has been staged into the package by setup.py it sits beside the
# bundled payload rather than in scripts/.
BUNDLED_SKILLS = HERE / "_skills"
BUNDLED_DATA = HERE / "_data"


def _is_repo(candidate: pathlib.Path) -> bool:
    """A checkout, rather than a directory that happens to be named right."""
    return ((candidate / "skills" / "master-repo-auto" / "SKILL.md").is_file()
            and (candidate / "docs" / "auto-mode-block.txt").is_file())


def repo_root() -> pathlib.Path | None:
    """The checkout this is running from, or None when installed standalone."""
    override = os.environ.get(ENV_REPO)
    if override:
        candidate = pathlib.Path(override).expanduser()
        return candidate if _is_repo(candidate) else None
    for parent in (HERE, *HERE.parents):
        if _is_repo(parent):
            return parent
    return None


def installed_standalone() -> bool:
    return repo_root() is None


def skills_dir() -> pathlib.Path:
    root = repo_root()
    return (root / "skills") if root else BUNDLED_SKILLS


def skill_path(name: str) -> pathlib.Path:
    return skills_dir() / name / "SKILL.md"


def skill_names() -> list[str]:
    directory = skills_dir()
    if not directory.is_dir():
        return []
    return sorted(path.name for path in directory.iterdir()
                  if (path / "SKILL.md").is_file())


def agents_dir() -> pathlib.Path:
    """The agent roster the computer router names.

    Bundled with the wheel rather than skipped when installed. The router
    reports which agents are available to run a route; an install that names
    four agents whose files do not exist is claiming a capability it cannot
    show, which is worse than admitting it has none.
    """
    root = repo_root()
    return (root / "agents") if root else (HERE / "_agents")


def agent_path(relative: str) -> pathlib.Path:
    """Resolve a roster entry like 'agents/ui-canvas.md' in either mode."""
    name = pathlib.PurePosixPath(relative).name
    root = repo_root()
    return (root / relative) if root else (agents_dir() / name)


def hooks_dir() -> pathlib.Path:
    """Where the hook scripts live: the pipeline and the two guards.

    In a checkout, scripts/hooks/. Installed, beside this module, because a
    wheel is flat. Client configs get an absolute path to whichever it is, and
    both are real files a client can execute.
    """
    root = repo_root()
    return (root / "scripts" / "hooks") if root else HERE


def project_dir() -> pathlib.Path:
    """Where a project-level instruction file belongs.

    The checkout when running from one. Installed, the CALLER's directory, which
    is the project they are setting up: that is the whole point of installing
    this without the repository. It must never be the package directory, and it
    was: a standalone `--install all` wrote .github/copilot-instructions.md into
    site-packages, where it instructs nothing and is deleted on the next
    upgrade. Nothing errored.
    """
    root = repo_root()
    return root if root is not None else pathlib.Path.cwd()


def block_path() -> pathlib.Path:
    root = repo_root()
    return (root / "docs" / "auto-mode-block.txt") if root else BUNDLED_DATA / "auto-mode-block.txt"


def state_dir() -> pathlib.Path:
    """Where the standing goal is written.

    In a checkout, .auto-mode/ beside the repo, which is gitignored. Installed,
    a per-user data directory: there is no repo to sit beside, and writing into
    site-packages fails on any normal install and silently drops the goal.
    """
    override = os.environ.get(ENV_STATE)
    if override:
        return pathlib.Path(override).expanduser()
    root = repo_root()
    if root is not None:
        return root / ".auto-mode"
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or (pathlib.Path.home() / "AppData" / "Local")
    else:
        base = os.environ.get("XDG_DATA_HOME") or (pathlib.Path.home() / ".local" / "share")
    return pathlib.Path(base) / "master-harness"


def seed_path() -> pathlib.Path | None:
    """The committed goal, read only when no runtime state exists yet.

    None when installed: a wheel has no committed goal to inherit, and inventing
    one from whatever the author last set would be someone else's objective
    riding a stranger's prompts.
    """
    root = repo_root()
    return (root / "docs" / "auto-mode-goal.json") if root else None


def block_header(project: pathlib.Path | None = None) -> str:
    """The first line of an installed block: where these rules came from.

    In a checkout that is the repository. Installed it is the package, because
    naming a Master Repo path that does not exist on the machine sends the
    reader looking for a directory nobody has.

    Defined here because the installer WRITES it and the verifier COMPARES it,
    and the same string in two files is the drift that had five clients
    reporting a mismatch against a block that was correct.
    """
    root = repo_root()
    if root is not None:
        return f"Master Repo path: {project if project is not None else root}"
    return f"Master harness package: {HERE}"


def harness_modules_dir() -> pathlib.Path:
    """Where the harness command modules live.

    scripts/ in a checkout, the package directory when installed. The verifier
    checks they are present, and looking only under scripts/ reported four
    missing harnesses on an install that had all of them.
    """
    root = repo_root()
    return (root / "scripts") if root else HERE


def hook_command() -> list[str]:
    """What a client config should run for the per-prompt hook.

    A checkout registers the script by path, which is what every existing
    installation already has written into it. Installed, there is no path worth
    writing down, so it registers the console script pip put on PATH.
    """
    root = repo_root()
    if root is not None:
        return ["python", str(root / "scripts" / "hooks" / "skill_pipeline.py")]
    return ["master-harness-hook"]


def harness_command(module: str) -> list[str]:
    """How to invoke another harness as a subprocess, in either mode.

    By FILE PATH, not by console-script name. The console scripts exist and are
    the interface a person types, but they are a poor thing for one process to
    spawn: on Windows the entry point is master-harness-wrap.exe and a bare name
    without the suffix raises WinError 2, and on any platform it depends on PATH
    being set the way the installer left it. The module file is beside this one
    when installed and under scripts/ in a checkout, and both are exact.
    """
    import sys
    root = repo_root()
    if root is not None:
        return [sys.executable, str(root / "scripts" / f"{module}.py")]
    bundled = HERE / f"{module}.py"
    if bundled.is_file():
        return [sys.executable, str(bundled)]
    return [sys.executable, "-c",
            f"import sys,{module};sys.exit({module}.main())"]


def work_dir() -> pathlib.Path:
    """Where a spawned harness should run.

    The checkout when there is one, so relative paths in a command resolve the
    way the person typing them expects. Installed, the caller's own directory:
    running them inside site-packages would resolve a relative path against a
    library directory, which is never what was meant.
    """
    root = repo_root()
    return root if root is not None else pathlib.Path.cwd()


def describe() -> dict:
    root = repo_root()
    return {
        "mode": "repo" if root else "installed",
        "repo": str(root) if root else None,
        "skills": str(skills_dir()),
        "skillCount": len(skill_names()),
        "block": str(block_path()),
        "blockPresent": block_path().is_file(),
        "state": str(state_dir()),
        "hookCommand": " ".join(hook_command()),
    }


if __name__ == "__main__":
    for key, value in describe().items():
        print(f"{key:<14}{value}")
