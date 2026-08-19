# Catalog Status

![Live catalog health](catalog-status.svg)

The Catalog Guardian is enabled and refreshes this page automatically. It runs metadata health checks every six hours, deep-vets newly added repositories immediately, rotates deeper source/security scans through the existing catalog, and updates the SVG/JSON status artifacts.

Status meanings:

- 🟢 **HEALTHY** — active and no current removal signal.
- 🟡 **STALE** — no recent push inside the configured freshness window; review, but do not auto-remove solely for age.
- 🟠 **REVIEW** — high-risk static/security pattern needs human review.
- 🔴 **REMOVE** — deleted/disabled/archived or a critical deep-scan finding; eligible for automatic removal under the guardian policy.

The first generated full table will replace/extend this content when the workflow completes.
