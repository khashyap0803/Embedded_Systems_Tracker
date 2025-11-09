#!/usr/bin/env bash
set -euo pipefail

OUTPUT_ROOT=${1:-dist/linux}
APP_ID="embedded-tracker"
APP_TITLE="Embedded Tracker"
VERSION=$(poetry version -s)

mkdir -p "${OUTPUT_ROOT}"

poetry run pyinstaller \
  --noconsole \
  --name "${APP_ID}" \
  --onefile \
  --collect-all embedded_tracker \
  main.py

STAGE_DIR="${OUTPUT_ROOT}/package"
BIN_DIR="${STAGE_DIR}/usr/local/bin"
DESKTOP_DIR="${STAGE_DIR}/usr/share/applications"
DEBIAN_DIR="${STAGE_DIR}/DEBIAN"

rm -rf "${STAGE_DIR}"
mkdir -p "${BIN_DIR}" "${DESKTOP_DIR}" "${DEBIAN_DIR}"

cp "dist/${APP_ID}" "${BIN_DIR}/${APP_ID}"
chmod 755 "${BIN_DIR}/${APP_ID}"

cat > "${DESKTOP_DIR}/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=${APP_TITLE}
Exec=${APP_ID}
Icon=${APP_ID}
Categories=Education;Utility;
Terminal=false
EOF

cat > "${DEBIAN_DIR}/control" <<EOF
Package: ${APP_ID}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: amd64
Maintainer: ${USER:-embedded-tracker}
Description: GUI tracker for embedded systems learning roadmaps.
EOF

dpkg-deb --build "${STAGE_DIR}" "${OUTPUT_ROOT}/${APP_ID}_${VERSION}_amd64.deb"

echo "Generated package at ${OUTPUT_ROOT}/${APP_ID}_${VERSION}_amd64.deb"
