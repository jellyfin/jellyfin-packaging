#!/bin/bash

#= Generic portable builder (portable, linux, macos, windows)

set -o errexit
set -o xtrace

# Create the intermediate build dir
BUILD_DIR="/build"
mkdir -p ${BUILD_DIR}

# Move to source directory
pushd "${SOURCE_DIR}"

# Build server
pushd jellyfin-server
case ${BUILD_TYPE} in
    portable)
        RUNTIME=""
        APPHOST="-p:UseAppHost=false"
    ;;
    *)
        RUNTIME="--self-contained --runtime ${DOTNET_TYPE}-${DOTNET_ARCH}"
        APPHOST="-p:UseAppHost=true"
    ;;
esac
dotnet publish Jellyfin.Server --configuration Release ${RUNTIME} --output ${BUILD_DIR}/ -p:DebugSymbols=false -p:DebugType=none ${APPHOST}
popd

# Build web
pushd jellyfin-web
npm ci --no-audit --unsafe-perm
npm run build:production
mv dist ${BUILD_DIR}/jellyfin-web
popd

mkdir -p "${ARTIFACT_DIR}/"

if [[ -n ${PACKAGE_ARCH} ]]; then
    VERSION_SUFFIX="${JVERS}-${PACKAGE_ARCH}"
else
    VERSION_SUFFIX="${JVERS}"
fi

pushd ${BUILD_DIR}
for ARCHIVE_TYPE in $( tr ',' '\n' <<<"${ARCHIVE_TYPES}" ); do
    case ${ARCHIVE_TYPE} in
        targz)
            tar -czf "${ARTIFACT_DIR}"/jellyfin_${VERSION_SUFFIX}.tar.gz .
        ;;
        zip)
            zip -qr "${ARTIFACT_DIR}"/jellyfin_${VERSION_SUFFIX}.zip .
        ;;
    esac
done
popd

# Clean up any lingering artifacts
make -f debian/rules clean
rm -rf ${BUILD_DIR}

popd
