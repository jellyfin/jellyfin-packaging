<h1 align="center">Jellyfin Packaging</h1>
<h3 align="center">Part of Jellyfin: The Free Software Media System</h3>

---

<p align="center">
<img alt="Logo Banner" src="https://raw.githubusercontent.com/jellyfin/jellyfin-ux/master/branding/SVG/banner-logo-solid.svg?sanitize=true"/>
<br/>
<br/>
<a href="https://github.com/jellyfin/jellyfin-packaging">
<img alt="GPL 3.0 License" src="https://img.shields.io/github/license/jellyfin/jellyfin-packaging.svg"/>
</a>
<a href="https://github.com/jellyfin/jellyfin/releases">
<img alt="Current Release" src="https://img.shields.io/github/release/jellyfin/jellyfin.svg"/>
</a>
<a href="https://translate.jellyfin.org/projects/jellyfin/jellyfin-core/?utm_source=widget">
<img alt="Translation Status" src="https://translate.jellyfin.org/widgets/jellyfin/-/jellyfin-core/svg-badge.svg"/>
</a>
<a href="https://hub.docker.com/r/jellyfin/jellyfin">
<img alt="Docker Pull Count" src="https://img.shields.io/docker/pulls/jellyfin/jellyfin.svg"/>
</a>
<br/>
<a href="https://opencollective.com/jellyfin">
<img alt="Donate" src="https://img.shields.io/opencollective/all/jellyfin.svg?label=backers"/>
</a>
<a href="https://features.jellyfin.org">
<img alt="Submit Feature Requests" src="https://img.shields.io/badge/fider-vote%20on%20features-success.svg"/>
</a>
<a href="https://matrix.to/#/#jellyfinorg:matrix.org">
<img alt="Chat on Matrix" src="https://img.shields.io/matrix/jellyfin:matrix.org.svg?logo=matrix"/>
</a>
<a href="https://forum.jellyfin.org">
<img alt="Join our Forum" src="https://img.shields.io/badge/Forum-forum.jellyfin.org-blue"/>
</a>
<a href="https://github.com/jellyfin/jellyfin/releases.atom">
<img alt="Release RSS Feed" src="https://img.shields.io/badge/rss-releases-ffa500?logo=rss" />
</a>
<a href="https://github.com/jellyfin/jellyfin/commits/master.atom">
<img alt="Master Commits RSS Feed" src="https://img.shields.io/badge/rss-commits-ffa500?logo=rss" />
</a>
</p>

---

Jellyfin is the Free Software Media System that puts you in control of managing and streaming your media. It is an alternative to the proprietary Emby and Plex, to provide media from a dedicated server to end-user devices via multiple apps.

