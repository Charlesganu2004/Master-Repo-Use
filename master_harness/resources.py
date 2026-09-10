"""Where the harness finds its skills, its block and its state.

A thin re-export. The implementation is scripts/harness_paths.py, which is
copied into this package at build time, because the harness modules import it by
bare name in a checkout and must keep doing so. Two implementations of "where
does this live" is exactly the drift this design exists to avoid, so there is
one, and this module points at it.
"""
from __future__ import annotations

from ._loader import load

_paths = load("harness_paths")

repo_root = _paths.repo_root
installed_standalone = _paths.installed_standalone
skills_dir = _paths.skills_dir
skill_path = _paths.skill_path
skill_names = _paths.skill_names
block_path = _paths.block_path
state_dir = _paths.state_dir
seed_path = _paths.seed_path
hook_command = _paths.hook_command
harness_command = _paths.harness_command
describe = _paths.describe

__all__ = ["repo_root", "installed_standalone", "skills_dir", "skill_path",
           "skill_names", "block_path", "state_dir", "seed_path",
           "hook_command", "harness_command", "describe"]
