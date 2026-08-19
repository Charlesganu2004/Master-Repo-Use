# Managed Repositories

This lane is for useful functionality whose upstream repository is no longer suitable for the active Master Repo catalog because it is stale, archived, deleted, disabled, or abandoned.

## Lifecycle rule

The default catalog lifecycle is:

- **0–120 days since last upstream push:** active/healthy from a freshness perspective.
- **121–269 days:** stale warning. Keep it available but watch it more closely.
- **270–365 days:** replacement/adoption review. Look for a maintained upstream replacement; if none exists, evaluate whether the useful parts should become a Charles-managed project.
- **More than 365 days:** remove from the active catalog unless Charles explicitly approves an exception.
- **Archived upstream:** 30-day grace period from first detection, then remove from the active catalog unless Charles approves an exception.
- **Deleted or disabled upstream:** immediate removal candidate.
- **Confirmed CRITICAL security finding:** immediate removal candidate regardless of age.

The freshness clock is a maintenance signal, not proof of quality. Stable libraries can legitimately have quiet periods, which is why removal happens much later than the first stale warning.

## Managed-adoption gate

Before useful code from a lifecycle-expired upstream can become a Master Repo-managed replacement:

1. Run the full deep security scan.
2. Reject CRITICAL findings and resolve HIGH findings before adoption.
3. Verify the upstream license allows the proposed use, modification, and redistribution.
4. Preserve required copyright, license, NOTICE, attribution, and source obligations.
5. Identify the smallest still-useful component instead of blindly copying an entire abandoned repository.
6. Upgrade dependencies, CI, tests, documentation, and security controls.
7. Create the maintained replacement under an owner-approved Charlesganu2004 repository or an explicitly approved managed package.
8. Re-run Guardian, dependency scanning, secret scanning, injection scanning, and malware scanning.
9. Add the maintained replacement back to the active catalog only after Charles approves the PR.

`managed-repos/candidates/` contains automatically generated adoption-review notes. **Automation never silently copies third-party source code or creates a maintained fork without owner approval.**
