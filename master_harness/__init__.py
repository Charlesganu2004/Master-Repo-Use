"""The Master Repo harness, installable without the repository.

Six harnesses and one standing pipeline, packaged so a machine can carry the
rules without carrying the catalog. `pip install` puts the commands on PATH:

    master-harness            the surface harness: install every client
    master-harness-super      one command that does what the others do, and more
    master-harness-proxy      an injecting proxy for OpenAI and Ollama clients
    master-harness-wrap       wrap a single command invocation
    master-harness-goal       the standing goal that survives the turn
    master-harness-computer   route work that needs a real machine or browser
    master-harness-hook       the per-prompt hook a client config registers
    master-harness-where      what this install resolved to, and from where

The rules themselves are not duplicated here. In a checkout the package reads
skills/ and docs/auto-mode-block.txt directly; in a wheel it carries a build-time
copy of both. resources.py is the only module that knows which.
"""
from __future__ import annotations

__version__ = "1.0.0"

from . import resources  # noqa: F401
from ._loader import HarnessNotAvailable, harness, load  # noqa: F401

__all__ = ["__version__", "resources", "harness", "load", "HarnessNotAvailable"]
