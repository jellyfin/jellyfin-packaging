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
from yaml import load, SafeLoader

from git import Repo

# Determine top level directory of this repository ("jellyfin-packaging")
revparse = run(["git", "rev-parse", "--show-toplevel"], stdout=PIPE)
repo_root_dir = revparse.stdout.decode().strip()

# Base Docker commands
docker_build_cmd = "docker build --progress=plain --no-cache"
docker_run_cmd = "docker run --rm"

def build_package_deb(jellyfin_version, build_type, build_arch, build_version):
    try:
        os_type = build_type if build_type in configurations.keys() else None
        if os_type is None:
            raise ValueError(f"{build_type} is not a valid OS type in {configurations.keys()}")
        os_version = configurations[build_type]['releases'][build_version] if build_version in configurations[build_type]['releases'].keys() else None
        if os_version is None:
            raise ValueError(f"{build_version} is not a valid {build_type} version in {configurations[build_type]['releases'].keys()}")
        PACKAGE_ARCH = configurations[build_type]['archmaps'][build_arch]['PACKAGE_ARCH'] if build_arch in configurations[build_type]['archmaps'].keys() else None
        if PACKAGE_ARCH is None:
            raise ValueError(f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}")
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Set the cross-gcc version
    crossgccvers = configurations[build_type]['cross-gcc'][build_version]

    # Prepare the debian changelog file
    changelog_src = f"{repo_root_dir}/debian/changelog.in"
    changelog_dst = f"{repo_root_dir}/debian/changelog"

    with open(changelog_src) as fh:
        changelog = fh.read()

    if "v" in jellyfin_version:
        comment = f"Jellyfin release {jellyfin_version}, see https://github.com/jellyfin/jellyfin/releases/{jellyfin_version} for details."
    else:
        comment = f"Jellyin unstable release {jellyfin_version}."
    jellyfin_version = jellyfin_version.replace('v', '')

    changelog = changelog.format(
        package_version=jellyfin_version,
        package_build=f"{build_type[:3]}{os_version.replace('.', '')}",
        release_comment=comment,
        release_date=format_datetime(localtime())
    )

    with open(changelog_dst, "w") as fh:
        fh.write(changelog)

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}-{build_version}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --build-arg PACKAGE_TYPE={os_type} --build-arg PACKAGE_VERSION={os_version} --build-arg PACKAGE_ARCH={PACKAGE_ARCH} --build-arg GCC_VERSION={crossgccvers} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --name {imagename} {imagename}")


def build_package_rpm(jellyfin_version, build_type, build_arch, build_version):
    pass


