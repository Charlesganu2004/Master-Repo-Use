#!/usr/bin/env python3
"""Build hook: copy the harness into the package before the wheel is written.

The metadata is in pyproject.toml. This file exists for one job, and the job is
the reason the package works at all.

THE PROBLEM. The harness modules live in scripts/ and the skills live in
skills/, both at the repository root, because that is where every hook, doc,
test and already-installed client config points at them. A wheel cannot
reference files outside its package directory, so a naive build produces a
package that imports nothing and enforces nothing, and it does that quietly:
`pip install` succeeds, the commands appear on PATH, and every one of them fails
the first time it is run on a machine with no checkout.

THE OPTION NOT TAKEN. Committing a second copy of each module and each SKILL.md
inside master_harness/ would also work, and it is what this nearly became. It
was rejected for the reason this repository has a whole module about: the same
content in two files is fixed in one of them. That is how a dotted-key bug got
found once and fixed twice, and how a page said ten rules while the hook
injected eleven.

SO: one copy in the repository, copied in at BUILD time. `pip install .` and
`pip install git+https://...` both run this, so both produce a complete wheel.
An editable install and a plain checkout skip it entirely and read the repo
directly, which is what resources.py resolves.

Verified after every build by tests/test_package.py, which builds a wheel,
installs it into a throwaway environment with no repository in sight, and runs
the commands.
"""
from __future__ import annotations

import pathlib
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py

ROOT = pathlib.Path(__file__).resolve().parent
PACKAGE = ROOT / "master_harness"

# The modules that make up the harness, in the repository, with where each one
# lives. Named explicitly rather than globbed: scripts/ holds forty files and
# most of them are catalog tooling that has no business in this wheel.
HARNESS_MODULES = {
    # First, because every other module imports it to find its data.
    "harness_paths.py": ROOT / "scripts" / "harness_paths.py",
    "skill_pipeline.py": ROOT / "scripts" / "hooks" / "skill_pipeline.py",
    # The two guards. Registered alongside the pipeline by every client, and a
    # client config that points at a guard which is not there is a protection
    # that silently never runs.
    "no_prune_guard.py": ROOT / "scripts" / "hooks" / "no_prune_guard.py",
    "no_compress_guard.py": ROOT / "scripts" / "hooks" / "no_compress_guard.py",
    "auto_mode_harness.py": ROOT / "scripts" / "auto_mode_harness.py",
    "harness_proxy.py": ROOT / "scripts" / "harness_proxy.py",
    "harness_wrap.py": ROOT / "scripts" / "harness_wrap.py",
    "harness_goal.py": ROOT / "scripts" / "harness_goal.py",
    "harness_computer.py": ROOT / "scripts" / "harness_computer.py",
    "harness_super.py": ROOT / "scripts" / "harness_super.py",
    # auto_mode_harness calls this one to write client configs.
    "install_auto_mode.py": ROOT / "scripts" / "install_auto_mode.py",
    # An install nobody can check is an install nobody should trust. This is the
    # same verifier the repository runs, resolving through harness_paths so it
    # recognises a pip install as readily as a checkout.
    "verify_auto_mode.py": ROOT / "scripts" / "verify_auto_mode.py",
    # harness_computer reads the agent roster through it.
    "capability_definitions.py": ROOT / "scripts" / "capability_definitions.py",
    "sync_project_skills.py": ROOT / "scripts" / "sync_project_skills.py",
}

DATA_FILES = {
    "auto-mode-block.txt": ROOT / "docs" / "auto-mode-block.txt",
}


def stage_payload() -> list[str]:
    """Copy the modules, the skills and the block into the package.

    Returns what it staged so the build log says it rather than leaving the
    author to trust that a silent step happened.
    """
    staged = []

    for name, source in HARNESS_MODULES.items():
        if not source.is_file():
            raise SystemExit(f"cannot build: {source} is missing")
        shutil.copy2(source, PACKAGE / name)
        staged.append(name)

    data_dir = PACKAGE / "_data"
    data_dir.mkdir(exist_ok=True)
    for name, source in DATA_FILES.items():
        if not source.is_file():
            raise SystemExit(f"cannot build: {source} is missing")
        shutil.copy2(source, data_dir / name)
        staged.append(f"_data/{name}")

    # The agent roster. The computer router reports which agents can run a
    # route, and an install that names four whose files are absent is claiming a
    # capability it cannot show.
    agents_source = ROOT / "agents"
    agents_target = PACKAGE / "_agents"
    if agents_target.exists():
        shutil.rmtree(agents_target)
    agents_target.mkdir()
    agent_count = 0
    for agent in sorted(agents_source.glob("*.md")):
        shutil.copy2(agent, agents_target / agent.name)
        agent_count += 1
    staged.append(f"_agents/ ({agent_count} agents)")

    skills_source = ROOT / "skills"
    skills_target = PACKAGE / "_skills"
    if skills_target.exists():
        shutil.rmtree(skills_target)
    count = 0
    for skill in sorted(skills_source.iterdir()):
        if not (skill / "SKILL.md").is_file():
            continue
        shutil.copytree(skill, skills_target / skill.name)
        count += 1
    if count == 0:
        raise SystemExit("cannot build: no skills found to bundle")
    staged.append(f"_skills/ ({count} skills)")

    return staged


class BuildWithHarness(build_py):
    def run(self):
        for line in stage_payload():
            self.announce(f"staged {line}", level=2)
        super().run()


setup(cmdclass={"build_py": BuildWithHarness})
