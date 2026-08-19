# Managed Repositories

This lane is for useful functionality whose upstream repository is no longer suitable for the active Master Repo catalog because it is stale, archived, deleted, disabled, sunset, or abandoned.

## Lifecycle rule

The default catalog lifecycle is:

- **0–120 days since last upstream push:** active/healthy from a freshness perspective.
- **121–269 days:** stale warning. Keep it available but watch it more closely.
- **270–365 days:** replacement/adoption review. Look for a maintained upstream replacement; if none exists, evaluate whether the useful parts should become a Charles-managed project.
- **More than 365 days:** remove from the active/runtime catalog unless Charles explicitly approves a reference/stability exception.
- **Archived + recent activity/release:** do **not** auto-delete from the archived flag alone. Mark `REVIEW`, determine why it was archived, check releases/sunset notices/successor repos, and decide whether it is a transition reference, replacement case, or managed-adoption candidate.
- **Archived + no recent activity:** 30-day observation grace from first detection, then propose removal/replacement/adoption.
- **Static research/reference repos:** may receive a `reference` lifecycle override when inactivity is expected and the artifact is still useful. They must not be presented as actively maintained runtime dependencies.
- **Deleted or disabled upstream:** immediate removal candidate.
- **Confirmed CRITICAL security finding:** immediate removal candidate regardless of age.

The freshness clock is a maintenance signal, not proof of quality. Stable libraries and finished research artifacts can legitimately have quiet periods, while an archived repo can also be an explicit sunset even when its last release is recent. The guardian therefore combines metadata, explicit owner overrides, upstream notices, and deep security review.

## Managed-adoption gate

Before useful code from a lifecycle-expired upstream can become a Master Repo-managed replacement:

1. Run the full deep security scan.
2. Reject CRITICAL findings and resolve HIGH findings before adoption.
3. Verify the upstream license allows the proposed use, modification, and redistribution.
4. Preserve required copyright, license, NOTICE, attribution, and source obligations.
5. Identify the smallest still-useful component instead of blindly copying an entire abandoned repository.
6. Upgrade dependencies, CI, tests, documentation, and security controls.
7. Create the maintained replacement under an owner-approved `Charlesganu2004` repository or an explicitly approved managed package.
8. Re-run Guardian, dependency scanning, secret scanning, injection scanning, and malware scanning.
9. Add the maintained replacement back to the active catalog only after Charles approves the PR.

`managed-repos/candidates/` contains adoption-review notes. **Automation never silently copies third-party source code or creates a maintained fork without owner approval.**
