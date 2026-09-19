#!/bin/sh
# Builds dist/Canon-MP250-arm64-Gutenprint-<ver>.pkg from pkgroot + scripts
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$HERE/.."; VER=${1:-1.0.0}
xattr -cr "$ROOT/pkgroot" 2>/dev/null; find "$ROOT/pkgroot" -name "._*" -delete
mkdir -p "$ROOT/dist"
pkgbuild --root "$ROOT/pkgroot" --scripts "$ROOT/scripts" --install-location / \
  --identifier com.github.mp250-arm-driver --version "$VER" \
  "$ROOT/dist/Canon-MP250-arm64-Gutenprint-$VER.pkg"
