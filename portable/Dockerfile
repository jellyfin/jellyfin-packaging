# Docker build arguments
ARG DOTNET_VERSION=8.0
ARG NODEJS_VERSION=20

ARG PTYPE=debian
ARG PVERSION=12

FROM ${PTYPE}:${PVERSION}

ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist
ARG DOTNET_VERSION
ARG NODEJS_VERSION
ARG PTYPE
ARG PVERSION

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV TYPE=${PTYPE}
ENV VERSION=${PVERSION}
ENV ARCHIVE_TYPES=tar

# Prepare Debian build environment
RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get install --no-install-recommends -y \
    wget debhelper gnupg devscripts build-essential mmv lsb-release zip \
    libssl*.* liblttng-ust* \
    libfontconfig*-dev libcurl*openssl-dev libfreetype*-dev libssl-dev \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

# Prepare dotnet SDK
RUN wget https://packages.microsoft.com/config/${PTYPE}/${PVERSION}/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
 && dpkg -i packages-microsoft-prod.deb \
 && apt-get -f install \
 && apt-get update \
 && apt-get install -y dotnet-sdk-${DOTNET_VERSION}

# Prepare nodejs
RUN wget https://deb.nodesource.com/setup_${NODEJS_VERSION}.x -O nodejs-install.sh \
 && chmod +x ./nodejs-install.sh \
 && ./nodejs-install.sh \
 && apt-get install -y \
    nodejs

# Link to build script
RUN ln -sf ${SOURCE_DIR}/portable/build.sh /build.sh

VOLUME ${SOURCE_DIR}/

VOLUME ${ARTIFACT_DIR}/

ENTRYPOINT ["/build.sh"]
