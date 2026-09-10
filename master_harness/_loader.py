"""Import a harness module, whichever way this is running.

The harness modules live in scripts/ in the repository, because that is where
every existing hook, doc, test and installed client config points at them. When
this is built into a wheel they are copied in beside this file, so an installed
user gets the same code with no checkout anywhere.

One function resolves both, and it is the only place that knows there are two.
The alternative was a second copy of each module committed inside the package,
which is the duplication that drifts: the same defect fixed twice, in two files,
is what produced catalog_index_spec.py and it is not a lesson worth relearning.

Import order matters and is deliberate. The BUNDLED copy is tried first, so an
installed wheel never depends on finding a checkout, and a machine that happens
to have both gets the one it installed rather than whatever is in a working tree
mid-edit.

THE BOOTSTRAP. harness_paths answers "where does everything live", and this
module has to find harness_paths before it can ask. That is the one question it
cannot delegate, so the search below is small and self-contained: beside this
file first, then up the tree for a checkout. Everything else, including
resources.py, goes through the module it finds.
"""
from __future__ import annotations

import importlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

HARNESSES = {
    "surface": "auto_mode_harness",
    "proxy": "harness_proxy",
    "wrap": "harness_wrap",
    "goal": "harness_goal",
    "computer": "harness_computer",
    "super": "harness_super",
    "pipeline": "skill_pipeline",
    "paths": "harness_paths",
    "verify": "verify_auto_mode",
}

# skill_pipeline lives one directory deeper in the repository, under
# scripts/hooks/, because it is a hook rather than a command.
_REPO_SUBDIR = {"skill_pipeline": ("scripts", "hooks")}

_paths = None


class HarnessNotAvailable(RuntimeError):
    """Raised with something actionable rather than an ImportError traceback."""


def _add_path(directory: pathlib.Path) -> None:
    text = str(directory)
    if text not in sys.path:
        sys.path.insert(0, text)


def paths():
    """harness_paths, found without asking harness_paths where it is."""
    global _paths
    if _paths is not None:
        return _paths

    bundled = HERE / "harness_paths.py"
    if bundled.is_file():
        _add_path(HERE)
        _paths = importlib.import_module("harness_paths")
        return _paths

    for parent in (HERE, *HERE.parents):
        candidate = parent / "scripts" / "harness_paths.py"
        if candidate.is_file():
            _add_path(parent / "scripts")
            _paths = importlib.import_module("harness_paths")
            return _paths

    raise HarnessNotAvailable(
        "harness_paths is neither bundled with this package nor reachable in a "
        "checkout. Reinstall the package, or set MASTER_REPO_PATH to a clone of "
        "Master-Repo-Use.")


def load(module_name: str):
    """Import one harness module by its module name."""
    if module_name in sys.modules:
        return sys.modules[module_name]
    if module_name == "harness_paths":
        return paths()

    bundled = HERE / f"{module_name}.py"
    if bundled.is_file():
        # Installed: the modules sit beside this file and import each other by
        # bare name, exactly as they do in the repository, so the package
        # directory goes on the path rather than being imported as a subpackage.
        _add_path(HERE)
        return importlib.import_module(module_name)

    root = paths().repo_root()
    if root is None:
        raise HarnessNotAvailable(
            f"{module_name} is neither bundled with this package nor reachable in a "
            "checkout. Reinstall the package, or set MASTER_REPO_PATH to a clone of "
            "Master-Repo-Use.")
    _add_path(root / "scripts")
    _add_path(root / "scripts" / "hooks")
    return importlib.import_module(module_name)


def harness(alias: str):
    """Import by the short name the CLI uses."""
    try:
        module_name = HARNESSES[alias]
    except KeyError:
        raise HarnessNotAvailable(
            f"unknown harness {alias!r}; try one of "
            + ", ".join(sorted(HARNESSES))) from None
    return load(module_name)
