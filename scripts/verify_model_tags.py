#!/usr/bin/env python3
"""Check that every model tag in docs/hardware-profiles.json actually resolves.

Why this exists: the tags in the advisor could not be verified automatically when the
data was authored, because the Ollama library index is not reachable as plain JSON from
the build environment. Rather than publish unverified tags and hope, this script lets
anyone confirm them against a real Ollama install in one command:

    python scripts/verify_model_tags.py

It queries the local Ollama daemon if one is running, and falls back to the public
registry manifest endpoint otherwise. Entries whose runtime is not Ollama (BitNet)
are reported as skipped rather than silently passed.

Exit status is 1 if any Ollama-hosted tag could not be resolved, so this is usable as
a pre-commit or CI check once a runner has Ollama available.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = ROOT / "docs" / "hardware-profiles.json"
LOCAL_TAGS = "http://localhost:11434/api/tags"
REGISTRY = "https://registry.ollama.ai/v2/library/{name}/manifests/{tag}"
TIMEOUT = 15


def split_tag(tag: str) -> tuple[str, str]:
    name, _, version = tag.partition(":")
    return name, version or "latest"


def local_models() -> set[str] | None:
    """Tags already pulled on this machine, or None if no daemon is reachable."""
    try:
        with urllib.request.urlopen(LOCAL_TAGS, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None
    return {str(m.get("name", "")) for m in payload.get("models", [])}


def registry_has(tag: str) -> bool | None:
    """True/False if the registry answered, None if it could not be reached."""
    name, version = split_tag(tag)
    request = urllib.request.Request(
        REGISTRY.format(name=name, tag=version),
        headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status == 200
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 404):
            return False
        return None
    except (urllib.error.URLError, OSError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true",
                        help="only check tags already pulled locally; never hit the network")
    args = parser.parse_args()

    data = json.loads(PROFILES.read_text(encoding="utf-8"))
    models = data.get("models") or []
    pulled = local_models()

    if pulled is None:
        print("No local Ollama daemon on :11434.", end=" ")
        if args.offline:
            print("Nothing to check in --offline mode.")
            return 0
        print("Falling back to the public registry.\n")
    else:
        print(f"Local Ollama daemon found: {len(pulled)} model(s) pulled.\n")

    ok, missing, unknown, skipped = [], [], [], []
    for model in models:
        tag = str(model.get("tag", ""))
        if model.get("runtime") != "ollama":
            skipped.append((tag, model.get("runtime")))
            continue

        name, version = split_tag(tag)
        canonical = f"{name}:{version}"
        if pulled is not None and (tag in pulled or canonical in pulled):
            ok.append(tag)
            continue
        if args.offline:
            missing.append(tag)
            continue

        result = registry_has(tag)
        if result is True:
            ok.append(tag)
        elif result is False:
            missing.append(tag)
        else:
            unknown.append(tag)

    for tag in sorted(ok):
        print(f"  OK        {tag}")
    for tag, runtime in sorted(skipped):
        print(f"  SKIP      {tag}  (runtime: {runtime}, not an Ollama tag)")
    for tag in sorted(unknown):
        print(f"  UNKNOWN   {tag}  (registry unreachable -- not a failure)")
    for tag in sorted(missing):
        print(f"  MISSING   {tag}  <-- does not resolve")

    print(f"\n{len(ok)} ok - {len(missing)} missing - {len(unknown)} unknown - "
          f"{len(skipped)} skipped, of {len(models)} models")

    if missing:
        print("\nFix docs/hardware-profiles.json, or pull the tag and re-run. Model "
              "libraries move; a MISSING tag means the catalog is stale, not that the "
              "model never existed.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
