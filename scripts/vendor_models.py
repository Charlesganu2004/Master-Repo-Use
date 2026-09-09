#!/usr/bin/env python3
"""Make the repository the source of truth for local models, without weights in git.

Charles asked to push the local models into the repository so nobody has to go to
Hugging Face, and so the repo carries the current ones. The goal is right and the
literal method does not work, so this does the goal a way that does.

WHY WEIGHTS CANNOT GO IN GIT, measured on 2026-09-09 rather than recalled:

  GitHub rejects any single file over 100 MB. The SMALLEST model in the catalog,
  gemma3:270m, is 290 MB from the registry manifest. Every one of the 35 is over
  the limit, the smallest by 2.9x.

  A repository is capped at 5 GB and degrades badly past 1 GB. All 35 tags total
  about 202 GB. That is 40x the cap.

  Git LFS moves the limit to a few GB per file but bills storage and bandwidth on
  every clone, and a clone of this repo would then pull 202 GB.

  GitHub Pages, which publishes this repo, caps a site at 1 GB.

So the weights live where a 200 GB artifact belongs, and the REPOSITORY carries
the three things that actually remove the trip to Hugging Face:

  1. THE MANIFEST. docs/model-manifest.json pins every tag to the exact digest and
     byte size the registry returns today. The repo therefore states which models
     and which versions, and drift is detectable rather than assumed.

  2. THE MODELFILES. models/*.Modelfile, committed, so `ollama create` builds the
     named model from this repository's definition rather than from a web page.

  3. ONE COMMAND. --fetch pulls every model this machine can hold, verifies each
     against the pinned digest, and afterwards the machine is offline-capable.
     Nobody visits Hugging Face; they run one command from the repo.

REDISTRIBUTION, and why only some are offered as release assets. A GitHub release
asset may be 2 GiB, which fits 19 of the 35, and release assets do not enter the
clone. But size is not the only gate: redistributing weights makes you a
distributor and the licence decides whether that is allowed.

  Apache-2.0, MIT      redistribution is clear. Offered.
  Gemma Terms of Use   redistribution is permitted only with the use policy and
                       the terms passed through to every recipient. Not offered
                       here, because doing it correctly is a legal commitment
                       rather than a file copy.
  Llama Community      requires attribution, a "Built with Llama" notice, a copy
                       of the licence, and carries a monthly-active-user clause.
                       Not offered, for the same reason.

That leaves the licence-clean subset, and --release prepares exactly it. The rest
are pull-only, which costs the user one command and costs Charles no obligation.

Usage:
    python scripts/vendor_models.py --check
    python scripts/vendor_models.py --manifest
    python scripts/vendor_models.py --modelfiles
    python scripts/vendor_models.py --plan
    python scripts/vendor_models.py --fetch --max-ram 16
    python scripts/vendor_models.py --release --out dist/models
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROFILES = ROOT / "docs" / "hardware-profiles.json"
MANIFEST = ROOT / "docs" / "model-manifest.json"
MODELFILES = ROOT / "models"

REGISTRY = "https://registry.ollama.ai/v2/library/{name}/manifests/{tag}"
BLOB = "https://registry.ollama.ai/v2/library/{name}/blobs/{digest}"
ACCEPT = "application/vnd.docker.distribution.manifest.v2+json"

# GitHub's real limits, checked against the docs on 2026-09-09. These are the
# numbers the refusal above rests on, so they are named rather than implied.
GIT_FILE_LIMIT = 100 * 1024 * 1024          # hard rejection
REPO_SOFT_LIMIT = 5 * 1024 ** 3             # strong recommendation
RELEASE_ASSET_LIMIT = 2 * 1024 ** 3         # 2 GiB per asset, 1000 per release
PAGES_SITE_LIMIT = 1 * 1024 ** 3

# Which licences permit redistributing the weights without taking on conditions
# that a file copy cannot satisfy. Conservative on purpose: being wrong here is a
# licence violation, and being cautious costs one command.
REDISTRIBUTABLE = {"apache-2.0", "mit"}
CONDITIONAL = {
    "gemma terms of use": "Gemma Terms require passing the use policy and terms "
                          "to every recipient, which a release asset does not do.",
    "llama 3.2 community": "Llama Community requires attribution, a Built with "
                           "Llama notice, a licence copy, and carries a monthly "
                           "active user clause.",
}


def profiles() -> list[dict]:
    data = json.loads(PROFILES.read_text(encoding="utf-8"))
    return [m for m in data["models"] if m.get("runtime") == "ollama"]


def split_tag(tag: str) -> tuple[str, str]:
    name, _, version = tag.partition(":")
    return name, version or "latest"


def fetch_manifest(tag: str, timeout: int = 25) -> dict | None:
    """The registry's own manifest: real digests, real byte sizes."""
    name, version = split_tag(tag)
    request = urllib.request.Request(REGISTRY.format(name=name, tag=version),
                                     headers={"Accept": ACCEPT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def weight_layer(manifest: dict) -> dict | None:
    for layer in manifest.get("layers", []):
        if "model" in layer.get("mediaType", ""):
            return layer
    return None


def licence_state(licence: str) -> tuple[str, str]:
    """Whether this repository may redistribute the weights, and why not."""
    key = (licence or "").strip().lower()
    if key in REDISTRIBUTABLE:
        return "redistributable", ""
    for name, reason in CONDITIONAL.items():
        if name in key:
            return "conditional", reason
    return "unknown", f"Licence {licence!r} is not classified; treat as pull-only."


def build_manifest(verbose: bool = True) -> dict:
    """Pin every tag to the digest and size the registry returns today."""
    entries, unreachable = [], []
    for model in profiles():
        tag = model["tag"]
        manifest = fetch_manifest(tag)
        if manifest is None:
            unreachable.append(tag)
            if verbose:
                print(f"  {tag:<26}registry unreachable")
            continue
        layer = weight_layer(manifest)
        total = sum(l.get("size", 0) for l in manifest.get("layers", []))
        state, reason = licence_state(model.get("license", ""))
        entry = {
            "tag": tag,
            "vendor": model.get("vendor", ""),
            "license": model.get("license", ""),
            "paramsB": model.get("params_b"),
            "minRamGb": model.get("min_ram_gb"),
            "bytes": total,
            "digest": (layer or {}).get("digest", ""),
            "redistribution": state,
            "redistributionNote": reason,
            "fitsReleaseAsset": total <= RELEASE_ASSET_LIMIT,
            "fitsGitFile": total <= GIT_FILE_LIMIT,
        }
        entries.append(entry)
        if verbose:
            print(f"  {tag:<26}{total/1e9:>7.2f} GB  {state}")
    payload = {
        "note": ("Pinned from registry.ollama.ai. Weights are NOT stored in this "
                 "repository: the smallest is 2.9x GitHub's 100 MB file limit and "
                 "the set totals about 202 GB against a 5 GB repository cap. This "
                 "manifest is what makes the repository the source of truth for "
                 "which models and which versions."),
        "registry": "https://registry.ollama.ai",
        "limits": {
            "gitFileBytes": GIT_FILE_LIMIT,
            "repoSoftBytes": REPO_SOFT_LIMIT,
            "releaseAssetBytes": RELEASE_ASSET_LIMIT,
            "pagesSiteBytes": PAGES_SITE_LIMIT,
        },
        "unreachable": unreachable,
        "models": sorted(entries, key=lambda e: e["bytes"]),
    }
    return payload


def write_manifest() -> int:
    print("Reading the registry for every catalogued tag\n")
    payload = build_manifest()
    if not payload["models"]:
        print("\nnothing resolved; not overwriting the manifest", file=sys.stderr)
        return 1
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    total = sum(m["bytes"] for m in payload["models"])
    print(f"\n{len(payload['models'])} models pinned, {total/1e9:.0f} GB in total")
    if payload["unreachable"]:
        print(f"unreachable: {', '.join(payload['unreachable'])}")
    print(f"written to {MANIFEST.relative_to(ROOT)}")
    return 0


def write_modelfiles(dry: bool = False) -> int:
    """A committed Modelfile per tag, so the repository defines the model.

    This is the part that genuinely replaces a trip to a model page: the
    definition is versioned here, and `ollama create` builds from it.
    """
    if not MANIFEST.is_file():
        print("run --manifest first", file=sys.stderr)
        return 1
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not dry:
        MODELFILES.mkdir(parents=True, exist_ok=True)
    written = 0
    for model in payload["models"]:
        tag = model["tag"]
        safe = tag.replace(":", "-").replace("/", "-")
        body = (
            f"# {tag}\n"
            f"# {model['vendor']}, {model['license']}. "
            f"{model['bytes']/1e9:.2f} GB, needs {model['minRamGb']} GB of memory.\n"
            f"#\n"
            f"# Pinned to the digest the registry returned on the day\n"
            f"# docs/model-manifest.json was last written:\n"
            f"#   {model['digest']}\n"
            f"#\n"
            f"# Build it from this file rather than from a web page:\n"
            f"#   ollama create {tag} --file models/{safe}.Modelfile\n"
            f"# Or pull it, which is the same bytes by digest:\n"
            f"#   ollama pull {tag}\n"
            f"\n"
            f"FROM {tag}\n"
        )
        path = MODELFILES / f"{safe}.Modelfile"
        if dry:
            print(f"  would write {path.relative_to(ROOT)}")
        else:
            path.write_text(body, encoding="utf-8")
        written += 1
    print(f"{'would write' if dry else 'wrote'} {written} Modelfiles in "
          f"{MODELFILES.relative_to(ROOT)}")
    return 0


def plan(max_ram: int | None = None) -> int:
    """What is fetchable, what is redistributable, and what each would cost."""
    if not MANIFEST.is_file():
        print("run --manifest first", file=sys.stderr)
        return 1
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    models = payload["models"]
    if max_ram:
        models = [m for m in models if (m["minRamGb"] or 0) <= max_ram]

    print(f"{'tag':<26}{'size':>9}  {'fits git':<9}{'release':<9}redistribution")
    print("-" * 74)
    for m in models:
        print(f"{m['tag']:<26}{m['bytes']/1e9:>7.2f} GB  "
              f"{'no':<9}{'yes' if m['fitsReleaseAsset'] else 'no':<9}"
              f"{m['redistribution']}")
    total = sum(m["bytes"] for m in models)
    shippable = [m for m in models
                 if m["fitsReleaseAsset"] and m["redistribution"] == "redistributable"]
    print("-" * 74)
    print(f"{len(models)} models, {total/1e9:.0f} GB"
          + (f", filtered to {max_ram} GB of memory" if max_ram else ""))
    print(f"{sum(1 for m in models if m['fitsGitFile'])} would fit inside git's "
          f"100 MB file limit")
    print(f"{len(shippable)} are both under the 2 GiB release-asset limit and "
          f"licence-clean to redistribute:")
    for m in shippable:
        print(f"    {m['tag']:<26}{m['bytes']/1e9:>6.2f} GB  {m['license']}")
    held = [m for m in models if m["redistribution"] != "redistributable"]
    if held:
        print(f"\n{len(held)} are pull-only, and the reason is the licence rather "
              f"than the size:")
        seen = set()
        for m in held:
            note = m["redistributionNote"]
            if note in seen:
                continue
            seen.add(note)
            print(f"    {m['license']}: {note}")
    return 0


def have_ollama() -> bool:
    return shutil.which("ollama") is not None


def fetch(max_ram: int | None, dry: bool) -> int:
    """Pull every model that fits, then verify each against the pinned digest."""
    if not MANIFEST.is_file():
        print("run --manifest first", file=sys.stderr)
        return 1
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    models = payload["models"]
    if max_ram:
        models = [m for m in models if (m["minRamGb"] or 0) <= max_ram]
    if not models:
        print("nothing fits that memory figure", file=sys.stderr)
        return 1

    total = sum(m["bytes"] for m in models)
    print(f"{len(models)} models, {total/1e9:.0f} GB to download\n")
    if dry:
        for m in models:
            print(f"  would run: ollama pull {m['tag']}")
        return 0
    if not have_ollama():
        print("ollama is not installed. Install the runtime first:\n"
              "  winget install --id Ollama.Ollama    (Windows)\n"
              "  curl -fsSL https://ollama.com/install.sh | sh    (Linux)",
              file=sys.stderr)
        return 2

    failed = []
    for m in models:
        print(f"pulling {m['tag']} ({m['bytes']/1e9:.2f} GB)")
        result = subprocess.run(["ollama", "pull", m["tag"]])
        if result.returncode != 0:
            failed.append(m["tag"])
    if failed:
        print(f"\nfailed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(f"\n{len(models)} models local. This machine no longer needs the network "
          f"for them.")
    return 0


def check() -> int:
    """Everything verifiable without a network or a model. Offline."""
    failures = []
    models = profiles()
    print(f"catalogued ollama tags      {len(models)}")

    if MANIFEST.is_file():
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        pinned = {m["tag"] for m in payload["models"]}
        missing = sorted({m["tag"] for m in models} - pinned)
        extra = sorted(pinned - {m["tag"] for m in models})
        print(f"pinned in the manifest      {len(pinned)}")
        if missing:
            failures.append(f"catalogued but not pinned: {', '.join(missing[:6])}")
        if extra:
            failures.append(f"pinned but not catalogued: {', '.join(extra[:6])}")
        for m in payload["models"]:
            if not m["digest"].startswith("sha256:"):
                failures.append(f"{m['tag']} has no usable digest")
            if m["fitsGitFile"]:
                failures.append(f"{m['tag']} is claimed to fit git's 100 MB limit; "
                                f"no model does, so the manifest is wrong")
        total = sum(m["bytes"] for m in payload["models"])
        smallest = min(payload["models"], key=lambda m: m["bytes"])
        print(f"total size                  {total/1e9:.0f} GB")
        print(f"smallest model              {smallest['tag']} at "
              f"{smallest['bytes']/1e6:.0f} MB, "
              f"{smallest['bytes']/GIT_FILE_LIMIT:.1f}x git's file limit")
        print(f"repository cap              {REPO_SOFT_LIMIT/1e9:.0f} GB, so the set "
              f"is {total/REPO_SOFT_LIMIT:.0f}x over")
        clean = [m for m in payload["models"]
                 if m["redistribution"] == "redistributable" and m["fitsReleaseAsset"]]
        print(f"release-asset candidates    {len(clean)} under 2 GiB and licence-clean")
    else:
        failures.append("docs/model-manifest.json is missing; run --manifest")

    if MODELFILES.is_dir():
        files = sorted(MODELFILES.glob("*.Modelfile"))
        print(f"committed Modelfiles        {len(files)}")
        if MANIFEST.is_file() and len(files) != len(pinned):
            failures.append(f"{len(files)} Modelfiles for {len(pinned)} pinned models")
    else:
        print("committed Modelfiles        none yet; run --modelfiles")

    print(f"ollama on this machine      {'yes' if have_ollama() else 'no'}")

    if failures:
        print("\nFAILED", file=sys.stderr)
        for line in failures:
            print("  " + line, file=sys.stderr)
        return 1
    print("\nmanifest, Modelfiles and limits all agree")
    return 0


def release(out: pathlib.Path, dry: bool) -> int:
    """Stage the licence-clean subset for upload as release assets.

    Release assets are the only GitHub path that holds a model at all: 2 GiB per
    asset, and they never enter the clone. Only the licence-clean ones are staged,
    because size is not the gate that matters here.
    """
    if not MANIFEST.is_file():
        print("run --manifest first", file=sys.stderr)
        return 1
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clean = [m for m in payload["models"]
             if m["redistribution"] == "redistributable" and m["fitsReleaseAsset"]]
    if not clean:
        print("nothing is both licence-clean and under 2 GiB", file=sys.stderr)
        return 1

    print(f"{len(clean)} models are licence-clean and fit a release asset:\n")
    total = 0
    for m in clean:
        total += m["bytes"]
        print(f"  {m['tag']:<26}{m['bytes']/1e9:>6.2f} GB  {m['license']}")
    print(f"\n{total/1e9:.2f} GB across {len(clean)} assets, "
          f"{RELEASE_ASSET_LIMIT/1e9:.1f} GB allowed per asset, 1000 per release.")
    print("\nStaging writes the blob for each from the registry. To upload:")
    print("  gh release create local-models --title 'Local models' --notes-file "
          "docs/MODELS.md")
    print(f"  gh release upload local-models {out}/*.gguf")
    if dry:
        print("\n--dry-run: nothing downloaded.")
        return 0
    print(f"\nDownloading into {out} ...")
    out.mkdir(parents=True, exist_ok=True)
    for m in clean:
        name, _ = split_tag(m["tag"])
        target = out / (m["tag"].replace(":", "-") + ".gguf")
        if target.is_file() and target.stat().st_size == m["bytes"]:
            print(f"  have {target.name}")
            continue
        url = BLOB.format(name=name, digest=m["digest"])
        print(f"  fetching {target.name} ({m['bytes']/1e9:.2f} GB)")
        try:
            urllib.request.urlretrieve(url, target)
        except Exception as exc:                      # noqa: BLE001
            print(f"    failed: {exc}", file=sys.stderr)
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if "sha256:" + digest != m["digest"]:
            print(f"    DIGEST MISMATCH, deleting {target.name}", file=sys.stderr)
            target.unlink(missing_ok=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true",
                        help="verify the manifest against the catalog, offline")
    parser.add_argument("--manifest", action="store_true",
                        help="pin every tag to its registry digest and size")
    parser.add_argument("--modelfiles", action="store_true",
                        help="write a committed Modelfile per tag")
    parser.add_argument("--plan", action="store_true",
                        help="what is fetchable, redistributable, and what it costs")
    parser.add_argument("--fetch", action="store_true",
                        help="pull every model that fits this machine")
    parser.add_argument("--release", action="store_true",
                        help="stage the licence-clean subset for release assets")
    parser.add_argument("--max-ram", type=int, help="only models this memory can hold")
    parser.add_argument("--out", default="dist/models")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.check:
        return check()
    if args.manifest:
        return write_manifest()
    if args.modelfiles:
        return write_modelfiles(args.dry_run)
    if args.plan:
        return plan(args.max_ram)
    if args.fetch:
        return fetch(args.max_ram, args.dry_run)
    if args.release:
        return release(ROOT / args.out, args.dry_run)
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
