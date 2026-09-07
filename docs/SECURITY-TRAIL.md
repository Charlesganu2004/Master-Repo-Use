# Security trail

<!-- NO-COMPRESS:BEGIN -->
An audit record that can be summarised is not an audit record. This file carries
the no-compress markers so the guard refuses any pass over it: the rows are the
evidence, and a shortened row is a changed fact.
<!-- NO-COMPRESS:END -->

Append-only. Every automated scan and every action taken on its findings lands
here, whether or not it changed anything. Written by `scripts/security_trail.py`
from the workflow that did the work.

Read this rather than the issue comments when you want to know what actually
happened: issues get closed and comments get edited, and this is in git history.

Three rules the automation follows, and this file is how you check it kept them:

1. A bot may scan, report, comment and open a pull request. It may not merge, and
   it may not delete a catalog entry.
2. Every scan writes a row here, including the ones that found nothing. A quiet
   period should be visible as quiet rows, not as an absence of rows.
3. Removals require an owner approval phrase, and the row records which one.

| UTC | Run | Action | Scope | Outcome | Authorised by | Budget |
|---|---|---|---|---|---|---|
| 2026-09-01 13:08 | local | metadata-audit | 304 catalogued repositories | healthy 298, stale 2, review 3, remove 1 (removals held, see issue 16) | scheduled weekly run, no approval required for a read-onl... | 292 of 3000 min |
| 2026-09-01 13:08 | local | fixture-exemption-fix | gitleaks severity mapping in catalog_guardian_legacy and catalog_se... | 56 fixture CRITICALs recategorised to HIGH; no repository removed | owner instruction, this session | 292 of 3000 min |
| 2026-09-01 13:15 | local | verdict-substantiation-fix | both REMOVE paths in catalog_guardian_legacy | a verdict with no quotable finding now becomes REVIEW, not REMOVE; llama.cpp case repro... | owner instruction, this session | 292 of 3000 min |
| 2026-09-01 13:40 | local | branch-deletion | feature/cpp-lane-and-designs (0 unique files); feature/graphite-ful... | both deleted on owner instruction; constellation recoverable from d1b5ff7b46cd784b44b92... | owner said go, this session | 292 of 3000 min |
| 2026-09-01 13:43 | local | branch-deletion | feature/cpp-lane-and-designs; feature/graphite-full-map | deleted on owner instruction; cpp-lane had 0 unique files, graphite held the last copy ... | owner instruction: go | 292 of 3000 min |
| 2026-09-07 14:20 | [34128162448](https://github.com/Charlesganu2004/Master-Repo-Use/actions/runs/34128162448) | deep-scan-rotation | rotating slice of the catalog, read-only | scan job finished with status cancelled | scheduled rotation; read-only, so no owner phrase required | 0 of 3000 minutes |
