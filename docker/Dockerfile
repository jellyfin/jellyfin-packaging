# Docker build arguments
ARG DOTNET_VERSION=8.0
ARG NODEJS_VERSION=20

# Combined image version (Debian)
ARG OS_VERSION=bookworm

# Jellyfin FFMPEG package
ARG FFMPEG_PACKAGE=jellyfin-ffmpeg6

# https://github.com/intel/compute-runtime/releases
ARG GMMLIB_VERSION=22.3.0
ARG IGC_VERSION=1.0.14828.8
ARG NEO_VERSION=23.30.26918.9
ARG LEVEL_ZERO_VERSION=1.3.26918.9

# Debian architecture (amd64, arm64, armhf), set by build script
ARG PARCH
# Dotnet architeture (x64, arm64, arm), set by build script
ARG DARCH
# QEMU architecture (x86_64, aarch64, arm), set by build script
ARG QARCH
# Base Image archiecture (amd64, arm64v8, arm32v7), set by build script
ARG BARCH

#
# Build the web artifacts
#
FROM node:${NODEJS_VERSION}-alpine as web

ARG SOURCE_DIR=/src
ARG ARTIFACT_DIR=/web

RUN apk add \
    autoconf \
    g++ \
    make \
    libpng-dev \
    gifsicle \
    alpine-sdk \
    automake \
    libtool \
    make \
    gcc \
    musl-dev \
    nasm \
    python3

WORKDIR ${SOURCE_DIR}
COPY jellyfin-web .

RUN npm ci --no-audit --unsafe-perm \
 && npm run build:production \
 && mv dist ${ARTIFACT_DIR}

#
# Build the server artifacts
#
FROM mcr.microsoft.com/dotnet/sdk:${DOTNET_VERSION}-${OS_VERSION}-slim as server

ARG DARCH

ARG SOURCE_DIR=/src
ARG ARTIFACT_DIR=/server

WORKDIR ${SOURCE_DIR}
COPY jellyfin-server .
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1

RUN dotnet publish Jellyfin.Server --configuration Release \
    --output="${ARTIFACT_DIR}" --self-contained \
    --runtime linux-${DARCH} -p:DebugSymbols=false -p:DebugType=none

#
# Build the final combined image
#
FROM multiarch/qemu-user-static:x86_64-${QARCH} as qemu
FROM ${BARCH}/debian:${OS_VERSION}-slim as combined

ARG OS_VERSION
ARG FFMPEG_PACKAGE

ARG GMMLIB_VERSION
ARG IGC_VERSION
ARG NEO_VERSION
ARG LEVEL_ZERO_VERSION

ARG PARCH
ARG DARCH
ARG QARCH

# Copy the QEMU runtime
COPY --from=qemu /usr/bin/* /usr/bin

# Set the health URL
ENV HEALTHCHECK_URL=http://localhost:8096/health

# Default environment variables for the Jellyfin invocation
ENV DOTNET_SYSTEM_GLOBALIZATION_INVARIANT="1" \
    DEBIAN_FRONTEND="noninteractive" \
    LC_ALL="en_US.UTF-8" \
    LANG="en_US.UTF-8" \
    LANGUAGE="en_US:en" \
    JELLYFIN_DATA_DIR="/config" \
    JELLYFIN_CACHE_DIR="/cache" \
    JELLYFIN_CONFIG_DIR="/config/config" \
    JELLYFIN_LOG_DIR="/config/log" \
    JELLYFIN_WEB_DIR="/jellyfin/jellyfin-web" \
    JELLYFIN_FFMPEG="/usr/lib/jellyfin-ffmpeg/ffmpeg"

# https://github.com/dlemstra/Magick.NET/issues/707#issuecomment-785351620
ENV MALLOC_TRIM_THRESHOLD_=131072

# https://github.com/NVIDIA/nvidia-docker/wiki/Installation-(Native-GPU-Support)
ENV NVIDIA_VISIBLE_DEVICES="all"
ENV NVIDIA_DRIVER_CAPABILITIES="compute,video,utility"

# Install dependencies:
# curl: healthcheck
RUN apt-get update \
 && apt-get install --no-install-recommends --no-install-suggests --yes \
    ca-certificates \
    gnupg \
    curl \
    wget \
    apt-transport-https \
 && curl -fsSL https://repo.jellyfin.org/jellyfin_team.gpg.key \
  | gpg --dearmor -o /etc/apt/trusted.gpg.d/debian-jellyfin.gpg \
 && echo "deb [arch=${PARCH}] https://repo.jellyfin.org/debian ${OS_VERSION} main" > /etc/apt/sources.list.d/jellyfin.list \
 && apt-get update \
 && apt-get install --no-install-recommends --no-install-suggests --yes \
    ${FFMPEG_PACKAGE} \
    openssl \
    locales \
    libfontconfig1 \
    libfreetype6 \
 && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen \
 && apt-get remove gnupg apt-transport-https --yes \
 && apt-get clean autoclean --yes \
 && apt-get autoremove --yes \
 && rm -rf /var/cache/apt/archives* /var/lib/apt/lists/*

# Intel VAAPI Tone mapping dependencies:
# Prefer NEO to Beignet since the latter one doesn't support Comet Lake or newer for now.
# Do not use the intel-opencl-icd package from repo since they will not build with RELEASE_WITH_REGKEYS enabled.
# https://github.com/intel/compute-runtime/releases
RUN if [[ ${PARCH} == "amd64" ]]; then \
    mkdir intel-compute-runtime \
 && pushd intel-compute-runtime \
 && wget https://github.com/intel/compute-runtime/releases/download/${NEO_VERSION}/libigdgmm12_${GMMLIB_VERSION}_amd64.deb \
 && wget https://github.com/intel/intel-graphics-compiler/releases/download/igc-${IGC_VERSION}/intel-igc-core_${IGC_VERSION}_amd64.deb \
 && wget https://github.com/intel/intel-graphics-compiler/releases/download/igc-${IGC_VERSION}/intel-igc-opencl_${IGC_VERSION}_amd64.deb \
 && wget https://github.com/intel/compute-runtime/releases/download/${NEO_VERSION}/intel-opencl-icd_${NEO_VERSION}_amd64.deb \
 && wget https://github.com/intel/compute-runtime/releases/download/${NEO_VERSION}/intel-level-zero-gpu_${LEVEL_ZERO_VERSION}_amd64.deb \
 && dpkg -i *.deb \
 && popd \
 && rm -rf intel-compute-runtime \
 ; fi \
 && apt-get remove wget --yes \
 && apt-get clean autoclean --yes \
 && apt-get autoremove --yes \
 && rm -rf /var/cache/apt/archives* /var/lib/apt/lists/*

RUN mkdir -p ${JELLYFIN_DATA_DIR} ${JELLYFIN_CACHE_DIR} \
 && chmod 777 ${JELLYFIN_DATA_DIR} ${JELLYFIN_CACHE_DIR}

COPY --from=server /server /jellyfin
COPY --from=web /web /jellyfin/jellyfin-web

EXPOSE 8096
VOLUME ${JELLYFIN_DATA_DIR} ${JELLYFIN_CACHE_DIR}
ENTRYPOINT [ "/jellyfin/jellyfin" ]

HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
     CMD curl -Lk -fsS "${HEALTHCHECK_URL}" || exit 1