def build_linux(jellyfin_version, build_type, build_arch, _build_version):
    try:
        PACKAGE_ARCH = configurations[build_type]['archmaps'][build_arch]['PACKAGE_ARCH'] if build_arch in configurations[build_type]['archmaps'].keys() else None
        if PACKAGE_ARCH is None:
            raise ValueError(f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}")
        DOTNET_ARCH = configurations[build_type]['archmaps'][build_arch]['DOTNET_ARCH']
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jellyfin_version = jellyfin_version.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env PACKAGE_ARCH={PACKAGE_ARCH} --env DOTNET_TYPE=linux --env DOTNET_ARCH={DOTNET_ARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_windows(jellyfin_version, build_type, _build_arch, _build_version):
    try:
        PACKAGE_ARCH = configurations[build_type]['archmaps'][build_arch]['PACKAGE_ARCH'] if build_arch in configurations[build_type]['archmaps'].keys() else None
        if PACKAGE_ARCH is None:
            raise ValueError(f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}")
        DOTNET_ARCH = configurations[build_type]['archmaps'][build_arch]['DOTNET_ARCH']
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jellyfin_version = jellyfin_version.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env PACKAGE_ARCH={PACKAGE_ARCH} --env DOTNET_TYPE=win --env DOTNET_ARCH={DOTNET_ARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_macos(jellyfin_version, build_type, build_arch, _build_version):
    try:
        PACKAGE_ARCH = configurations[build_type]['archmaps'][build_arch]['PACKAGE_ARCH'] if build_arch in configurations[build_type]['archmaps'].keys() else None
        if PACKAGE_ARCH is None:
            raise ValueError(f"{build_arch} is not a valid {build_type} {build_version} architecture in {configurations[build_type]['archmaps'].keys()}")
        DOTNET_ARCH = configurations[build_type]['archmaps'][build_arch]['DOTNET_ARCH']
    except Exception as e:
        print(f"Invalid/unsupported arguments: {e}")
        exit(1)

    jellyfin_version = jellyfin_version.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_arch}-{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env PACKAGE_ARCH={PACKAGE_ARCH} --env DOTNET_TYPE=osx --env DOTNET_ARCH={DOTNET_ARCH} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_portable(jellyfin_version, build_type, _build_arch, _build_version):
    jellyfin_version = jellyfin_version.replace('v', '')

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Use a unique docker image name for consistency
    imagename = f"{configurations[build_type]['imagename']}-{jellyfin_version}_{build_type}"

    # Set the archive type (tar-gz or zip)
    archivetypes = f"{configurations[build_type]['archivetypes']}"

    # Build the dockerfile and packages
    os.system(f"{docker_build_cmd} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")
    os.system(f"{docker_run_cmd} --volume {repo_root_dir}:/jellyfin --volume {repo_root_dir}/out/{build_type}:/dist --env JELLYFIN_VERSION={jellyfin_version} --env BUILD_TYPE={build_type} --env ARCHIVE_TYPES={archivetypes} --name {imagename} {imagename}")


def build_docker(jellyfin_version, build_type, _build_arch, _build_version):
    print("> Building Docker images...")
    print()

    # We build all architectures simultaneously to push a single tag, so no conditional checks
    architectures = configurations['docker']['archmaps'].keys()

    # Set the dockerfile
    dockerfile = configurations[build_type]["dockerfile"]

    # Determine if this is a "latest"-type image (v in jellyfin_version) or not
    if "v" in jellyfin_version:
        is_latest = True
        version_suffix = True
    else:
        is_latest = False
        version_suffix = False

    jellyfin_version = jellyfin_version.replace('v', '')

    # Set today's date in a convenient format for use as an image suffix
    date = datetime.now().strftime("%Y%m%d-%H%M%S")

    images = list()
    for _build_arch in architectures:
        print(f">> Building Docker image for {_build_arch}...")
        print()

        # Get our ARCH variables from the archmaps
        PACKAGE_ARCH = configurations['docker']['archmaps'][_build_arch]['PACKAGE_ARCH']
        DOTNET_ARCH = configurations['docker']['archmaps'][_build_arch]['DOTNET_ARCH']
        QEMU_ARCH = configurations['docker']['archmaps'][_build_arch]['QEMU_ARCH']
        IMAGE_ARCH = configurations['docker']['archmaps'][_build_arch]['IMAGE_ARCH']

        # Use a unique docker image name for consistency
        if version_suffix:
            imagename = f"{configurations['docker']['imagename']}:{jellyfin_version}-{_build_arch}.{date}"
        else:
            imagename = f"{configurations['docker']['imagename']}:{jellyfin_version}-{_build_arch}"

        # Clean up any existing qemu static image
        os.system(f"{docker_run_cmd} --privileged multiarch/qemu-user-static:register --reset")
        print()

        # Build the dockerfile
        os.system(f"{docker_build_cmd} --build-arg PACKAGE_ARCH={PACKAGE_ARCH} --build-arg DOTNET_ARCH={DOTNET_ARCH} --build-arg QEMU_ARCH={QEMU_ARCH} --build-arg IMAGE_ARCH={IMAGE_ARCH} --build-arg JELLYFIN_VERSION={jellyfin_version} --file {repo_root_dir}/{dockerfile} --tag {imagename} {repo_root_dir}")

        images.append(imagename)
        print()

    # Build the manifests
    print(f">> Building Docker manifests...")
    manifests = list()

    if version_suffix:
        print(f">>> Building dated version manifest...")
        os.system(f"docker manifest create --amend {configurations['docker']['imagename']}:{jellyfin_version}.{date} {' '.join(images)}") 
        manifests.append(f"{configurations['docker']['imagename']}:{jellyfin_version}.{date}")

    print(f">>> Building version manifest...")
    os.system(f"docker manifest create --amend {configurations['docker']['imagename']}:{jellyfin_version} {' '.join(images)}") 
    manifests.append(f"{configurations['docker']['imagename']}:{jellyfin_version}")

    if is_latest:
        print(f">>> Building latest manifest...")
        os.system(f"docker manifest create --amend {configurations['docker']['imagename']}:latest {' '.join(images)}") 
        manifests.append(f"{configurations['docker']['imagename']}:latest")

    # Push the images and manifests to DockerHub (we are already logged in from GH Actions)
    for image in images:
        os.system(f"docker push {image}")
    for manifest in manifests:
        os.system(f"docker manifest push --purge {manifest}")

    # Push the images and manifests to GHCR (we are already logged in from GH Actions)
    for image in images:
        os.system(f"docker push ghcr.io/{image}")
    for manifest in manifests:
        os.system(f"docker manifest push --purge ghcr.io/{manifest}")


# Define a map of possible configurations
function_definitions = {
    "build_package_deb": build_package_deb,
    "build_package_rpm": build_package_rpm,
    "build_portable": build_portable,
    "build_linux": build_linux,
    "build_windows": build_windows,
    "build_macos": build_macos,
    "build_portable": build_portable,
    "build_docker": build_docker,
}

def usage():
    print(f"{sys.argv[0]} JELLYFIN_VERSION BUILD_TYPE [BUILD_ARCH] [BUILD_VERSION]")
    print(f" JELLYFIN_VERSION: The Jellyfin version being built; stable releases should be tag names with a 'v' e.g. v10.9.0")
    print(f" BUILD_TYPE: A valid build OS type (debian, ubuntu, fedora, centos, docker, portable, linux, windows, macos)")
    print(f" BUILD_ARCH: A valid build OS CPU architecture (empty [portable/docker], amd64, arm64, or armhf)")
    print(f" BUILD_VERSION: A valid build OS version (packaged OS types only)")

try:
    with open("build.yaml") as fh:
        configurations = load(fh, Loader=SafeLoader)
except Exception as e:
    print(f"Error: Failed to find 'build.yaml' configuration: {e}")
    exit(1)

try:
    jellyfin_version = sys.argv[1]
    build_type = sys.argv[2]
except IndexError:
    usage()
    exit(1)

if build_type not in configurations.keys():
    print(f"Error: The specified build type {build_type} is not valid: choices are: {', '.join(configurations.keys())}")
    exit(1)

try:
    if configurations[build_type]['build_function'] not in function_definitions.keys():
        raise ValueError
except Exception:
    print(f"Error: The specified build type {build_type} does not define a valid build function in this script.")
    exit(1)

try:
    build_arch = sys.argv[3]
except IndexError:
    build_arch = None

try:
    build_version = sys.argv[4]
except IndexError:
    build_version = None

if jellyfin_version == "master":
    jellyfin_version = datetime.now().strftime("%Y%m%d%H")
    print(f"Autocorrecting 'master' version to {jellyfin_version}")

function_definitions[configurations[build_type]['build_function']](jellyfin_version, build_type, build_arch, build_version)
