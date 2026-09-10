# Install the harness without the repository

The rules used to require a checkout. Every hook pointed at
`scripts/hooks/skill_pipeline.py` by absolute path, every skill was read from
`skills/` at the repository root, and setting up a second machine meant cloning
a private catalog to get at four scripts inside it.

They are a package now. `pip install` puts the commands on PATH, the skills and
the canonical block travel inside the wheel, and nothing needs a clone.

## Install

```bash
pipx install git+https://github.com/Charlesganu2004/Master-Repo-Use
```

`pipx` is the right tool for something whose value is commands on PATH: it keeps
its own virtual environment so the harness cannot collide with a project's
dependencies. `pip install` works identically if you would rather it went into
the current environment.

There are no runtime dependencies. Every harness uses only the standard library,
so this installs into a locked-down environment and an offline one, and a
supply-chain question about it has no third party in the answer.

## Check what you got

```bash
master-harness-where
```

```
mode          installed
skills        20 in .../site-packages/master_harness/_skills
block         present at .../site-packages/master_harness/_data/auto-mode-block.txt
goal state    C:\Users\you\AppData\Local\master-harness
hook command  master-harness-hook
```

Worth running first, because every failure mode here is quiet. A wheel built
without its skills, an old checkout found ahead of a new install, a state
directory that is not writable: each one produces a harness that runs and
enforces less than it says it does. This command is how you find out.

## Set a machine up

```bash
cd your-project
master-harness --install all
master-harness-verify
```

That writes, for each of Claude Code, Codex, the Gemini CLI, Antigravity, Cursor
and the Copilot CLI: the standing block into its instruction file, all 20 skills
into its skill root, and the per-prompt hook plus both guards into its config.
It also puts the block into `CLAUDE.md`, `AGENTS.md` and `GEMINI.md` in the
project you ran it from, and mirrors the skills into `.agents/skills` there.

`master-harness-verify` then checks all of it and prints a count. Anything other
than `0 failed` names the file and the reason.

## The commands

    master-harness            install every client; --bundle for a browser product
    master-harness-super      one command that does what the others do, and more
    master-harness-proxy      an injecting proxy for OpenAI and Ollama clients
    master-harness-wrap       put the rules in front of one command invocation
    master-harness-goal       the standing goal that survives the turn
    master-harness-computer   route work needing a real machine or a browser
    master-harness-hook       the per-prompt hook a client config registers
    master-harness-where      what this install resolved to, and from where
    master-harness-verify     check what a machine actually has

Every one takes `--check`, which contacts nothing and reports what it can prove.

## What the goal does on an installed copy

The first substantive prompt of a session becomes the standing goal, with
nothing typed. Installed, it is written to a per-user directory rather than
beside a repository:

    Windows   %LOCALAPPDATA%\master-harness\goal.json
    macOS     ~/.local/share/master-harness/goal.json
    Linux     $XDG_DATA_HOME/master-harness/goal.json

`MASTER_REPO_GOAL_DIR` overrides it, which is how the tests keep their fixtures
out of the real store.

An installed copy has no committed goal to inherit. A wheel that shipped one
would put whatever its author last set in front of a stranger's prompts, so the
seed is deliberately absent and a fresh install starts with no goal.

## If you also have a checkout

The package finds it and uses it. Skills come from `skills/`, the block from
`docs/auto-mode-block.txt`, and the goal from `.auto-mode/` beside them, which
is what every existing installation already points at.

That is detection, not configuration: a checkout is identifiable by containing
`skills/master-repo-auto/SKILL.md` and `docs/auto-mode-block.txt`. Set
`MASTER_REPO_PATH` if yours is somewhere the search will not reach.

Precedence runs the other way inside the package: a bundled module is preferred
over one found in a checkout, so an installed copy never depends on finding a
working tree, and a machine with both gets what it installed rather than
whatever is mid-edit.

## What it will not do

It will not write the project-scoped Cursor rule or the project hook files into
a project that is not this repository. Those are committed content here and they
carry relative paths into `scripts/hooks/`, which means nothing in a project
that has no `scripts/hooks/`. An installed copy enforces through the
home-scoped hooks, which point at the package by absolute path because that is
where the code actually is.

It will not reach a program that is already running, or a browser tab. Those
limits belong to the harnesses themselves and are on each one's card.

## Building the wheel yourself

```bash
python -m build --wheel
```

The build copies the harness modules, every `SKILL.md`, the agent roster and the
canonical block into the package first. They are not committed inside
`master_harness/`: the repository keeps one copy of each, and a second committed
copy is the duplication that drifts. The build refuses rather than producing a
wheel with no skills in it.

To run the test that proves an install works with no repository present:

```bash
MASTER_HARNESS_BUILD_TEST=1 python -m pytest tests/test_package.py
```

It builds a wheel, installs it into a throwaway environment, and runs the
commands from a directory with no checkout above it. That test is the reason
this page can make the claim at the top of it.
