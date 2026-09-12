#!/usr/bin/env python3

"""Reconcile the Jellyfin release project boards from open pull requests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ORG = "jellyfin"

# Repository -> how many approvals a PR needs before it counts as Approved.
REPOS = {"jellyfin": 2, "jellyfin-web": 1}

# The status columns this script sets, in order.
PROGRESSION = ["Todo", "Review", "Approved"]

# Matches board titles like "Jellyfin 13". Titles with a minor version, such as
# "Jellyfin 10.11", do not match, so the script never touches those boards.
RELEASE_BOARD = re.compile(r"Jellyfin \d+")

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
        reviews(last: 100) { nodes { state author { login } } }
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


ARCHIVE_ITEM_MUTATION = """
mutation($p: ID!, $i: ID!) {
  archiveProjectV2Item(input: { projectId: $p, itemId: $i }) {
    item { id }
  }
}
"""


class GraphQLError(RuntimeError):
    def __init__(self, message: str, errors: list[dict]) -> None:
        super().__init__(message)
        self.errors = errors


def log(message: str) -> None:
    print(message, file=sys.stderr)


def gql(query: str, **variables: object) -> dict:
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        flag = "-F" if isinstance(value, (bool, int)) else "-f"
        args.extend([flag, f"{key}={value}"])
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api graphql failed: {proc.stderr.strip()}")
    payload = json.loads(proc.stdout)
    if "errors" in payload:
        raise GraphQLError(
            "; ".join(e.get("message", "?") for e in payload["errors"]),
            payload["errors"],
        )
    return payload["data"]


def require_token() -> bool:
    if os.environ.get("GH_TOKEN", "").strip():
        return True
    log(
        "GH_TOKEN is empty: the app token step did not produce a token.\n"
        "Check that PROJECT_AUTOMATION_APP_ID and PROJECT_AUTOMATION_KEY are set "
        "and that the app is installed on the organization."
    )
    return False


def list_projects() -> list[dict]:
    return gql(PROJECTS_QUERY, owner=ORG)["organization"]["projectsV2"]["nodes"]


def resolve_target_title(base_ref: str, projects: list[dict]) -> str | None:
    if base_ref == "master":
        majors = [
            int(m.group(1))
            for p in projects
            if (m := re.fullmatch(r"Jellyfin (\d+)(?:\.\d+)?", p["title"]))
        ]
        return f"Jellyfin {max(majors)}" if majors else None

    match = re.fullmatch(r"release-(\d+)(?:\.\d+)?\.z", base_ref)
    return f"Jellyfin {match.group(1)}" if match else None


def get_status_field(project_id: str) -> tuple[str, dict[str, str]]:
    field = gql(STATUS_FIELD_QUERY, id=project_id)["node"]["field"]
    if field is None:
        raise RuntimeError("Status field not found on project")
    return field["id"], {o["name"]: o["id"] for o in field["options"]}


def iter_open_pull_requests(repo: str):
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


def approving_reviewers(pr: dict) -> int:
    latest: dict[str, str] = {}
    for review in reversed(pr["reviews"]["nodes"]):
        author = review.get("author")
        if author is None:
            continue
        latest.setdefault(author["login"], review["state"])
    return sum(state == "APPROVED" for state in latest.values())


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


# Archiving keeps the card and its field values, and can be undone. Deleting cannot.
def archive_item(project_id: str, item_id: str) -> None:
    gql(ARCHIVE_ITEM_MUTATION, p=project_id, i=item_id)


def reconcile_target(
    pr: dict,
    project_id: str,
    field_id: str,
    options: dict[str, str],
    required: int,
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

    wanted = "Approved" if approving_reviewers(pr) >= required else "Review"
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


def write_summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    if not require_token():
        return 1

    dry_run = os.environ.get("DRY_RUN", "").strip().lower() in {"1", "true", "yes"}
    if dry_run:
        log("DRY RUN: no changes will be written.\n")

    projects = list_projects()
    project_ids = {p["title"]: p["id"] for p in projects}
    board_titles = {p["id"]: p["title"] for p in projects}
    release_boards = {
        p["id"] for p in projects if RELEASE_BOARD.fullmatch(p["title"])
    }
    boards: dict[str, tuple[str, dict[str, str]]] = {}

    summary = ["## Project board reconciliation", ""]
    if dry_run:
        summary.append("_Dry run - nothing was written._")
        summary.append("")

    failures = 0

    for repo, required in REPOS.items():
        counts = {
            "moved": 0,
            "added": 0,
            "archived": 0,
            "ok": 0,
            "skipped": 0,
            "failed": 0,
        }
        log(f"=== jellyfin/{repo} (needs {required} approval(s)) ===")

        for pr in iter_open_pull_requests(repo):
            number = pr["number"]
            title = resolve_target_title(pr["baseRefName"], projects)
            project_id = project_ids.get(title) if title else None
            if project_id is None:
                counts["skipped"] += 1
                continue

            if project_id not in boards:
                boards[project_id] = get_status_field(project_id)
            field_id, options = boards[project_id]

            counts[
                reconcile_target(
                    pr, project_id, field_id, options, required, title, dry_run
                )
            ] += 1

            # Remove the PR from any release board that is no longer the right one.
            for other in pr["projectItems"]["nodes"]:
                other_id = other["project"]["id"]
                if other_id == project_id or other_id not in release_boards:
                    continue
                value = other["fieldValueByName"]
                status = value["name"] if value else None
                if status is not None and status not in PROGRESSION:
                    continue

                log(f"  #{number}: archive from {board_titles[other_id]}")
                if dry_run:
                    counts["archived"] += 1
                    continue
                try:
                    archive_item(other_id, other["id"])
                    counts["archived"] += 1
                except (RuntimeError, GraphQLError) as exc:
                    log(f"  #{number}: FAILED to archive: {exc}")
                    counts["failed"] += 1

        failures += counts["failed"]
        log(f"  {counts}\n")
        summary.append(
            f"- **jellyfin/{repo}**: {counts['added']} added, "
            f"{counts['moved']} moved, {counts['archived']} archived, "
            f"{counts['ok']} already correct, "
            f"{counts['skipped']} skipped, {counts['failed']} failed"
        )

    write_summary(summary)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
