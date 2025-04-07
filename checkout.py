#!/usr/bin/env python3

# checkout.py - Checkout submodules for a build (checkout a given tag or head)
#
# Part of the Jellyfin CI system
###############################################################################

from datetime import datetime
from subprocess import run, PIPE
import sys

from git import Repo

try:
    target_release = sys.argv[1]
except IndexError:
    target_release = "master"

print(f"Preparing targets for {target_release}")

# Determine top level directory of this repository ("jellyfin-packaging")
revparse = run(["git", "rev-parse", "--show-toplevel"], stdout=PIPE)
revparse_dir = revparse.stdout.decode().strip()

# Prepare repo object for this repository
this_repo = Repo(revparse_dir)

# Update all the submodules
while True:
    try:
        this_repo.submodule_update(init=True, recursive=True)
        break
    except Exception as e:
        print(e)
        pass

# Prepare a dictionary form of the submodules so we can reference them by name
submodules = dict()
for submodule in this_repo.submodules:
    submodules[submodule.name] = submodule.module()

# Validate that the provided tag is valid; if not, fall back to "master"
if target_release != "master":
    if (
        target_release not in submodules["jellyfin-server"].tags
        or target_release not in submodules["jellyfin-web"].tags
    ):
        print(
            f"WARNING: Provided tag {target_release} is not a valid tag for both jellyfin-server and jellyfin-web; using master instead"
        )
        target_release = "master"

for submodule in submodules.keys():
    if target_release == "master" or submodule == 'jellyfin-server-windows':
        target_head = "origin/master"
    else:
        target_head = f"refs/tags/{target_release}"
    # Checkout the given head and reset the working tree
    submodules[submodule].head.reference = target_head
    submodules[submodule].head.reset(index=True, working_tree=True)
    sha = submodules[submodule].head.object.hexsha
    author = submodules[submodule].head.object.author.name
    summary = submodules[submodule].head.object.summary
    date = datetime.fromtimestamp(submodules[submodule].head.object.committed_date)
    print(f"Submodule {submodule} now at {target_head} (\"{summary}\" commit {sha} by {author} @ {date})")

print(f"Successfully checked out submodules to ref {target_release}")
