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

# Base Docker commands
docker_build_cmd = "docker build --progress=plain --no-cache"
docker_run_cmd = "docker run --rm"

def build_package_deb(jvers, btype, barch, bvers):
    try:
        ostype = btype if btype in configurations.keys() else None
        if ostype is None:
            raise ValueError(f"{btype} is not a valid OS type in {configurations.keys()}")
        osversion = bvers if bvers in configurations[btype]['releases'] else None
        if osversion is None:
            raise ValueError(f"{bvers} is not a valid {btype} version in {configurations[btype]['releases']}")
        PARCH = configurations[btype]['archmaps'][barch]['PARCH'] if barch in configurations[btype]['archmaps'].keys() else None
        if PARCH is None:
            raise ValueError(f"{barch} is not a valid {btype} {bvers} architecture in {configurations[btype]['archmaps'].keys()}")
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    # Set the dockerfile
    dockerfile = configurations[btype]["dockerfile"]

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
    jvers = jvers.replace('v', '')

    changelog = changelog.format(
        package_version=jvers,
        package_build=f"{btype[:3]}{bvers.replace('.', '')}",
        release_comment=comment,
        release_date=format_datetime(localtime())
    )

    with open(changelog_dst, "w") as fh:
        fh.write(changelog)

    # Use a unique docker image name for consistency
    imagename = f"{configurations[btype]['imagename']}-{jvers}_{barch}-{btype}-{bvers}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --build-arg PTYPE={ostype} --build-arg PVERSION={osversion} --build-arg PARCH={PARCH} --build-arg GCC_VERSION={crossgccvers} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{btype}:/dist --name {imagename} {imagename}")


def build_package_rpm(jvers, btype, barch, bvers):
    pass


def build_linux(jvers, btype, barch, _bvers):
    try:
        PARCH = configurations[btype]['archmaps'][barch]['PARCH'] if barch in configurations[btype]['archmaps'].keys() else None
        if PARCH is None:
            raise ValueError(f"{barch} is not a valid {btype} {bvers} architecture in {configurations[btype]['archmaps'].keys()}")
        DARCH = configurations[btype]['archmaps'][barch]['DARCH']
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jvers = jvers.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[btype]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[btype]['imagename']}-{jvers}_{barch}-{btype}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[btype]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{btype}:/dist --env JVERS={jvers} --env BTYPE={btype} --env PARCH={PARCH} --env DTYPE=linux --env DARCH={DARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_windows(jvers, btype, _barch, _bvers):
    try:
        PARCH = configurations[btype]['archmaps'][barch]['PARCH'] if barch in configurations[btype]['archmaps'].keys() else None
        if PARCH is None:
            raise ValueError(f"{barch} is not a valid {btype} {bvers} architecture in {configurations[btype]['archmaps'].keys()}")
        DARCH = configurations[btype]['archmaps'][barch]['DARCH']
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jvers = jvers.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[btype]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[btype]['imagename']}-{jvers}_{barch}-{btype}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[btype]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{btype}:/dist --env JVERS={jvers} --env BTYPE={btype} --env PARCH={PARCH} --env DTYPE=win --env DARCH={DARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")




def build_macos(jvers, btype, barch, _bvers):
    try:
        PARCH = configurations[btype]['archmaps'][barch]['PARCH'] if barch in configurations[btype]['archmaps'].keys() else None
        if PARCH is None:
            raise ValueError(f"{barch} is not a valid {btype} {bvers} architecture in {configurations[btype]['archmaps'].keys()}")
        DARCH = configurations[btype]['archmaps'][barch]['DARCH']
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jvers = jvers.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[btype]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[btype]['imagename']}-{jvers}_{barch}-{btype}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[btype]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{btype}:/dist --env JVERS={jvers} --env BTYPE={btype} --env PARCH={PARCH} --env DTYPE=osx --env DARCH={DARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_portable(jvers, btype, _barch, _bvers):
    jvers = jvers.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[btype]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[btype]['imagename']}-{jvers}_{btype}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[btype]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{btype}:/dist --env JVERS={jvers} --env BTYPE={btype} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_docker(jvers, btype, _barch, _bvers):
    print("> Building Docker images...")
    print()

    # We build all architectures simultaneously to push a single tag, so no conditional checks
    architectures = configurations['docker']['archmaps'].keys()

    # Set the dockerfile
    dockerfile = configurations[btype]["dockerfile"]

    # Determine if this is a "latest"-type image (v in jvers) or not
    if "v" in jvers:
        is_latest = True
        version_suffix = True
    else:
        is_latest = False
        version_suffix = False

    jvers = jvers.replace('v', '')

    # Set today's date in a convenient format for use as an image suffix
    date = datetime.now().strftime("%Y%m%d-%H%M%S")

    images = list()
    for _barch in architectures:
        print(f">> Building Docker image for {_barch}...")
        print()

        # Get our ARCH variables from the archmaps
        PARCH = configurations['docker']['archmaps'][_barch]['PARCH']
        DARCH = configurations['docker']['archmaps'][_barch]['DARCH']
        QARCH = configurations['docker']['archmaps'][_barch]['QARCH']
        BARCH = configurations['docker']['archmaps'][_barch]['BARCH']

        # Use a unique docker image name for consistency
        if version_suffix:
            imagename = f"{configurations['docker']['imagename']}:{jvers}-{_barch}.{date}"
        else:
            imagename = f"{configurations['docker']['imagename']}:{jvers}-{_barch}"

        # Clean up any existing qemu static image
        os.system(f"{docker_run_cmd} --privileged multiarch/qemu-user-static:register --reset")
        print()

        # Build the dockerfile
        os.system(f"{docker_build_cmd} --build-arg PARCH={PARCH} --build-arg DARCH={DARCH} --build-arg QARCH={QARCH} --build-arg BARCH={BARCH} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")

        images.append(imagename)
        print()

    # Build the manifests
    print(f">> Building Docker manifests...")

    if version_suffix:
        print(f">>> Building dated version manifest...")
        os.system(f"docker manifest create --amend {configurations['docker']['imagename']}:{jvers}.{date} {' '.join(images)}") 

    print(f">>> Building version manifest...")
    os.system(f"docker manifest create --amend {configurations['docker']['imagename']}:{jvers} {' '.join(images)}") 
    if is_latest:
        print(f">>> Building latest manifest...")
        os.system(f"docker manifest create --amend {configurations['docker']['imagename']}:latest {' '.join(images)}") 


