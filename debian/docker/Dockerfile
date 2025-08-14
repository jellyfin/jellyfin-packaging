# Docker build arguments
ARG DOTNET_VERSION=8.0
ARG NODEJS_VERSION=20
# Default to 12, but set externally by the `build.py` script
ARG GCC_VERSION=12

ARG PACKAGE_TYPE
ARG PACKAGE_VERSION
ARG PACKAGE_ARCH
ARG GCC_ARCH

FROM ${PACKAGE_TYPE}:${PACKAGE_VERSION}

ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist
ARG DOTNET_VERSION
ARG NODEJS_VERSION
ARG PACKAGE_TYPE
ARG PACKAGE_VERSION
ARG PACKAGE_ARCH
ARG GCC_ARCH
ARG GCC_VERSION

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV DEB_BUILD_OPTIONS=noddebs
ENV TYPE=${PACKAGE_TYPE}
ENV VERSION=${PACKAGE_VERSION}
ENV ARCH=${PACKAGE_ARCH}
ENV GCC_ARCH=${GCC_ARCH}

# Prepare Debian build environment
RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get install --no-install-recommends -y \
    wget \
    debhelper \
    gnupg \
    devscripts \
    build-essential \
    git \
    mmv \
    lsb-release \
    libssl*.* \
    liblttng-ust* \
    libfontconfig*-dev \
    libcurl*openssl-dev \
    libfreetype*-dev \
    libssl-dev \
    libicu-dev \
    icu-devtools \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/* \
 && git config --global --add safe.directory /jellyfin/jellyfin-web

# Prepare the cross-toolchain
RUN if test "${PACKAGE_ARCH}" != "$( dpkg --print-architecture )"; then \
 if grep -q -i ubuntu /etc/os-release; then \
   rm /etc/apt/sources.list /etc/apt/sources.list.d/* || true \
   && export CODENAME="$( lsb_release -c -s )" \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME} main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME}-updates main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME}-backports main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME}-security main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=${PACKAGE_ARCH}] http://ports.ubuntu.com/ ${CODENAME} main restricted universe multiverse" >>/etc/apt/sources.list.d/${PACKAGE_ARCH}.list \
   && echo "deb [arch=${PACKAGE_ARCH}] http://ports.ubuntu.com/ ${CODENAME}-updates main restricted universe multiverse" >>/etc/apt/sources.list.d/${PACKAGE_ARCH}.list \
   && echo "deb [arch=${PACKAGE_ARCH}] http://ports.ubuntu.com/ ${CODENAME}-backports main restricted universe multiverse" >>/etc/apt/sources.list.d/${PACKAGE_ARCH}.list \
   && echo "deb [arch=${PACKAGE_ARCH}] http://ports.ubuntu.com/ ${CODENAME}-security main restricted universe multiverse" >>/etc/apt/sources.list.d/${PACKAGE_ARCH}.list \
 ; fi \
 && set -o xtrace \
 && dpkg --add-architecture ${PACKAGE_ARCH} \
 && apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get -f install --no-install-recommends -o Dpkg::Options::="--force-overwrite" -y \
    bison \
    flex \
    libtool \
    gdb \
    sharutils \
    netbase \
    libmpc-dev \
    libmpfr-dev \
    libgmp-dev \
    systemtap-sdt-dev \
    autogen \
    expect \
    chrpath \
    zlib1g-dev \
    zip \
    binutils-aarch64-linux-gnu \
    binutils-arm-linux-gnueabihf \
    gcc-${GCC_VERSION}-source \
    gcc-${GCC_ARCH}-linux-gnu \
    binutils-${GCC_ARCH}-linux-gnu \
    libstdc++-${GCC_VERSION}-dev-${PACKAGE_ARCH}-cross \
    libc6-dev:${PACKAGE_ARCH} \
    linux-libc-dev:${PACKAGE_ARCH} \
    libgcc1:${PACKAGE_ARCH} \
    libstdc++-${GCC_VERSION}-dev:${PACKAGE_ARCH} \
    libfontconfig*-dev:${PACKAGE_ARCH} \
    libcurl*openssl-dev:${PACKAGE_ARCH} \
    libfreetype*-dev:${PACKAGE_ARCH} \
    libssl-dev:${PACKAGE_ARCH} \
    libssl[13].*:${PACKAGE_ARCH} \
    liblttng-ust*:${PACKAGE_ARCH} \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/* \
 ; fi

# Prepare dotnet SDK
RUN wget -O- https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --channel ${DOTNET_VERSION} --install-dir /usr/local/bin

# Prepare nodejs
RUN wget https://deb.nodesource.com/setup_${NODEJS_VERSION}.x -O nodejs-install.sh \
 && chmod +x ./nodejs-install.sh \
 && ./nodejs-install.sh \
 && apt-get install -y \
    nodejs

# Clean up dependencies
RUN apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

# Link to build script
RUN ln -sf ${SOURCE_DIR}/debian/docker/build.sh /build.sh

VOLUME ${SOURCE_DIR}/

VOLUME ${ARTIFACT_DIR}/

ENTRYPOINT ["/build.sh"]
