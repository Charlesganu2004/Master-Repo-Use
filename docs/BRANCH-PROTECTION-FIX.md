# Fixing `reviews: 1` and `codeowners: true`

## The thing to understand first

**Branch protection is not a file.** It lives on GitHub's servers, attached to the branch, not
in the repository. Nothing you open in VS Code can change it, and no workflow YAML controls it.

That is why editing `.github/workflows/owner-approval.yml` will not help. That workflow *produces*
the `owner-approval` status check. A separate server-side setting says "also require 1 approving
review and a code-owner review". Those are two different systems.

## Why the current setting makes your own PRs unmergeable

GitHub **does not allow anyone to approve their own pull request.** You author the PRs, and
`.github/CODEOWNERS` names you as the code owner. So on every PR you open:

- "Require 1 approving review" — you cannot satisfy it, because you cannot approve yourself.
- "Require review from Code Owners" — the only code owner is you.

The requirement is structurally unsatisfiable, which is why the only way through has been
**Merge without waiting for requirements (bypass rules)** every single time.

`scripts/branch-protection.json` — the policy this repository already commits — says
`required_approving_review_count: 0` and `require_code_owner_reviews: false`, with `owner-approval`
as the single authoritative gate. The live setting has drifted from it.

## Fix A — one command (recommended)

From a clone, applying the policy already in the repo:

```bash
gh api --method PUT repos/Charlesganu2004/Master-Repo-Use/branches/main/protection \
  --input scripts/branch-protection.json
```

Verify:

```bash
gh api repos/Charlesganu2004/Master-Repo-Use/branches/main/protection \
  --jq '{reviews:.required_pull_request_reviews.required_approving_review_count, codeowners:.required_pull_request_reviews.require_code_owner_reviews, checks:.required_status_checks.contexts}'
```

Expected afterwards:

```json
{"reviews": 0, "codeowners": false, "checks": ["owner-approval"]}
```

## Fix B — in the web UI

1. <https://github.com/Charlesganu2004/Master-Repo-Use/settings/branches>
2. Next to the `main` rule, click **Edit**.
3. Under **Protect matching branches**:
   - **Uncheck** "Require a pull request before merging → Require approvals"
     *(or set the count to 0 — the dropdown does not always allow 0, in which case uncheck the
     parent "Require approvals" box entirely)*
   - **Uncheck** "Require review from Code Owners"
4. Leave **Require status checks to pass** ticked with **`owner-approval`** selected.
5. **Save changes** at the bottom. It is easy to miss.

## Does this weaken anything?

No, and this is worth being precise about.

The protection that actually matters here is the `owner-approval` status check, which is
**SHA-bound**: approval applies to one exact commit, so a force-push or a new commit invalidates
it. That check stays required.

What is being removed is a review requirement that **has never once been satisfied** — every merge
so far went through bypass, which is strictly weaker than a gate that actually runs. Removing an
unsatisfiable requirement and keeping the working one is a net increase in enforcement.

## After the change

Merging a PR becomes:

```bash
gh pr comment <NUMBER> --repo Charlesganu2004/Master-Repo-Use \
  --body "APPROVE OWNER PR $(gh pr view <NUMBER> --repo Charlesganu2004/Master-Repo-Use --json headRefOid --jq .headRefOid)"
```

Wait for `owner-approval` to turn green, then merge normally — no bypass checkbox.

> The phrase must be its own comment and must carry the **current head SHA**. Pushing another
> commit invalidates it by design; comment again with the new SHA.
