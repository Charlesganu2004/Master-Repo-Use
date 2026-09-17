#!/usr/bin/env bash
# Append one row to the security trail on automation/security-trail, never on main.
#
#   bash scripts/record_trail_row.sh --action deep-scan-rotation --scope "..." \
#       --outcome "..." --approval "..." --budget "303 of 3000 minutes"
#
# Arguments pass straight through to scripts/security_trail.py. Set TRAIL_SUBJECT
# for the commit subject.
#
# The row is appended to the branch's own copy of docs/SECURITY-TRAIL.md, so rows
# accumulate run after run, as an append-only trail must. The steps this replaces
# pushed "main plus this run's row" over the branch, which erased the previous
# run's row every week, and pushed with a bare --force-with-lease, which git refuses
# as stale in a single-branch checkout, so every run after the first recorded
# nothing. This pushes a fast-forward and never forces. When another run pushes
# first, it starts again from the new tip.
set -euo pipefail

branch=automation/security-trail
root="$(git rev-parse --show-toplevel)"
author_name="${TRAIL_AUTHOR_NAME:-Charles Ganu}"
author_email="${TRAIL_AUTHOR_EMAIL:-charlesganu2004@gmail.com}"
work=""

cleanup() {
  if [[ -n "$work" ]]; then
    git -C "$root" worktree remove --force "$work" >/dev/null 2>&1 || true
    rm -rf "$work"
  fi
}
trap cleanup EXIT

for attempt in 1 2 3; do
  cleanup
  work="$(mktemp -d)"
  rmdir "$work"   # git worktree add wants to create the directory itself
  if git -C "$root" fetch --quiet --depth=1 origin \
       "+refs/heads/$branch:refs/remotes/origin/$branch" 2>/dev/null; then
    base="refs/remotes/origin/$branch"
  elif git -C "$root" rev-parse --verify --quiet refs/remotes/origin/main >/dev/null; then
    # First row ever: start the branch from main, not from whatever this job has
    # checked out, which in approved maintenance is the removal proposal.
    base="refs/remotes/origin/main"
  else
    base="HEAD"
  fi
  git -C "$root" worktree add --quiet --detach "$work" "$base"
  python "$root/scripts/security_trail.py" --file "$work/docs/SECURITY-TRAIL.md" "$@"
  git -C "$work" add docs/SECURITY-TRAIL.md
  git -C "$work" -c user.name="$author_name" -c user.email="$author_email" \
    commit --quiet -m "trail: ${TRAIL_SUBJECT:-security trail row}"
  if git -C "$work" push --quiet origin "HEAD:refs/heads/$branch"; then
    echo "recorded on $branch"
    exit 0
  fi
  echo "another run updated $branch first (attempt $attempt); appending again from its new tip" >&2
done

echo "could not record the trail row after 3 attempts" >&2
exit 1
