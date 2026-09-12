#!/usr/bin/env python3

"""Roll the release milestones forward after a stable release.

Releasing vN.M closes the vN.M milestone in every release repository, opens
vN.(M+1), and moves whatever issues and pull requests were still open on the
released milestone onto the new one.
"""

from __future__ import annotations

import os
import re
import sys

from common import ORG, REPOS, log, require_token, rest, write_summary

RELEASE_VERSION = re.compile(r"v?(\d+)\.(\d+)")

MILESTONE_TITLE = re.compile(r"(v?)(\d+)\.(\d+)")


def parse_release(version: str) -> tuple[int, int] | None:
    match = RELEASE_VERSION.fullmatch(version.strip())
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def list_milestones(repo: str) -> list[dict]:
    milestones: list[dict] = []
    page = 1
    while True:
        batch = rest(
            f"repos/{ORG}/{repo}/milestones",
            state="all",
            per_page=100,
            page=page,
        )
        milestones.extend(batch)
        if len(batch) < 100:
            return milestones
        page += 1


def find_milestone(milestones: list[dict], major: int, minor: int) -> dict | None:
    for milestone in milestones:
        match = MILESTONE_TITLE.fullmatch(milestone["title"])
        if match and (int(match.group(2)), int(match.group(3))) == (major, minor):
            return milestone
    return None


def next_title(released: dict | None, major: int, minor: int) -> str:
    if released is None:
        return f"v{major}.{minor + 1}"
    match = MILESTONE_TITLE.fullmatch(released["title"])
    prefix = match.group(1) if match else "v"
    return f"{prefix}{major}.{minor + 1}"


def open_items(repo: str, milestone_number: int) -> list[dict]:
    items: list[dict] = []
    page = 1
    while True:
        batch = rest(
            f"repos/{ORG}/{repo}/issues",
            milestone=milestone_number,
            state="open",
            per_page=100,
            page=page,
        )
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def ensure_milestone(repo: str, milestones: list[dict], title: str) -> dict:
    existing = next((m for m in milestones if m["title"] == title), None)
    if existing is None:
        log(f"  create milestone {title}")
        return rest(f"repos/{ORG}/{repo}/milestones", "POST", title=title)
    if existing["state"] == "closed":
        log(f"  reopen milestone {title}")
        return rest(
            f"repos/{ORG}/{repo}/milestones/{existing['number']}",
            "PATCH",
            state="open",
        )
    log(f"  milestone {title} already open")
    return existing


def roll_repo(repo: str, major: int, minor: int) -> tuple[str, int]:
    milestones = list_milestones(repo)
    released = find_milestone(milestones, major, minor)
    target = ensure_milestone(repo, milestones, next_title(released, major, minor))

    if released is None:
        log(f"  no milestone for v{major}.{minor}, nothing to close or move")
        return f"opened {target['title']}, no v{major}.{minor} milestone to close", 0

    moved_issues = 0
    moved_prs = 0
    failures = 0
    for item in open_items(repo, released["number"]):
        kind = "PR" if "pull_request" in item else "issue"
        log(f"  #{item['number']}: {kind} -> {target['title']}")
        try:
            rest(
                f"repos/{ORG}/{repo}/issues/{item['number']}",
                "PATCH",
                milestone=target["number"],
            )
        except RuntimeError as exc:
            log(f"  #{item['number']}: FAILED to move: {exc}")
            failures += 1
            continue
        if kind == "PR":
            moved_prs += 1
        else:
            moved_issues += 1

    log(f"  close milestone {released['title']}")
    try:
        rest(
            f"repos/{ORG}/{repo}/milestones/{released['number']}",
            "PATCH",
            state="closed",
        )
        closed = f"closed {released['title']}"
    except RuntimeError as exc:
        log(f"  FAILED to close {released['title']}: {exc}")
        failures += 1
        closed = f"could not close {released['title']}"

    detail = (
        f"{closed}, opened {target['title']}, moved {moved_issues} issues "
        f"and {moved_prs} PRs"
    )
    if failures:
        detail += f", {failures} failed"
    return detail, failures


def main() -> int:
    if not require_token():
        return 1

    version = os.environ.get("RELEASE_VERSION", "").strip()
    if not version:
        log("RELEASE_VERSION is empty: nothing to roll forward.")
        return 1

    release = parse_release(version)
    if release is None:
        log(f"{version} is not a MAJOR.MINOR version, so there is nothing to roll.")
        write_summary(
            [
                "## Milestone rollover",
                "",
                f"_Failed: `{version}` is not a MAJOR.MINOR version._",
            ]
        )
        return 1

    major, minor = release
    log(f"Rolling v{major}.{minor} forward to v{major}.{minor + 1}\n")

    summary = ["## Milestone rollover", ""]
    failures = 0
    for repo in REPOS:
        log(f"=== jellyfin/{repo} ===")
        try:
            detail, repo_failures = roll_repo(repo, major, minor)
        except RuntimeError as exc:
            log(f"  FAILED: {exc}")
            failures += 1
            summary.append(f"- **jellyfin/{repo}**: failed: {exc}")
            continue
        failures += repo_failures
        summary.append(f"- **jellyfin/{repo}**: {detail}")
        log("")

    write_summary(summary)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
