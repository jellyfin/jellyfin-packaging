# Docker build arguments
ARG DOTNET_VERSION=8.0
ARG NODEJS_VERSION=20
# Default to 12, but set externally by the `build.py` script
ARG GCC_VERSION=12

ARG PACKAGE_TYPE
ARG PACKAGE_VERSION
ARG PACKAGE_ARCH

FROM ${PACKAGE_TYPE}:${PACKAGE_VERSION}

ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist
ARG DOTNET_VERSION
ARG NODEJS_VERSION
ARG PACKAGE_TYPE
ARG PACKAGE_VERSION
ARG PACKAGE_ARCH
ARG GCC_VERSION

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV DEB_BUILD_OPTIONS=noddebs
ENV TYPE=${PACKAGE_TYPE}
ENV VERSION=${PACKAGE_VERSION}
ENV ARCH=${PACKAGE_ARCH}

# Prepare Debian build environment
RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get install --no-install-recommends -y \
    wget \
    debhelper \
    gnupg \
    devscripts \
    build-essential \
    mmv \
    lsb-release \
    libssl*.* \
    liblttng-ust* \
    libfontconfig*-dev \
    libcurl*openssl-dev \
    libfreetype*-dev \
    libssl-dev \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

# Prepare the cross-toolchain
RUN if test "${PACKAGE_ARCH}" != "$( dpkg --print-architecture )"; then \
 if grep -q -i ubuntu /etc/os-release; then \
   rm /etc/apt/sources.list \
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
 && apt-get install --no-install-recommends -y cross-gcc-dev \
 && TARGET_LIST="${PACKAGE_ARCH}" cross-gcc-gensource ${GCC_VERSION} \
 && cd cross-gcc-packages-amd64/cross-gcc-${GCC_VERSION}-${PACKAGE_ARCH} \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get -f install --no-install-recommends -o Dpkg::Options::="--force-overwrite" -y \
    bison flex libtool gdb sharutils netbase libmpc-dev libmpfr-dev libgmp-dev \
    systemtap-sdt-dev autogen expect chrpath zlib1g-dev zip \
    binutils-aarch64-linux-gnu binutils-arm-linux-gnueabihf \
    gcc-${GCC_VERSION}-source libstdc++-${GCC_VERSION}-dev-${PACKAGE_ARCH}-cross \
    libc6-dev:${PACKAGE_ARCH} linux-libc-dev:${PACKAGE_ARCH} libgcc1:${PACKAGE_ARCH} libstdc++-${GCC_VERSION}-dev:${PACKAGE_ARCH} \
    libfontconfig*-dev:${PACKAGE_ARCH} libcurl*openssl-dev:${PACKAGE_ARCH} libfreetype*-dev:${PACKAGE_ARCH} libssl-dev:${PACKAGE_ARCH} \
    libssl[13].*:${PACKAGE_ARCH} liblttng-ust*:${PACKAGE_ARCH} \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*
 ; fi

# Prepare dotnet SDK
RUN wget https://packages.microsoft.com/config/${PACKAGE_TYPE}/${PACKAGE_VERSION}/packages-microsoft-prod.deb -O packages-microsoft-prod.deb \
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

# Clean up dependencies
RUN apt-get remove wget -y \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

# Link to build script
RUN ln -sf ${SOURCE_DIR}/debian/docker/build.sh /build.sh

VOLUME ${SOURCE_DIR}/

VOLUME ${ARTIFACT_DIR}/

ENTRYPOINT ["/build.sh"]
