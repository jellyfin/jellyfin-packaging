#!/bin/bash

#= Debian .deb builder

set -o errexit
set -o xtrace

# Create the intermediate build dir
BUILD_DIR="/build"
mkdir -p ${BUILD_DIR}

# Move to source directory
pushd "${SOURCE_DIR}"

# Build server
pushd jellyfin-server
dotnet publish Jellyfin.Server --configuration Release --self-contained --runtime linux-${DARCH} --output ${BUILD_DIR}/ -p:DebugSymbols=false -p:DebugType=none -p:UseAppHost=false
popd

# Build web
pushd jellyfin-web
npm ci --no-audit --unsafe-perm
npm run build:production
mv dist ${BUILD_DIR}/jellyfin-web
popd

mkdir -p "${ARTIFACT_DIR}/"

pushd ${BUILD_DIR}
tar -czf "${ARTIFACT_DIR}"/jellyfin_${JVERS}-${PARCH}.tar.gz .
popd

# Clean up any lingering artifacts
make -f debian/rules clean
rm -rf ${BUILD_DIR}

popd
