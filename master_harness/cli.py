"""Console entry points.

Each one hands argv straight to the harness module it names. They are thin on
purpose: a wrapper that reinterprets flags is a second CLI to keep in step with
the first, and the flags are already documented in each harness's own docstring.

The only entry point with logic of its own is `where`, which answers the
question an installed user asks first and cannot otherwise answer: which skills
is this actually reading, and from where.
"""
from __future__ import annotations

import json
import sys

from . import resources
from ._loader import HarnessNotAvailable, harness


def _run(alias: str) -> int:
    try:
        module = harness(alias)
    except HarnessNotAvailable as problem:
        print(str(problem), file=sys.stderr)
        return 2
    return module.main()


def surface() -> int:
    return _run("surface")


def super_harness() -> int:
    return _run("super")


def proxy() -> int:
    return _run("proxy")


def wrap() -> int:
    return _run("wrap")


def goal() -> int:
    return _run("goal")


def computer() -> int:
    return _run("computer")


def hook() -> int:
    """The per-prompt hook. Reads one event on stdin and writes one on stdout.

    Registered in a client config by name rather than by path when this is
    installed, because an installed package has no path a user could have
    written down.
    """
    return _run("pipeline")


def verify() -> int:
    """Check what this machine actually has, for either layout.

    The same verifier the repository runs. It resolves the skills, the block and
    the hook scripts through harness_paths, so a machine set up from this
    package verifies as readily as one set up from a checkout; before that it
    reported twenty-two failures against an install that was complete.
    """
    return _run("verify")


def where() -> int:
    """What this install resolved to. `--json` for a machine.

    Worth its own command because every other failure mode here is quiet: a
    wheel built without its skills, an old checkout found ahead of a new
    install, a state directory that is not writable. Each of those produces a
    harness that runs and enforces less than it says it does.
    """
    facts = resources.describe()
    if "--json" in sys.argv[1:]:
        print(json.dumps(facts, indent=2))
        return 0

    print(f"mode          {facts['mode']}")
    if facts["repo"]:
        print(f"repository    {facts['repo']}")
    print(f"skills        {facts['skillCount']} in {facts['skills']}")
    print(f"block         {'present' if facts['blockPresent'] else 'MISSING'} at {facts['block']}")
    print(f"goal state    {facts['state']}")
    print(f"hook command  {facts['hookCommand']}")

    problems = []
    if facts["skillCount"] == 0:
        problems.append("no skills resolved; this install cannot enforce anything")
    if not facts["blockPresent"]:
        problems.append("the canonical block is missing; installs would write nothing")
    if problems:
        print()
        for line in problems:
            print(f"PROBLEM  {line}", file=sys.stderr)
        return 1
    return 0
