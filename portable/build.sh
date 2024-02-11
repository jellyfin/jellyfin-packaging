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
case ${BTYPE} in
    portable)
        RUNTIME=""
        APPHOST="-p:UseAppHost=false"
    ;;
    *)
        RUNTIME="--self-contained --runtime ${DTYPE}-${DARCH}"
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

pushd ${BUILD_DIR}
for ARCHIVE_TYPE in $( tr ',' '\n' <<<"${ARCHIVE_TYPES}" ); do
    case ${ARCHIVE_TYPE} in
        tar)
            tar -czf "${ARTIFACT_DIR}"/jellyfin_${JVERS}-${PARCH}.tar.gz .
        ;;
        zip)
            zip -qr "${ARTIFACT_DIR}"/jellyfin_${JVERS}-${PARCH}.zip .
        ;;
    esac
done
popd

# Clean up any lingering artifacts
make -f debian/rules clean
rm -rf ${BUILD_DIR}

popd
