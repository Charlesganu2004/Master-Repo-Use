"""Isolated public-site build fixture used by tests that write artifacts."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import tempfile
import uuid


SOURCE_ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER_SCRIPT = SOURCE_ROOT / "scripts" / "build_public_site.py"


def _load_builder():
    name = f"build_public_site_fixture_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, BUILDER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BUILDER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IsolatedPublicSite:
    """A builder instance whose complete public output lives under a temp root."""

    def __init__(self):
        self._scratch = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._scratch.name) / "repo"
        self.root.mkdir()
        shutil.copytree(SOURCE_ROOT / "repo-lists", self.root / "repo-lists")
        self.builder = _load_builder()
        self._configure()

    def _configure(self) -> None:
        builder = self.builder
        builder.ROOT = self.root
        builder.SITE = self.root / "_site"

        builder.PRIVATE_STATE = SOURCE_ROOT / "docs" / "catalog-status.json"
        builder.PRIVATE_INDEX = SOURCE_ROOT / "index.html"
        builder.PRIVATE_DESIGN_STUDIO = SOURCE_ROOT / "design-options.html"
        builder.PRIVATE_DESIGN_STUDIO_JS = SOURCE_ROOT / "design-options.js"
        builder.PRIVATE_ATLAS_CSS = SOURCE_ROOT / "atlas.css"
        builder.PRIVATE_ATLAS_JS = SOURCE_ROOT / "atlas.js"
        builder.PRIVATE_PROFILES = SOURCE_ROOT / "docs" / "hardware-profiles.json"
        builder.PRIVATE_DESIGNS = SOURCE_ROOT / "designs"
        builder.PRIVATE_ATLAS_DATA = SOURCE_ROOT / "atlas-data.json"
        builder.PUBLIC_ALLOWLIST_FILE = self.root / "repo-lists" / "public-allowlist.txt"

        builder.PUBLIC_STATE = builder.SITE / "docs" / "catalog-status.json"
        builder.PUBLIC_SVG = builder.SITE / "docs" / "catalog-status.svg"
        builder.PUBLIC_INDEX = builder.SITE / "index.html"
        builder.PUBLIC_DESIGN_STUDIO = builder.SITE / "design-options.html"
        builder.PUBLIC_DESIGN_STUDIO_JS = builder.SITE / "design-options.js"
        builder.PUBLIC_ATLAS_CSS = builder.SITE / "atlas.css"
        builder.PUBLIC_ATLAS_JS = builder.SITE / "atlas.js"
        builder.PUBLIC_PROFILES = builder.SITE / "docs" / "hardware-profiles.json"
        builder.PUBLIC_VERSION = builder.SITE / "version.json"
        builder.PUBLIC_DESIGNS = builder.SITE / "designs"

    def stage(self, *, design_studio: bool = True, version: bool = False) -> dict:
        builder = self.builder
        shutil.rmtree(builder.SITE, ignore_errors=True)
        (builder.SITE / "docs").mkdir(parents=True)
        shutil.copy(SOURCE_ROOT / "docs" / "catalog-status.svg", builder.PUBLIC_SVG)
        payload = builder.build()
        builder.PUBLIC_STATE.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        builder.build_index()
        if design_studio:
            problems = builder.build_design_studio()
            if problems:
                raise AssertionError("; ".join(problems))
        if version:
            builder.build_version(builder.build_id())
        return payload

    def cleanup(self) -> None:
        self._scratch.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.cleanup()
        return False
