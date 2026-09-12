"""Shared configuration and GitHub helpers for the release automation scripts."""

from __future__ import annotations

import json
import os
import subprocess
import sys

ORG = "jellyfin"

REPOS = ["jellyfin", "jellyfin-web"]


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


def rest(path: str, method: str = "GET", **fields: object) -> object:
    args = ["gh", "api", path]
    if method != "GET":
        args.extend(["-X", method])
    for key, value in fields.items():
        args.extend(["-F", f"{key}={value}"])
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def require_token() -> bool:
    if os.environ.get("GH_TOKEN", "").strip():
        return True
    log(
        "GH_TOKEN is empty: the app token step did not produce a token.\n"
        "Check that PROJECT_AUTOMATION_CLIENT_ID and PROJECT_AUTOMATION_KEY are set "
        "and that the app is installed on the organization."
    )
    return False


def write_summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

