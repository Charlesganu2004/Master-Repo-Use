"""Create a reviewed export without raw CLI transcripts, caches or local identities."""
import argparse
import hashlib
import json
import pathlib
import re
import zipfile

OMIT = {"stdout", "stderr", "stdout_hex", "stderr_hex", "raw_usage"}
FILES = (
    "REPORT.md", "summary.json", "manifest.json", "execution-audit.json",
    "coding-runs.json", "command-runs.json", "browser-runs.json",
    "archive-audit.json", "binary-audit.json", "upstream-audit.json", "rtk-runtime.json",
    "caveman-alternative-audit.json", "final-scoring-reconciliation.json",
    "scope-label-verification.json",
    "correction-v2/manifest.json", "correction-v2/frozen-v1-rows.json", "correction-v2/REPORT.md",
    "generation-set-2/manifest.json", "generation-set-2/reconciliation.json",
    "generation-set-2/controlled-runs/execution-audit.json",
    "generation-set-2/controlled-runs/coding-runs.json",
    "generation-set-2/controlled-runs/schedule.json",
)


def clean_text(text):
    text = re.sub(r"(?i)/mnt/[a-z]/Users/[^/\s\"<>]+", "<USER_HOME>", text)
    text = re.sub(r"(?i)[a-z]:[\\/]+Users[\\/]+[^\\/\s\"<>]+", "<USER_HOME>", text)
    return text.replace("u301268", "<LOCAL_USER>")


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items() if key not in OMIT}
    if isinstance(value, list):
        return [clean(item) for item in value]
    return clean_text(value) if isinstance(value, str) else value


def export(source, destination):
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Export destination must be empty; existing files are never removed")
    selected = [source / name for name in FILES if (source / name).is_file()]
    for folder, pattern in (("graphs", "*.svg"), ("prompts", "*.txt"),
                            ("generation-set-2/prompts", "*.txt"),
                            ("correction-v2/graphs", "*.svg"), ("correction-v2", "prompt.txt")):
        selected.extend((source / folder).rglob(pattern))
    for folder in ("coding", "generation-set-2/controlled-runs", "correction-v2"):
        for name in ("solution.py", "agent_tests.py.txt", "metrics.json", "evaluation.json",
                     "reevaluation-v3.json", "audit.json"):
            pattern = "*/" + name if folder == "generation-set-2/controlled-runs" else "*/*/" + name
            selected.extend((source / folder).glob(pattern))
    public_sources = set()
    for name, repo in (("ponytail", "DietrichGebert_ponytail"), ("caveman", "JuliusBrussee_caveman")):
        for relative in (pathlib.Path("LICENSE"), pathlib.Path("skills") / name / "SKILL.md"):
            path = source / "upstreams" / repo / relative
            if path.is_file():
                selected.append(path)
                public_sources.add(path)
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "private": True,
        "transform": "Raw CLI output and raw usage objects omitted; argument flags retained with local path redaction; pinned public skill sources unchanged",
        "metrics": "Measured numeric fields unchanged; byte counts and source hashes describe raw originals",
        "raw_evidence": "Retained only in the original session artifact directory and private ZIP",
        "files": [],
    }
    for path in sorted(set(selected)):
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents if parent != source.parent):
            raise ValueError("Symlink evidence is not exportable")
        relative = path.relative_to(source)
        original = path.read_bytes()
        if path in public_sources:
            rendered = original.decode("utf-8")
        elif path.suffix == ".json":
            rendered = json.dumps(clean(json.loads(original)), indent=2) + "\n"
        else:
            rendered = clean_text(original.decode("utf-8"))
        if re.search(r"(?i)u301268|[a-z]:[\\/]+Users[\\/]", rendered):
            raise ValueError("Local identity remains in export")
        if re.search(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN .*PRIVATE KEY-----)", rendered):
            raise ValueError("Potential credential found; export stopped")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        transformed = rendered.encode("utf-8")
        target.write_bytes(transformed)
        manifest["files"].append({
            "path": relative.as_posix(),
            "raw_source_sha256": hashlib.sha256(original).hexdigest(),
            "export_sha256": hashlib.sha256(transformed).hexdigest(),
        })
    (destination / "export-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def bundle(exported, output):
    """Package only reviewed data, reproducible code, prompts and checks."""
    here = pathlib.Path(__file__).parent
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(exported.rglob("*")):
            if item.is_symlink():
                raise ValueError("Symlink export is not packageable")
            if item.is_file():
                archive.write(item, "evidence/" + item.relative_to(exported).as_posix())
        for item in sorted(here.glob("*.py")):
            archive.write(item, "benchmarks/verified_2026/" + item.name)
        for name in ("README.md", "requirements.txt"):
            archive.write(here / name, "benchmarks/verified_2026/" + name)
        for name in ("test_benchmark_verified.py", "test_isolated_benchmark.py", "test_benchmark_export.py"):
            path = here.parents[1] / "tests" / name
            if path.exists():
                archive.write(path, "tests/" + name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, required=True)
    parser.add_argument("--destination", type=pathlib.Path, required=True)
    parser.add_argument("--zip", type=pathlib.Path)
    args = parser.parse_args()
    result = export(args.source.resolve(), args.destination.resolve())
    if args.zip:
        bundle(args.destination.resolve(), args.zip)
    print(f"Exported {len(result['files'])} reviewed evidence files")