# Define a map of possible configurations
configurations = {
    "debian": {
        "def": build_package_deb,
        "dockerfile": "debian/docker/Dockerfile",
        "imagename": "jellyfin-builder",
        "archmaps": {
            "amd64": {
                "PARCH": "amd64",
            },
            "arm64": {
                "PARCH": "arm64",
            },
            "armhf": {
                "PARCH": "armhf",
            },
        },
        "releases": [
            "11",
            "12",
        ],
        "cross-gcc": {
            "11": "10",
            "12": "12",
        },
    },
    "ubuntu": {
        "def": build_package_deb,
        "dockerfile": "debian/docker/Dockerfile",
        "imagename": "jellyfin-builder",
        "archmaps": {
            "amd64": {
                "PARCH": "amd64",
            },
            "arm64": {
                "PARCH": "arm64",
            },
            "armhf": {
                "PARCH": "armhf",
            },
        },
        "releases": [
            "20.04",
            "22.04",
        ],
        "cross-gcc": {
            "20.04": "10",
            "22.04": "12",
            "24.04": "12",
        },
    },
    "fedora": {
        "def": build_package_rpm,
    },
    "centos": {
        "def": build_package_rpm,
    },
    "linux": {
        "def": build_linux,
        "dockerfile": "portable/Dockerfile",
        "imagename": "jellyfin-builder",
        "archivetypes": "tar",
        "archmaps": {
            "amd64": {
                "PARCH": "amd64",
                "DARCH": "x64",
            },
            "amd64-musl": {
                "PARCH": "amd64-musl",
                "DARCH": "musl-x64",
            },
            "arm64": {
                "PARCH": "arm64",
                "DARCH": "arm64",
            },
            "arm64-musl": {
                "PARCH": "arm64-musl",
                "DARCH": "musl-arm64",
            },
            "armhf": {
                "PARCH": "armhf",
                "DARCH": "arm",
            },
        },
    },
    "windows": {
        "def": build_windows,
        "dockerfile": "portable/Dockerfile",
        "imagename": "jellyfin-builder",
        "archivetypes": "zip",
        "archmaps": {
            "amd64": {
                "PARCH": "amd64",
                "DARCH": "x64",
            },
            "arm64": {
                "PARCH": "arm64",
                "DARCH": "arm64",
            },
        },
    },
    "macos": {
        "def": build_macos,
        "dockerfile": "portable/Dockerfile",
        "imagename": "jellyfin-builder",
        "archivetypes": "tar",
        "archmaps": {
            "amd64": {
                "PARCH": "amd64",
                "DARCH": "x64",
            },
            "arm64": {
                "PARCH": "arm64",
                "DARCH": "arm64",
            },
        },
    },
    "portable": {
        "def": build_portable,
        "dockerfile": "portable/Dockerfile",
        "imagename": "jellyfin-builder",
        "archivetypes": "tar,zip",
    },
    "docker": {
        "def": build_docker,
        "dockerfile": "docker/Dockerfile",
        "imagename": "jellyfin/jellyfin",
        "archmaps": {
            "amd64": {
                "PARCH": "amd64",
                "DARCH": "x64",
                "QARCH": "x86_64",
                "BARCH": "amd64",
            },
            "arm64": {
                "PARCH": "arm64",
                "DARCH": "arm64",
                "QARCH": "aarch64",
                "BARCH": "arm64v8",
            },
            "armhf": {
                "PARCH": "armhf",
                "DARCH": "arm",
                "QARCH": "arm",
                "BARCH": "arm32v7",
            },
        }
    },
}

def usage():
    print(f"{sys.argv[0]} JVERS BTYPE [BARCH] [BVERS]")
    print(f" JVERS: The Jellyfin version being built; stable releases should be tag names with a 'v' e.g. v10.9.0")
    print(f" BTYPE: A valid build OS type (debian, ubuntu, fedora, centos, docker, portable, linux, windows, macos)")
    print(f" BARCH: A valid build OS CPU architecture (empty [portable/docker], amd64, arm64, or armhf)")
    print(f" BVERS: A valid build OS version (packaged OS types only)")

try:
    jvers = sys.argv[1]
    btype = sys.argv[2]
except IndexError:
    usage()
    exit(1)
try:
    barch = sys.argv[3]
except IndexError:
    barch = None
try:
    bvers = sys.argv[4]
except IndexError:
    bvers = None

configurations[btype]['def'](jvers, btype, barch, bvers)