This repository contains operating system and Docker packaging for Jellyfin, for use by manual builders and our release CI system with GitHub workflows. All packaging has henceforth been removed from the main code repositories for the [Jellyfin Server](https://github.com/jellyfin/jellyfin) and [Primary WebUI](https://github.com/jellyfin/jellyfin-web) and moved here.

## Quickstart

To build Jellyfin packages for yourself, follow this quickstart guide. You will need to be running on a Linux system, preferably Debian- or Ubuntu-based, with Docker, Python3 and the Python packages `PyYAML` and `git` (`python3-yaml` and `python3-git` in Debian). Other systems including WSL are untested.

1. Install Docker on your system. The build scripts leverage Docker containers to perform clean builds and avoid contaminating the host system with dependencies.

1. Clone this repository somewhere on your system and enter it.

1. Run `git submodule update --init` to check out the submodules (`jellyfin-server`, `jellyfin-web`).

1. Run `./checkout.py` to update the submodules to the correct `HEAD`s. This command takes one argument, the tag or branch (i.e. `master`) of the repositories to check out; if nothing is specified, `master` is assumed. For example, `./checkout.py master` checks out the current `master` branch of both `jellyfin-server` and `jellyfin-web`, `./checkout.py v10.8.13` checks out the `v10.8.13` tag of both, etc. If a tag is used and one (or more) of the repositories are missing the tag, this command will error out.

### Non-Docker Platforms

If you want a non-Docker image output (`.deb`, `tar`/`zip` archive, etc.) follow this process:

1. Run `./build.py`. This command takes up to 4 arguments, depending on what you're trying to build:

   * The first argument is the version you want to tag your build as. For our official releases, we use either dates for unstable builds (`YYYYMMDDHH` numerical format or `auto` for autogeneration) or the tag without `v` for stable release builds (`10.8.13`, `10.9.0`, etc.), but you can use any version tag you wish here.
   
   * The second argument is the "platform" you want to build for. The available options are listed as top-level keys in the `build.yaml` configuration file or in the `-h` help output.

   * The third argument is, for all platforms except `portable` (DotNET portable), the architecture you want to build for. For each platform, the available architectures can be found as the keys under `archmaps` in the `build.yaml` configuration file.

   * The fourth argument is exclusive to `debian` and `ubuntu` `.deb` packages, and is the release codename of Debian or Ubuntu to build for. For each platform, the available releases can be found as the keys under `releases` in the `build.yaml` configuration file.

   **NOTE:** Your running user must have Docker privileges, or you should run `build.py` as root/with `sudo`.

1. The output binaries will be in the `out/` directory, ready for use. The exact format varies depending on the build type, and can be found, for each archive-based platform, as the values to the `archivetypes` key in the `build.yaml` configuration file.

#### Examples

Build `.deb` packages for Debian 13 "Trixie" `amd64`:

```
./build.py auto debian amd64 trixie
```

Build Linux `.tar.xx` archives for `arm64-musl`:

```
./build.py auto linux arm64-musl
```

Build Windows `.zip` for `amd64`:

```
./build.py auto windows amd64
```

Build a .NET portable `.zip`:

```
./build.py auto portable
```

### Docker Image Platform

If you want a Docker image output follow this process:

1. Install `docker` and `docker-buildx-plugin` for your OS.

1. Run `./build.py`. This command takes up to 4 arguments specific to Docker builds:

   * The first argument is the version you want to tag your build as. For our official releases, we use either dates for unstable builds (`YYYYMMDDHH` numerical format or `auto` for autogeneration) or the tag without `v` for stable release builds (`10.8.13`, `10.9.0`, etc.), but you can use any version tag you wish here.
   
   * The second argument is the "platform" you want to build for. For Docker images, this should be `docker`.

   * The third argument is the architecture you wish to build for. This argument is optional, and not providing it will build images for all supported architectures (sequentially).

   * The fourth argument is `--local`, which should be provided to prevent the script from trying to generate image manifests and push the resulting images to our repositories.

1. The output container image(s) will be present in your `docker image ls` as `jellyfin/jellyfin` with the tag(s) `<jellyfin_version>-<build_arch>`.

#### Examples

Build an `amd64` Docker image:

```
./build.py auto docker amd64 --local
```

## Design

Inside this repository are 7 major components:

1. Submodules for the `jellyfin` (as `jellyfin-server`) and `jellyfin-web` repositories. These are dynamic submodules; the `checkout.py` script will check them out to the required `HEAD` on each build, and thus their actual committed value is irrelevant. Nonetheless, they should be bumped occasionally just to avoid excessive checkout times later.

1. Debian/Ubuntu packaging configurations (under `debian`). These will build the 3 Jellyfin packages (`jellyfin` metapackage, `jellyfin-server` core server, and `jellyfin-web` web client) from a single Dockerfile and helper script (`build.sh`) under `debian/docker/`. Future packages (e.g. Vue) may be added here as well if and when they are promoted to a production build alongside the others, following one consistent versioning scheme.

1. Docker image builder (under `docker`). Like the above two as well, only building the combined Docker images with a single Dockerfile as well as preparing the various manifests needed to push these to the container repos.

1. Portable image builder (under `portable`), which covers all the "archive" builds (.NET portable, Linux, Windows, and MacOS) again from a single Dockerfile.

1. NuGet package builder, to prepare NuGet packages for consumption by plugins and 3rd party clients.

1. Script infrastructure to handle coordinating builds (`build.py`). This script takes basic arguments and, using its internal logic, fires the correct Dockerized builds for the given build type.

1. The GitHub Actions CI to build all the above for every supported version and architecture.

## Design Decisions

### General

* Unified packaging: all packaging is in this repository (vs. within the `jellyfin-server` and `jellyfin-web` repositories)

  This helps ensure two things:
    1. There is a single source of truth for packaging. Previously, there were at least 3 sources of truth, and this became very confusing to update.
    2. Packaging can be run and managed independently of actual code, simplifying the release and build process.

* GitHub Actions for CI: all builds use the GitHub Actions system instead of Azure DevOps

  This helps ensure that CI is visible in a "single pane of glass" (GitHub) and is easier to manage long-term.

* Python script-based builds: Building actually happens via the `build.py` script

  This helps reduce the complexity of the builds by ensuring that the logic to actually generate specific builds is handled in one place in a consistent, well-known language, instead of the CI definitions.

* Git Submodules to handle code (vs. cross-repo builds)

  This ensures that the code checked out is consistent to both repositories, and allows for the unified builds described below without extra steps to combine.

* Remote manual-only triggers: CI workers are triggered by a remote bot

  This reduces the complexity of triggering builds; while it can be done manually in this repo, using an external bot allows for more release wrapper actions to occur before triggering builds.

### Debian/Ubuntu Packages

* Unified package build: this entire repo is the "source" and the source package is named "jellyfin".

   This was chosen to simplify the source package system and simplify building. Now, there is only a single "jellyfin" source package rather than 2. There may be more in the future as other repos might be included (e.g. "jellyfin-ffmpeg", "jellyfin-vue", etc.)

* Dockerized build (`debian/docker/`): the build is run inside a Docker container that matches the target OS release

   This was chosen to ensure a clean slate for every build, as well as enable release-specific builds due to the complexities of our shared dependencies (e.g. `libssl`).

* Per-release/version builds: package versions contain the specific OS version (e.g. `-deb11`, `-ubu2204`)

   This enables support for different builds and packages for each OS release, simplifying shared dependency handling as mentioned above.

* Ubuntu LTS-only support: non-LTS Ubuntu versions have been dropped

   This simplifies our builds as we do not need to then track many 9-month-only releases of Ubuntu, and also reduces the build burden. Users of non-LTS Ubuntu releases can use either the closest Ubuntu LTS version or use Docker containers instead.

* Signing of Debian packages with `debsigs`.

   This was suggested in https://github.com/jellyfin/jellyfin-packaging/issues/14 and was not something we had ever done, but has become trivial with this CI. This alows for the end-user verification of the ownership and integrity of manually downloaded binary `.deb` files obtained from the repository with the `debsigs-verify` command and the policy detailed in that issue. Note that since Debian as a whole (i.e. `dpkg`, `apt`, etc.) does not enforce package signing at this time, enabling this for the *repository* is not possible; conventional repository signatures (using the same signing key) are considered sufficient.

### Docker

* Single unified Docker build: the entirety of our Docker images are built as one container from one Dockerfile.

   This was chosen to keep our Docker builds as simple as possible without requiring 2 intervening images (as was the case with our previous CI).

* Push to both DockerHub and GHCR (GitHub Packages)

   This ensures flexibility for container users to fetch the containers from whatever repository they choose.

* Seamless rebuilds: The root images are appended with the build date to keep them unique

  This ensures we can trigger rebuilds of the Docker containers arbitrarily, in response to things like base OS updates or packaging changes (e.g. a new version of the Intel compute engine for instance).

* Based on Debian 12 ("Bookworm"): the latest base Debian release

  While possibly not as "up-to-date" as Ubuntu, this release is quite current and should cover all major compatibility issues we had with the old images based on Debian 11.

### Portable Builds (Portable .NET, Linux, MacOS, Windows)

* Single unified build: the entirety of the output package is built in one container from one Dockerfile

   This was chosen to keep the portable builds as simple as possible without requiring complex archive combining (as was the case with our previous CI).

* Multiple archive type support (`.tar.gz` vs. `.zip`)

   The output archive type (`.tar.gz` or `.zip`) is chosen based on the build target, with Portable providing both for maximum compatibility, Windows providing `.zip`, and Linux and MacOS providing `.tar.gz`. This can be changed later, for example to add more formats (e.g. `.tar.xz`) or change what produces what, without major complications.

* Full architecture support

   The portable builds support all major architectures now, specifically adding `arm64` Windows builds (I'm certain that _someone_ out there uses it), and making it quite trivial to add new architectures in the future if needed.
