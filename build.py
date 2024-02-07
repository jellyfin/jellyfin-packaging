#!/usr/bin/env python3

# build.py - Build packages in a Docker wrapper
#
# Part of the Jellyfin CI system
###############################################################################

from datetime import datetime
from email.utils import format_datetime, localtime
from os import system
import os.path
from subprocess import run, PIPE
import sys

from git import Repo

try:
    target_release = sys.argv[1]
except IndexError:
    target_release = "master"

# Determine top level directory of this repository ("jellyfin-packaging")
revparse = run(["git", "rev-parse", "--show-toplevel"], stdout=PIPE)
repo_root_dir = revparse.stdout.decode().strip()

def build_package_deb(jvers, btype, barch, bvers):
    try:
        ostype = btype if btype in configurations.keys() else None
        if ostype is None:
            raise ValueError(f"{btype} is not a valid OS type in {configurations.keys()}")
        osversion = bvers if bvers in configurations[btype]['releases'] else None
        if osversion is None:
            raise ValueError(f"{bvers} is not a valid {btype} version in {configurations[btype]['releases']}")
        dockerfiles = configurations[btype]['files'][barch] if barch in configurations[btype]['files'].keys() else None
        if dockerfiles is None:
            raise ValueError(f"{barch} is not a valid {btype} {bvers} architecture in {configurations[btype]['files'].keys()}")
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    # Set the cross-gcc version
    crossgccvers = configurations[btype]['cross-gcc'][bvers]

    # Prepare the debian changelog file
    changelog_src = f"{repo_root_dir}/debian/changelog.in"
    changelog_dst = f"{repo_root_dir}/debian/changelog"

    with open(changelog_src) as fh:
        changelog = fh.read()

    if "v" in jvers:
        comment = f"Jellyfin release {jvers}, see https://github.com/jellyfin/jellyfin/releases/{jvers} for details."
    else:
        comment = f"Jellyin unstable release {jvers}."

    changelog = changelog.format(
        package_version=jvers.replace('v', ''),
        package_build=f"{btype[:3]}{bvers.replace('.', '')}",
        release_comment=comment,
        release_date=format_datetime(localtime())
    )

    with open(changelog_dst, "w") as fh:
        fh.write(changelog)

    # Build the dockerfile(s) and packages
    for dockerfile in dockerfiles:
        imagename = f"jellyfin-builder-{btype}-{barch}-{bvers}-{abs(hash(dockerfile))}"
        os.system(f"docker build --progress=plain --build-arg PTYPE={ostype} --build-arg PVERSION={osversion} --build-arg PARCH={barch} --build-arg GCC_VERSION={crossgccvers} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
        os.system(f"docker run --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out:/dist --name {imagename} {imagename}")

    # Clean up the docker containers and images
    for dockerfile in dockerfiles:
        imagename = f"jellyfin-builder-{btype}-{barch}-{bvers}-{abs(hash(dockerfile))}"
        os.system(f"docker rm {imagename}")
        os.system(f"docker image rm {imagename}")

def build_package(btype, barch, bvers):
    pass

def build_docker(ostype, osversion, dockerfiles):
    pass

# Define a map of possible configurations
configurations = {
    "debian": {
        "files": {
            "amd64": [ "debian/docker/Dockerfile" ],
            "arm64": [ "debian/docker/Dockerfile" ],
            "armhf": [ "debian/docker/Dockerfile" ],
        },
        "releases": [ "11", "12" ],
        "def": build_package_deb,
        "cross-gcc": {
            "11": "10",
            "12": "12",
        },
    },
    "ubuntu": {
        "files": {
            "amd64": [ "debian/docker/Dockerfile" ],
            "arm64": [ "debian/docker/Dockerfile" ],
            "armhf": [ "debian/docker/Dockerfile" ],
        },
        "releases": [ "20.04", "22.04" ],
        "def": build_package_deb,
        "cross-gcc": {
            "20.04": "10",
            "22.04": "12",
            "24.04": "12",
        },
    },
    "fedora": {
        "def": build_package,
    },
    "centos": {
        "def": build_package,
    },
    "linux": {
        "def": build_package,
    },
    "windows": {
        "def": build_package,
    },
    "macos": {
        "def": build_package,
    },
    "portable": {
        "def": build_package,
    },
    "docker": {
        "def": build_docker,
    },
}

def usage():
    print(f"{sys.argv[0]} JVERS BTYPE BARCH [BVERS]")
    print(f" JVERS: The Jellyfin version being built")
    print(f" BTYPE: A valid build OS type")
    print(f" BARCH: A valid build OS CPU architecture")
    print(f" BVERS: A valid build OS version (packaged OS types only)")

try:
    jvers = sys.argv[1]
    barch = sys.argv[2]
    btype = sys.argv[3]
except IndexError:
    usage()
    exit(1)
try:
    bvers = sys.argv[4]
except IndexError:
    bvers = None

configurations[btype]['def'](jvers, btype, barch, bvers)
