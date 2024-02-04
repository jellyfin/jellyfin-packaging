#!/bin/bash

#= Debian .deb builder

set -o errexit
set -o xtrace

# Move to source directory
pushd "${SOURCE_DIR}"

# Build DEB
if [[ ${ARCH} != $( dpkg --print-architecture ) ]]; then
    export CONFIG_SITE=/etc/dpkg-cross/cross-config.${ARCH}
    export CONFIG_CROSS="-a ${ARCH}"
fi
dpkg-buildpackage -us -uc ${CONFIG_CROSS} --pre-clean --post-clean

mkdir -p "${ARTIFACT_DIR}/"
mv ../jellyfin*.{deb,dsc,tar.gz,buildinfo,changes} "${ARTIFACT_DIR}/"

popd
