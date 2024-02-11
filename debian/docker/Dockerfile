# Docker build arguments
ARG DOTNET_VERSION=8.0
ARG NODEJS_VERSION=20
# Default to 12, but set externally by the `build.py` script
ARG GCC_VERSION=12

ARG PTYPE
ARG PVERSION
ARG PARCH

FROM ${PTYPE}:${PVERSION}

ARG SOURCE_DIR=/jellyfin
ARG ARTIFACT_DIR=/dist
ARG DOTNET_VERSION
ARG NODEJS_VERSION
ARG PTYPE
ARG PVERSION
ARG PARCH
ARG GCC_VERSION

# Docker run environment
ENV SOURCE_DIR=/jellyfin
ENV ARTIFACT_DIR=/dist
ENV DEB_BUILD_OPTIONS=noddebs
ENV TYPE=${PTYPE}
ENV VERSION=${PVERSION}
ENV ARCH=${PARCH}

# Prepare Debian build environment
RUN apt-get update -y \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get install --no-install-recommends -y \
    wget debhelper gnupg devscripts build-essential mmv lsb-release \
    libssl*.* liblttng-ust* \
    libfontconfig*-dev libcurl*openssl-dev libfreetype*-dev libssl-dev \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Prepare the cross-toolchain
RUN if test "${PARCH}" != "$( dpkg --print-architecture )"; then \
 if grep -q -i ubuntu /etc/os-release; then \
   rm /etc/apt/sources.list \
   && export CODENAME="$( lsb_release -c -s )" \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME} main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME}-updates main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME}-backports main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ ${CODENAME}-security main restricted universe multiverse" >>/etc/apt/sources.list.d/amd64.list \
   && echo "deb [arch=${PARCH}] http://ports.ubuntu.com/ ${CODENAME} main restricted universe multiverse" >>/etc/apt/sources.list.d/${PARCH}.list \
   && echo "deb [arch=${PARCH}] http://ports.ubuntu.com/ ${CODENAME}-updates main restricted universe multiverse" >>/etc/apt/sources.list.d/${PARCH}.list \
   && echo "deb [arch=${PARCH}] http://ports.ubuntu.com/ ${CODENAME}-backports main restricted universe multiverse" >>/etc/apt/sources.list.d/${PARCH}.list \
   && echo "deb [arch=${PARCH}] http://ports.ubuntu.com/ ${CODENAME}-security main restricted universe multiverse" >>/etc/apt/sources.list.d/${PARCH}.list \
 ; fi \
 && set -o xtrace \
 && dpkg --add-architecture ${PARCH} \
 && apt-get update -y \
 && apt-get install --no-install-recommends -y cross-gcc-dev \
 && TARGET_LIST="${PARCH}" cross-gcc-gensource ${GCC_VERSION} \
 && cd cross-gcc-packages-amd64/cross-gcc-${GCC_VERSION}-${PARCH} \
 && DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC \
    apt-get -f install --no-install-recommends -o Dpkg::Options::="--force-overwrite" -y \
    bison flex libtool gdb sharutils netbase libmpc-dev libmpfr-dev libgmp-dev \
    systemtap-sdt-dev autogen expect chrpath zlib1g-dev zip \
    binutils-aarch64-linux-gnu binutils-arm-linux-gnueabihf \
    gcc-${GCC_VERSION}-source libstdc++-${GCC_VERSION}-dev-${PARCH}-cross \
    libc6-dev:${PARCH} linux-libc-dev:${PARCH} libgcc1:${PARCH} libstdc++-${GCC_VERSION}-dev:${PARCH} \
    libfontconfig*-dev:${PARCH} libcurl*openssl-dev:${PARCH} libfreetype*-dev:${PARCH} libssl-dev:${PARCH} \
    libssl[13].*:${PARCH} liblttng-ust*:${PARCH} \
 && apt-get clean autoclean -y \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/* \
 ; fi

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
RUN ln -sf ${SOURCE_DIR}/debian/docker/build.sh /build.sh

VOLUME ${SOURCE_DIR}/

VOLUME ${ARTIFACT_DIR}/

ENTRYPOINT ["/build.sh"]
