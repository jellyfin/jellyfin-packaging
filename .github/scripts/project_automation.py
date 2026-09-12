#!/usr/bin/env python3

"""Reconcile the Jellyfin release project boards from open pull requests."""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Iterator

from common import (
    ORG,
    REPOS,
    GraphQLError,
    gql,
    log,
    require_token,
    rest,
    write_summary,
)

# The status columns this script sets, in order.
PROGRESSION = ["Todo", "Review", "Approved"]

RELEASE_BOARD = re.compile(r"Jellyfin v?(\d+)")

MILESTONE = re.compile(r"v?(\d+)(?:\.(\d+))?(?:\.\d+)?")

RELEASE_BRANCH = re.compile(r"release-(\d+)(?:\.\d+)?\.z")

PROJECTS_QUERY = """
query($owner: String!) {
  organization(login: $owner) {
    projectsV2(first: 100) {
      nodes { id title }
    }
  }
}
"""

STATUS_FIELD_QUERY = """
query($id: ID!) {
  node(id: $id) {
    ... on ProjectV2 {
      field(name: "Status") {
        ... on ProjectV2SingleSelectField {
          id
          options { id name }
        }
      }
    }
  }
}
"""

OPEN_PULL_REQUESTS_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(states: OPEN, first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        number
        baseRefName
        milestone { title }
        reviewDecision
        projectItems(first: 20) {
          nodes {
            id
            project { id }
            fieldValueByName(name: "Status") {
              ... on ProjectV2ItemFieldSingleSelectValue { name }
            }
          }
        }
      }
    }
  }
}
"""

ADD_ITEM_MUTATION = """
mutation($p: ID!, $c: ID!) {
  addProjectV2ItemById(input: { projectId: $p, contentId: $c }) {
    item { id }
  }
}
"""

SET_STATUS_MUTATION = """
mutation($p: ID!, $i: ID!, $f: ID!, $v: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $p
      itemId: $i
      fieldId: $f
      value: { singleSelectOptionId: $v }
    }
  ) {
    projectV2Item { id }
  }
}
"""


DELETE_ITEM_MUTATION = """
mutation($p: ID!, $i: ID!) {
  deleteProjectV2Item(input: { projectId: $p, itemId: $i }) {
    deletedItemId
  }
}
"""


def list_projects() -> list[dict]:
    return gql(PROJECTS_QUERY, owner=ORG)["organization"]["projectsV2"]["nodes"]


def open_milestones(repo: str) -> dict[int, dict]:
    # major version -> milestone. When a major has several open milestones the
    # lowest minor wins, because that is the one shipping next.
    best: dict[int, tuple[int, dict]] = {}
    for milestone in rest(f"repos/{ORG}/{repo}/milestones?state=open&per_page=100"):
        match = MILESTONE.fullmatch(milestone["title"])
        if match is None:
            continue
        major, minor = int(match.group(1)), int(match.group(2) or 0)
        if major not in best or minor < best[major][0]:
            best[major] = (minor, milestone)
    return {major: milestone for major, (_, milestone) in best.items()}


def set_milestone(repo: str, number: int, milestone_number: int) -> None:
    rest(f"repos/{ORG}/{repo}/issues/{number}", "PATCH", milestone=milestone_number)


def target_major(
    pr: dict, milestones: dict[int, dict], newest: int | None
) -> tuple[int | None, dict | None]:
    # Returns the major release this PR belongs to, and the milestone to apply
    # when it has none yet.
    if pr["milestone"]:
        match = MILESTONE.fullmatch(pr["milestone"]["title"])
        return (int(match.group(1)) if match else None), None

    # A PR against a release branch belongs to that release by definition.
    branch = RELEASE_BRANCH.fullmatch(pr["baseRefName"])
    if branch:
        major = int(branch.group(1))
    elif pr["baseRefName"] == "master" and pr["reviewDecision"] == "APPROVED":
        major = newest
    else:
        return None, None

    # The major stands on its own. The milestone is only what to apply, and is
    # None when the repository has no open milestone for that release yet.
    milestone = milestones.get(major) if major is not None else None
    return major, milestone


def get_status_field(project_id: str) -> tuple[str, dict[str, str]]:
    field = gql(STATUS_FIELD_QUERY, id=project_id)["node"]["field"]
    if field is None:
        raise RuntimeError("Status field not found on project")
    return field["id"], {o["name"]: o["id"] for o in field["options"]}


def iter_open_pull_requests(repo: str) -> Iterator[dict]:
    cursor = None
    while True:
        variables = {"owner": ORG, "repo": repo}
        if cursor:
            variables["cursor"] = cursor
        page = gql(OPEN_PULL_REQUESTS_QUERY, **variables)["repository"]["pullRequests"]
        yield from page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return
        cursor = page["pageInfo"]["endCursor"]


def add_item_to_project(project_id: str, content_id: str) -> str | None:
    try:
        return gql(ADD_ITEM_MUTATION, p=project_id, c=content_id)[
            "addProjectV2ItemById"
        ]["item"]["id"]
    except GraphQLError as exc:
        if all(e.get("type") == "UNPROCESSABLE" for e in exc.errors):
            log(f"Item already on board: {exc}")
            return None
        raise


def set_status(project_id: str, item_id: str, field_id: str, option_id: str) -> None:
    gql(SET_STATUS_MUTATION, p=project_id, i=item_id, f=field_id, v=option_id)


def remove_item(project_id: str, item_id: str) -> None:
    gql(DELETE_ITEM_MUTATION, p=project_id, i=item_id)


def reconcile_target(
    pr: dict,
    project_id: str,
    field_id: str,
    options: dict[str, str],
    title: str,
    dry_run: bool,
) -> str:
    number = pr["number"]
    item = next(
        (i for i in pr["projectItems"]["nodes"] if i["project"]["id"] == project_id),
        None,
    )
    value = item["fieldValueByName"] if item else None
    current = value["name"] if value else None

    wanted = "Approved" if pr["reviewDecision"] == "APPROVED" else "Review"
    if wanted not in options:
        log(f"  #{number}: board '{title}' has no '{wanted}' column")
        return "skipped"

    if current is not None and current not in PROGRESSION:
        return "skipped"

    rank = {name: i for i, name in enumerate(PROGRESSION)}
    if current is not None and rank[wanted] <= rank[current]:
        return "ok"

    origin = "add to" if item is None else f"{current or 'no status'} ->"
    log(f"  #{number}: {origin} {title} / {wanted}")
    if dry_run:
        return "added" if item is None else "moved"

    try:
        item_id = item["id"] if item else add_item_to_project(project_id, pr["id"])
        if item_id is None:
            log(f"  #{number}: could not resolve project item")
            return "failed"
        set_status(project_id, item_id, field_id, options[wanted])
        return "added" if item is None else "moved"
    except (RuntimeError, GraphQLError) as exc:
        log(f"  #{number}: FAILED: {exc}")
        return "failed"


def main() -> int:
    if not require_token():
        return 1

    dry_run = os.environ.get("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
    if dry_run:
        log("DRY RUN: no changes will be written.\n")

    projects = list_projects()
    board_titles = {p["id"]: p["title"] for p in projects}
    release_boards: dict[int, str] = {}
    for project in projects:
        match = RELEASE_BOARD.fullmatch(project["title"])
        if match:
            release_boards[int(match.group(1))] = project["id"]
    board_ids = set(release_boards.values())
    boards: dict[str, tuple[str, dict[str, str]]] = {}

    summary = ["## Project board reconciliation", ""]
    if dry_run:
        summary.append("_Dry run - nothing was written._")
        summary.append("")

    failures = 0

    for repo in REPOS:
        counts = {
            "milestoned": 0,
            "moved": 0,
            "added": 0,
            "removed": 0,
            "ok": 0,
            "skipped": 0,
            "failed": 0,
        }
        log(f"=== jellyfin/{repo} ===")
        try:
            milestones = open_milestones(repo)
        except RuntimeError as exc:
            log(f"  FAILED to read milestones: {exc}")
            failures += 1
            summary.append(f"- **jellyfin/{repo}**: could not read milestones")
            continue
        newest = max(milestones) if milestones else None
        if not milestones:
            log(f"  no open milestones in {repo}, so no PR can be routed")

        for pr in iter_open_pull_requests(repo):
            number = pr["number"]
            major, milestone = target_major(pr, milestones, newest)
            if milestone is not None:
                log(f"  #{number}: set milestone {milestone['title']}")
                if dry_run:
                    counts["milestoned"] += 1
                else:
                    try:
                        set_milestone(repo, number, milestone["number"])
                        counts["milestoned"] += 1
                    except RuntimeError as exc:
                        log(f"  #{number}: FAILED to set milestone: {exc}")
                        counts["failed"] += 1

            project_id = release_boards.get(major) if major is not None else None
            title = board_titles.get(project_id) if project_id else None

            if project_id is None:
                counts["skipped"] += 1
                if pr["milestone"]:
                    # A milestone naming no board is still a person's decision,
                    # so leave whatever cards the PR already has alone.
                    continue
            else:
                if project_id not in boards:
                    boards[project_id] = get_status_field(project_id)
                field_id, options = boards[project_id]

                counts[
                    reconcile_target(
                        pr, project_id, field_id, options, title, dry_run
                    )
                ] += 1

            # Remove the PR from every release board except the right one.
            for other in pr["projectItems"]["nodes"]:
                other_id = other["project"]["id"]
                if other_id == project_id or other_id not in board_ids:
                    continue
                value = other["fieldValueByName"]
                status = value["name"] if value else None
                if status is not None and status not in PROGRESSION:
                    continue

                log(f"  #{number}: remove from {board_titles[other_id]}")
                if dry_run:
                    counts["removed"] += 1
                    continue
                try:
                    remove_item(other_id, other["id"])
                    counts["removed"] += 1
                except (RuntimeError, GraphQLError) as exc:
                    log(f"  #{number}: FAILED to remove: {exc}")
                    counts["failed"] += 1

        failures += counts["failed"]
        log("  " + ", ".join(f"{k}={v}" for k, v in counts.items()) + "\n")
        summary.append(
            f"- **jellyfin/{repo}**: {counts['milestoned']} milestoned, "
            f"{counts['added']} added, {counts['moved']} moved, "
            f"{counts['removed']} removed, {counts['ok']} already correct, "
            f"{counts['skipped']} skipped, {counts['failed']} failed"
        )

    write_summary(summary)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
