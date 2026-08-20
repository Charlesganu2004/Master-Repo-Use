#!/usr/bin/env python3
"""Master Repo Catalog Guardian entry point.

The lifecycle engine is preserved in ``catalog_guardian_legacy.py`` while the
security-sensitive helpers are patched from the small, independently tested
``catalog_security.py`` module.  This keeps the existing lifecycle behavior
stable while making scanner classification and secret handling fail closed.
"""
from __future__ import annotations

import catalog_guardian_legacy as _legacy
import catalog_security as _security

# Patch the lifecycle engine's module globals. Functions such as deep_scan resolve
# these names at call time, so they automatically use the hardened helpers.
for _name in (
    "INVISIBLE",
    "SUSPICIOUS",
    "PROMPT_INJECTION",
    "SQL",
    "SECRETS",
    "FINDING_EXIT_CODES",
    "REDACTIONS",
    "redact",
    "scan_text",
    "run_external",
    "run_gitleaks",
    "clamav_database_ready",
    "has_scanner_error",
):
    setattr(_legacy, _name, getattr(_security, _name))

# Re-export the legacy public surface for compatibility with existing docs/tests.
for _name in dir(_legacy):
    if not _name.startswith("_"):
        globals().setdefault(_name, getattr(_legacy, _name))

# Explicitly expose hardened helpers even if legacy exported names already existed.
redact = _security.redact
scan_text = _security.scan_text
run_external = _security.run_external
run_gitleaks = _security.run_gitleaks
clamav_database_ready = _security.clamav_database_ready
has_scanner_error = _security.has_scanner_error
FINDING_EXIT_CODES = _security.FINDING_EXIT_CODES
REDACTIONS = _security.REDACTIONS
SUSPICIOUS = _security.SUSPICIOUS
PROMPT_INJECTION = _security.PROMPT_INJECTION
SQL = _security.SQL
SECRETS = _security.SECRETS
INVISIBLE = _security.INVISIBLE

main = _legacy.main

if __name__ == "__main__":
    raise SystemExit(main())
