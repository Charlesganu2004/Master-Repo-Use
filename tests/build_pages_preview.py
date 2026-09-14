"""Build a privacy-verified Pages preview outside the checkout."""
import argparse
import pathlib
import shutil
import sys
import tempfile

from public_site_fixture import IsolatedPublicSite

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    args = parser.parse_args()
    output = args.out.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("--out must be outside the private checkout")
    if output.exists() and any(output.iterdir()):
        parser.error("--out must be empty; existing artifacts are never overwritten")
    output.parent.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(output.parent)
    with IsolatedPublicSite() as fixture:
        payload = fixture.stage(version=True)
        problems = fixture.builder.verify(payload)
        if problems:
            for problem in problems:
                print("PRIVACY FAILURE: " + problem, file=sys.stderr)
            return 1
        shutil.copytree(fixture.builder.SITE, output, dirs_exist_ok=True)
    print("Public artifact OK: privacy verification passed; profiles and every design included.")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
