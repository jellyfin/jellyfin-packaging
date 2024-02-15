<h1 align="center">Jellyfin</h1>
<h3 align="center">The Free Software Media System</h3>

---

<p align="center">
<img alt="Logo Banner" src="https://raw.githubusercontent.com/jellyfin/jellyfin-ux/master/branding/SVG/banner-logo-solid.svg?sanitize=true"/>
<br/>
<br/>
<a href="https://github.com/jellyfin/jellyfin">
<img alt="GPL 2.0 License" src="https://img.shields.io/github/license/jellyfin/jellyfin.svg"/>
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
<a href="https://www.reddit.com/r/jellyfin">
<img alt="Join our Subreddit" src="https://img.shields.io/badge/reddit-r%2Fjellyfin-%23FF5700.svg"/>
</a>
<a href="https://github.com/jellyfin/jellyfin/releases.atom">
<img alt="Release RSS Feed" src="https://img.shields.io/badge/rss-releases-ffa500?logo=rss" />
</a>
<a href="https://github.com/jellyfin/jellyfin/commits/master.atom">
<img alt="Master Commits RSS Feed" src="https://img.shields.io/badge/rss-commits-ffa500?logo=rss" />
</a>
</p>

---

Jellyfin is a Free Software Media System that puts you in control of managing and streaming your media. It is an alternative to the proprietary Emby and Plex, to provide media from a dedicated server to end-user devices via multiple apps. Jellyfin is descended from Emby's 3.5.2 release and ported to the .NET Core framework to enable full cross-platform support. There are no strings attached, no premium licenses or features, and no hidden agendas: just a team who want to build something better and work together to achieve it. We welcome anyone who is interested in joining us in our quest!

This repository contains packaging for Jellyfin 10.9.0 and above, for use by manual builders or the CI system with GitHub workflows.

Inside this repository are 7 major components:

1. Submodules for the `jellyfin` (as `jellyfin-server`) and `jellyfin-web` repositories. These are dynamic submodules; the `checkout.py` script will check them out to the required `HEAD` on each build, and thus their actual committed value is irrelevant. Nonetheless, they should be bumped occasionally just to avoid excessive checkout times later.

2. Debian/Ubuntu packaging configurations (under `debian`). These will build the 3 Jellyfin packages (`jellyfin` metapackage, `jellyfin-server` core server, and `jellyfin-web` web client). Future packages (e.g. Vue) may be added here if and when they are promoted to a production build alongside the others.

3. Fedora/CentOS packaging configurations (under `fedora`). These will build the same packages as Debian. This is still a TODO.

4. Docker image builder (under `docker`). Like the above two as well, only building the combined Docker images with a single Dockerfile.

5. Script infrastructure to handle coordinating builds (`build.py`). This script takes basic arguments and, using its internal logic, fires the correct Dockerized builds for the given build type.

6. The GitHub Actions CI to build all the above for every supported version and architecture.

## Design Decisions

### General

* Unified packaging: all packaging is in this repository (vs. within the `jellyfin-server` and `jellyfin-web` repositories)

  This helps ensure two things:
    1. There is a single source of truth for packaging. Previously, there were at least 3 sources of truth and this became very confusing to update.
    2. Packaging can be run and managed independently of actual code, simplifying the release and build process.

* GitHub Actions for CI: all builds use the GitHub Actions system instead of Azure DevOps

  This helps ensure that CI is visible in a "single pane of glass" (GitHub) and is easier to manage long-term.

* Python script-based builds: Building actually happens via the `build.py` script

  This helps reduce the complexity of the builds by ensuring that the logic to actually generate specific builds is handled in one place in a consistent, well-known language, instead of the CI definitions.

* Git Submodules to handle code (vs. cross-repo builds)

  This ensures that the code checked out is consistent to both repositories, and allows for the unified builds described below without extra steps to combine.

### Debian/Ubuntu Packages

* Unified package build: this entire repo is the "source" and the source package is named "jellyfin".

   This was chosen to simplify the source package system and simplify building. Now, there is only a single "jellyfin" source package rather than 2. There may be more in the future as other repos might be included (e.g. "jellyfin-ffmpeg", "jellyfin-vue", etc.)

* Dockerized build (`debian/docker/`): the build is run inside a Docker container.

   This was chosen to ensure a clean slate for every build, as well as enable release-specific builds due to the complexities of our shared dependencies (e.g. `libssl`).

### Fedora/CentOS Packages

TODO - these have not yet been implemented.

### Docker

* Single unified Docker build: the entirety of our Docker images are built as one container from one Dockerfile.

   This was chosen to keep our Docker builds as simple as possible without requiring 2 intervening images (as was the case with our previous CI).

* Push to both DockerHub and GHCR (GitHub Packages)

   This ensures flexibility for container users to fetch the containers from whatever repository they choose.

### Portable Builds (Portable .NET, Linux, MacOS, Windows)

* Single unified build: the entirety of the output package is built in one container from one Dockerfile, with the output archive type (`.tar.gz` or `.zip`) chosen based on the target.

   This was chosen to keep the portable builds as simple as possible without requiring complex archivec combining (as was the case with our previous CI).
