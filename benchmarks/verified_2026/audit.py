"""Read-only upstream/archive audit and selective recovery. No archive overlay."""
import argparse
import hashlib
import json
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "private-benchmark-audit"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive_audit(archive, output, comparison=None):
    base = "Master-Repo-Use/benchmarks/2026-09-11/"
    names = ["results/coding-runs.json", "results/browser-runs.json",
             "results/summary.json", "arms/manifest.json", "prompts/coding.json",
             "hidden/hidden_t1.py", "hidden/hidden_t2.py"]
    audit = {"kind": "archival-unverified", "date_label": "2026-09-11",
             "archive_sha256": digest(archive.read_bytes()), "files": [],
             "limitations": [
                 "Archive is a partial export, not fresh execution.",
                 "Provider raw sessions and pricing/rate sources are absent.",
                 "Judge arrays are empty; no judge quality claims are recoverable.",
                 "Old summary excludes missing denominators from correctness, inflating pass rates.",
                 "Duration parser and single-key limiter are easier than the new tasks.",
                 "Common system instructions, tools and cache state were not controlled.",
                 "Do not reuse old medians, cost rankings, browser timings, or charts as fresh results."]}
    with zipfile.ZipFile(archive) as source:
        inventory = [i for i in source.infolist() if i.filename.startswith(base) and not i.is_dir()]
        audit["inventory_files"] = len(inventory)
        for name in names:
            data = source.read(base + name)
            target = output / "archive" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            audit["files"].append({"path": name, "sha256": digest(data), "bytes": len(data)})
        rows = json.loads(source.read(base + names[0]))
        audit["coding_rows"] = len(rows)
        audit["expected_claimed_rows"] = 60
        audit["missing_solution_rows"] = sum(row.get("solutionLoc", 0) == 0 for row in rows)
        audit["missing_denominator_rows"] = sum(not row.get("hidden", {}).get("total") for row in rows)
        audit["judge_rows"] = sum(bool(row.get("judges")) for row in rows)
        audit["correct_complete_rows"] = sum(
            bool(row.get("hidden", {}).get("total"))
            and row["hidden"]["passed"] == row["hidden"]["total"] for row in rows)
        audit["observed_complete_fraction"] = audit["correct_complete_rows"] / len(rows)
    if comparison:
        data = comparison.read_bytes()
        entries = json.loads(data)
        audit["parent_comparison_sha256"] = digest(data)
        audit["comparison_benchmark_entries"] = sum("benchmarks/" in str(row) for row in entries)
    save(output / "archive-audit.json", audit)
    return audit


def upstream_audit(output):
    candidates = {
        "DietrichGebert/ponytail": ["package.json", "LICENSE", "skills/ponytail/SKILL.md"],
        "JuliusBrussee/caveman": ["LICENSE", "skills/caveman/SKILL.md"],
        "JuliusBrussee/caveman-browse": ["LICENSE", "go.mod", "package.json", "README.md"],
        "Skyvern-AI/rustwright": ["LICENSE", "pyproject.toml", "README.md"],
        "rtk-ai/rtk": ["LICENSE", "Cargo.toml", "README.md"],
    }
    results = []
    for repo, paths in candidates.items():
        row = {"repo": repo, "retrieved_at": datetime.now(timezone.utc).isoformat(),
               "scanners": {"gitleaks": None, "trivy": None, "osv": None, "semgrep": None},
               "scope": "metadata and selected install manifests only; no full source scan"}
        try:
            meta = json.loads(fetch("https://api.github.com/repos/" + repo))
            if meta["full_name"].lower() != repo.lower() or meta["fork"] or meta["archived"]:
                raise ValueError("canonical active upstream gate failed")
            sha = json.loads(fetch(f"https://api.github.com/repos/{repo}/commits/{meta['default_branch']}"))["sha"]
            row.update(sha=sha, license=(meta.get("license") or {}).get("spdx_id"),
                       pushed_at=meta["pushed_at"], files=[])
            for path in paths:
                try:
                    url = f"https://raw.githubusercontent.com/{repo}/{sha}/{path}"
                    data = fetch(url)
                    target = output / "upstreams" / repo.replace("/", "_") / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    row["files"].append({"path": path, "sha256": digest(data), "url": url,
                                         "install_risk_markers": re.findall(
                                             r"postinstall|preinstall|build-backend|curl.*\|\s*(?:sh|bash)",
                                             data.decode("utf-8", "replace"))})
                except Exception as error:  # noqa: BLE001 - retain partial upstream retrieval evidence
                    row["files"].append({"path": path, "error": str(error)})
            row["verdict"] = "PASS-WITH-NOTE: instruction-only use or prebuilt artifacts; full scan unverified"
        except Exception as error:  # noqa: BLE001 - unavailable sources become explicit blockers
            row.update(verdict="BLOCKED", error=str(error))
        results.append(row)
    save(output / "upstream-audit.json", results)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--comparison", type=Path)
    parser.add_argument("--upstreams", action="store_true")
    args = parser.parse_args()
    if args.archive:
        print(json.dumps(archive_audit(args.archive, args.output, args.comparison)))
    if args.upstreams:
        print(json.dumps(upstream_audit(args.output)))
