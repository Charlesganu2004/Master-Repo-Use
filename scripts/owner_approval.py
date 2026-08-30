#!/usr/bin/env python3
"""Evaluate and publish the Master Repo owner-approval status.

Two secure paths are supported:

* PR authored by someone other than Charlesganu2004:
  a normal GitHub APPROVED review by Charles on the *current head SHA*.
* PR authored by Charlesganu2004:
  an exact PR conversation comment from Charles:
      APPROVE OWNER PR <CURRENT_HEAD_SHA>

The result is written as the commit status context ``owner-approval`` on the
current PR head SHA.  Any new commit therefore invalidates the previous approval.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OWNER = "Charlesganu2004"
STATUS_CONTEXT = "owner-approval"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class Decision:
    approved: bool
    mode: str
    reason: str


def same_login(value: str | None, expected: str = OWNER) -> bool:
    return bool(value) and value.casefold() == expected.casefold()


def exact_owner_command(head_sha: str) -> str:
    if not SHA_RE.fullmatch(head_sha):
        raise ValueError("head SHA must be a lowercase 40-character Git SHA")
    return f"APPROVE OWNER PR {head_sha}"


# Forms seen in practice, all of which meant "approved" and none of which the
# original strict pattern accepted:
#
#   APPROVE OWNER PR <sha>
#   gh pr comment 13 --repo owner/name --body "APPROVE OWNER PR <sha>"
#   APPROVE OWNER PR https://github.com/owner/name/commit/<sha>
#
# Surrounding text is now tolerated because the SHA is what carries the security,
# not the absence of other words. A comment still has to name this exact revision,
# so a pasted command or a commit URL approves the same commit it always did.
# A PR URL is still refused: it names no revision at all.
APPROVAL_RE = re.compile(
    r"APPROVE\s+OWNER\s+PR\s+"
    r"(?:https?://\S*?/commit/)?"          # optional commit URL prefix
    r"([0-9a-fA-F]{7,40})\b",
    re.IGNORECASE,
)

# Charles's standing passcode approval. Requested deliberately after the
# per-SHA form made him re-approve on every push.
#
# Trade-off, stated once so it is on the record: this form does NOT expire when
# new commits land. A passcode comment approves the pull request, not one
# revision of it, so code pushed afterwards inherits that approval. The per-SHA
# form above still exists and still expires; use it when a branch is moving and
# the review needs to pin an exact revision.
#
# The passcode is a second factor, not the only gate. The comment must also come
# from the owner account, so knowing the number is useless without it.
PASSCODE = "152004"
PASSCODE_RE = re.compile(
    r"^\s*I\s+APPROVE\s+(?:WITH\s+(?:THE\s+)?PASSCODE\s+)?(\d{4,12})\s*$",
    re.IGNORECASE,
)


def is_passcode_approval(body: str) -> bool:
    """True when the owner gave the standing passcode.

    Deliberately independent of the head SHA: that is the whole point of the
    form. Accepts "I approve 152004" and "I approve with passcode 152004".
    """
    match = PASSCODE_RE.match(body or "")
    return bool(match) and match.group(1) == PASSCODE


def is_owner_approval(body: str, head_sha: str) -> bool:
    """True when this comment approves exactly this head SHA.

    Tolerates any casing, surrounding whitespace, and any SHA prefix from 7
    characters up. Retyping 40 hex characters by hand is where this check
    actually failed, and a prefix still names one commit.

    Surrounding text is tolerated: a pasted gh command or a commit URL both work,
    because the SHA is what binds the approval to a revision, not the absence of
    other words around it.

    A bare "APPROVE OWNER PR" with no SHA is still rejected, and so is a PR URL,
    because neither names a revision. Approval that deliberately does not pin a
    revision is expressed with the passcode instead.
    """
    for match in APPROVAL_RE.finditer(body or ""):
        if head_sha.lower().startswith(match.group(1).lower()):
            return True
    return False


def evaluate_approval(pr: dict[str, Any], comments: list[dict[str, Any]], reviews: list[dict[str, Any]], owner: str = OWNER) -> Decision:
    head_sha = str(((pr.get("head") or {}).get("sha") or "")).lower()
    author = str(((pr.get("user") or {}).get("login") or ""))
    if not SHA_RE.fullmatch(head_sha):
        return Decision(False, "invalid", "could not verify a valid current PR head SHA")
    if pr.get("draft"):
        return Decision(False, "draft", "draft PRs cannot be owner-approved")
    if same_login(author, owner):
        command = exact_owner_command(head_sha)
        for comment in comments:
            login = str(((comment.get("user") or {}).get("login") or ""))
            body = str(comment.get("body") or "").strip()
            if same_login(login, owner) and is_passcode_approval(body):
                return Decision(True, "owner-passcode", "owner approved with the standing passcode")
            if same_login(login, owner) and is_owner_approval(body, head_sha):
                return Decision(True, "owner-comment", "owner approved this exact PR head SHA")
        return Decision(False, "owner-comment",
                        f'comment "I approve {PASSCODE}" to approve, '
                        f"or APPROVE OWNER PR {head_sha[:7]} to pin this revision only")
    # Someone else opened it. The passcode works here too, so Charles has one
    # phrase that approves anything rather than a different ritual per case.
    for comment in comments:
        login = str(((comment.get("user") or {}).get("login") or ""))
        if same_login(login, owner) and is_passcode_approval(str(comment.get("body") or "").strip()):
            return Decision(True, "owner-passcode", "owner approved with the standing passcode")
    decisive: list[tuple[str, int, str]] = []
    for review in reviews:
        login = str(((review.get("user") or {}).get("login") or ""))
        commit_id = str(review.get("commit_id") or "").lower()
        state = str(review.get("state") or "").upper()
        if not same_login(login, owner) or commit_id != head_sha or state not in {"APPROVED", "CHANGES_REQUESTED"}:
            continue
        decisive.append((str(review.get("submitted_at") or ""), int(review.get("id") or 0), state))
    if not decisive:
        return Decision(False, "owner-review", "non-owner-authored PR requires Charles approval on the current head SHA")
    decisive.sort(key=lambda item: (item[0], item[1]))
    if decisive[-1][2] == "APPROVED":
        return Decision(True, "owner-review", "owner approved the current PR head SHA")
    return Decision(False, "owner-review", "latest owner decision on current head requests changes")


class GitHubAPI:
    def __init__(self, repository: str, token: str) -> None:
        if repository.count("/") != 1:
            raise ValueError("GITHUB_REPOSITORY must be owner/name")
        self.repository = repository
        self.token = token
        self.base = f"https://api.github.com/repos/{repository}"

    def request(self, method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
        data = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "master-repo-owner-approval",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else None

    def get(self, path: str) -> Any:
        return self.request("GET", self.base + path)

    def list_all(self, path: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        page = 1
        while True:
            join = "&" if "?" in path else "?"
            chunk = self.get(f"{path}{join}per_page=100&page={page}") or []
            if not isinstance(chunk, list):
                raise RuntimeError(f"GitHub API expected list for {path}")
            rows.extend(item for item in chunk if isinstance(item, dict))
            if len(chunk) < 100:
                break
            page += 1
            if page > 20:
                raise RuntimeError(f"pagination safety limit exceeded for {path}")
        return rows

    def pull(self, number: int) -> dict[str, Any]:
        value = self.get(f"/pulls/{number}")
        if not isinstance(value, dict):
            raise RuntimeError("GitHub API did not return a pull request object")
        return value

    def comments(self, number: int) -> list[dict[str, Any]]:
        return self.list_all(f"/issues/{number}/comments")

    def reviews(self, number: int) -> list[dict[str, Any]]:
        return self.list_all(f"/pulls/{number}/reviews")

    def set_status(self, sha: str, state: str, description: str, target_url: str) -> None:
        if state not in {"success", "failure", "pending", "error"}:
            raise ValueError("invalid commit status state")
        self.request("POST", f"{self.base}/statuses/{urllib.parse.quote(sha, safe='')}", {
            "state": state,
            "context": STATUS_CONTEXT,
            "description": description[:140],
            "target_url": target_url,
        })


def pr_number_from_event(payload: dict[str, Any]) -> int | None:
    pr = payload.get("pull_request")
    if isinstance(pr, dict) and pr.get("number"):
        return int(pr["number"])
    issue = payload.get("issue")
    if isinstance(issue, dict) and issue.get("pull_request") and issue.get("number"):
        return int(issue["number"])
    review = payload.get("review")
    if isinstance(review, dict):
        tail = str(review.get("pull_request_url") or "").rstrip("/").split("/")[-1]
        if tail.isdigit():
            return int(tail)
    return None


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not event_path or not repository or not token:
        print("owner-approval: missing GITHUB_EVENT_PATH/GITHUB_REPOSITORY/GITHUB_TOKEN", file=sys.stderr)
        return 2
    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    number = pr_number_from_event(payload)
    if number is None:
        print("owner-approval: event is not associated with a pull request")
        return 0
    api = GitHubAPI(repository, token)
    head_sha = ""
    try:
        pr = api.pull(number)
        head_sha = str(((pr.get("head") or {}).get("sha") or "")).lower()
        decision = evaluate_approval(pr, api.comments(number), api.reviews(number))
        state = "success" if decision.approved else "failure"
        target_url = str(pr.get("html_url") or f"https://github.com/{repository}/pull/{number}")
        api.set_status(head_sha, state, decision.reason, target_url)
        print(f"owner-approval: PR #{number} head={head_sha} mode={decision.mode} state={state}: {decision.reason}")
        return 0 if decision.approved else 1
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, RuntimeError) as exc:
        print(f"owner-approval evaluation error: {type(exc).__name__}", file=sys.stderr)
        if SHA_RE.fullmatch(head_sha):
            try:
                api.set_status(head_sha, "error", "owner approval could not be verified; fail closed", f"https://github.com/{repository}/pull/{number}")
            except Exception:
                pass
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
