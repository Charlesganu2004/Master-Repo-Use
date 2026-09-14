"""Fetch only canonical release binaries with publisher-provided SHA256 evidence."""
import argparse
import io
import json
import zipfile
from pathlib import Path

from .audit import digest, fetch, save


def download(repo, output, executable):
    row = {"repo": repo, "executable": executable, "status": "blocked"}
    try:
        release = json.loads(fetch(f"https://api.github.com/repos/{repo}/releases/latest"))
        assets = release["assets"]
        suitable = [asset for asset in assets
                    if ("windows" in asset["name"].lower()
                        and ("x86_64" in asset["name"] or "amd64" in asset["name"])
                        and asset["name"].endswith(".zip"))]
        row["available_asset_names"] = [a["name"] for a in assets]
        if not suitable:
            raise ValueError("No supported verified Windows x64 ZIP asset; source-build alternative needs isolated Go/Rust toolchain and full dependency review")
        asset = suitable[0]
        data = fetch(asset["browser_download_url"])
        expected = asset.get("digest", "").removeprefix("sha256:")
        if not expected:
            checksums = next(a for a in assets if a["name"] == "checksums.txt")
            text = fetch(checksums["browser_download_url"]).decode()
            expected = next(line.split()[0] for line in text.splitlines() if asset["name"] in line)
        if digest(data) != expected:
            raise ValueError("Publisher artifact hash mismatch")
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            matches = [name for name in archive.namelist() if Path(name).name == executable]
            if len(matches) != 1:
                raise ValueError("Expected exactly one executable")
            binary = archive.read(matches[0])
        target = output / "bin" / executable
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(binary)
        row.update(status="verified-artifact", tag=release["tag_name"],
                   release_url=release["html_url"], asset_url=asset["browser_download_url"],
                   artifact_sha256=expected, binary_sha256=digest(binary), path=str(target))
    except Exception as error:  # noqa: BLE001 - preserve download/validation blockers
        row["blocker"] = str(error)
        if repo == "JuliusBrussee/caveman-browse":
            url = "https://registry.npmjs.org/caveman-browse/latest"
            try:
                metadata = json.loads(fetch(url))
                row["alternative"] = {"url": url, "version": metadata.get("version"),
                                      "status": "manifest available; downloader not executed"}
            except Exception as alternative_error:  # noqa: BLE001 - preserve single alternative failure
                row["alternative"] = {"url": url, "status": "blocked",
                                      "error": str(alternative_error)}
    return row


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [download("rtk-ai/rtk", args.output, "rtk.exe"),
            download("JuliusBrussee/caveman-browse", args.output, "caveman-browse.exe")]
    save(args.output / "binary-audit.json", rows)
    print(json.dumps(rows))
