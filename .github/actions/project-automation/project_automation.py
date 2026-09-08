#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ORG = "jellyfin"
DEFAULT_APPROVALS = 2

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

PULL_REQUEST_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      id
      closingIssuesReferences(first: 20) { nodes { number } }
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

REVIEWS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviews(last: 100) { nodes { state author { login } } }
    }
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
        args.extend(["-F", f"{key}={value}"])
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


def list_projects() -> list[dict]:
    return gql(PROJECTS_QUERY, owner=ORG)["organization"]["projectsV2"]["nodes"]


def resolve_target_title(base_ref: str, projects: list[dict]) -> str | None:
    if base_ref == "master":
        majors = [
            int(m.group(1))
            for p in projects
            if (m := re.fullmatch(r"Jellyfin (\d+)\.\d+", p["title"]))
        ]
        return f"Jellyfin {max(majors)}.0" if majors else None

    match = re.fullmatch(r"release-(\d+)(?:\.\d+)?\.z", base_ref)
    return f"Jellyfin {match.group(1)}.0" if match else None


def get_status_field(project_id: str) -> tuple[str, dict[str, str]]:
    field = gql(STATUS_FIELD_QUERY, id=project_id)["node"]["field"]
    if field is None:
        raise RuntimeError("Status field not found on project")
    options = {o["name"]: o["id"] for o in field["options"]}
    return field["id"], options


def get_pull_request(repo: str, number: int) -> dict:
    return gql(PULL_REQUEST_QUERY, owner=ORG, repo=repo, number=number)["repository"][
        "pullRequest"
    ]


def get_item_id(
    repo: str, number: int, project_id: str, *, issue: bool = False
) -> str | None:
    kind = "issue" if issue else "pullRequest"
    query = f"""
      query($owner: String!, $repo: String!, $number: Int!) {{
        repository(owner: $owner, name: $repo) {{
          {kind}(number: $number) {{
            projectItems(first: 20) {{ nodes {{ id project {{ id }} }} }}
          }}
        }}
      }}
    """
    node = gql(query, owner=ORG, repo=repo, number=number)["repository"][kind]
    return next(
        (
            i["id"]
            for i in node["projectItems"]["nodes"]
            if i["project"]["id"] == project_id
        ),
        None,
    )


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


def current_approving_reviewers(repo: str, number: int) -> int:
    reviews = gql(REVIEWS_QUERY, owner=ORG, repo=repo, number=number)["repository"][
        "pullRequest"
    ]["reviews"]["nodes"]
    latest: dict[str, str] = {}
    for review in reversed(reviews):
        latest.setdefault(review["author"]["login"], review["state"])
    return sum(state == "APPROVED" for state in latest.values())


def parse_approvals(raw: str | None) -> int:
    try:
        return max(0, int(raw or DEFAULT_APPROVALS))
    except ValueError:
        return DEFAULT_APPROVALS


def main() -> int:
    event_name = os.environ["EVENT_NAME"]
    repo = os.environ["REPO"]
    base_ref = os.environ["BASE_REF"]
    pr_number = int(os.environ["PR_NUMBER"])
    merged = os.environ.get("PR_MERGED", "false") == "true"
    required_approvals = parse_approvals(os.environ.get("REQUIRED_APPROVALS"))

    # Find the project board for this branch.
    projects = list_projects()
    title = resolve_target_title(base_ref, projects)
    if title is None:
        log(f"Unmanaged base branch '{base_ref}'.")
        return 0

    project_id = next((p["id"] for p in projects if p["title"] == title), None)
    if project_id is None:
        log(f"No project titled '{title}'.")
        return 0

    # Get the project's Status field and its column ids.
    field_id, options = get_status_field(project_id)
    pr = get_pull_request(repo, pr_number)

    # When a PR is merged, move it and its closed issues to Done.
    if event_name == "pull_request_target":
        if not merged:
            return 0
        item_id = get_item_id(repo, pr_number, project_id)
        if item_id is not None:
            set_status(project_id, item_id, field_id, options["Done"])
            log("Moved PR to Done.")
        for closing in pr["closingIssuesReferences"]["nodes"]:
            issue_item_id = get_item_id(repo, closing["number"], project_id, issue=True)
            if issue_item_id is not None:
                set_status(project_id, issue_item_id, field_id, options["Done"])
                log(f"Moved issue #{closing['number']} to Done.")
        return 0

    # Add the PR to the board and set it to Review.
    item_id = add_item_to_project(project_id, pr["id"]) or get_item_id(
        repo, pr_number, project_id
    )
    if item_id is None:
        log("Could not resolve project item.")
        return 1

    set_status(project_id, item_id, field_id, options["Review"])
    log("Set PR to Review.")

    # Move issues this PR closes to In Progress.
    for closing in pr["closingIssuesReferences"]["nodes"]:
        issue_item_id = get_item_id(repo, closing["number"], project_id, issue=True)
        if issue_item_id is not None and "In Progress" in options:
            set_status(project_id, issue_item_id, field_id, options["In Progress"])
            log(f"Moved issue #{closing['number']} to In Progress.")

    # Move to Approved once it has enough approvals.
    if current_approving_reviewers(repo, pr_number) >= required_approvals:
        set_status(project_id, item_id, field_id, options["Approved"])
        log("Moved PR to Approved.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
