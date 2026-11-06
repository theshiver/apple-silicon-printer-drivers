#!/bin/sh
# Builds dist/AppleSilicon-Printer-Drivers-<ver>.pkg from pkgroot + scripts.
# With Developer ID certificates in the keychain (and a notarytool profile named "notary")
# the binaries and the package are signed, notarized and stapled; otherwise ad-hoc signed.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$HERE/.."; VER=${1:-1.0.0}
OUT="$ROOT/dist/AppleSilicon-Printer-Drivers-$VER.pkg"
APP="$ROOT/pkgroot/Applications/Print from iPhone & iPad.app"
mkdir -p "$ROOT/pkgroot/Applications"; rm -rf "${APP:?}"
"$HERE/build-airprint-app.sh" "$APP"
xattr -cr "$ROOT/pkgroot" 2>/dev/null; find "$ROOT/pkgroot" -name "._*" -delete
mkdir -p "$ROOT/dist"

APP_ID=$(security find-identity -v -p codesigning 2>/dev/null | grep -o '"Developer ID Application: [^"]*"' | head -1 | tr -d '"')
INST_ID=$(security find-identity -v -p basic 2>/dev/null | grep -o '"Developer ID Installer: [^"]*"' | head -1 | tr -d '"')

if [ -n "$APP_ID" ]; then
  echo "signing binaries with: $APP_ID"
  for f in "$ROOT"/pkgroot/Library/Printers/Gutenprint/libexec/*; do
    codesign --force --sign "$APP_ID" --options runtime --timestamp "$f"
  done
  codesign --force --sign "$APP_ID" --options runtime --timestamp "$APP"
else
  echo "no Developer ID Application cert — ad-hoc signing"
  codesign -s - -f "$ROOT"/pkgroot/Library/Printers/Gutenprint/libexec/* "$APP"
fi

TMP="$OUT.unsigned"
WORK=$(mktemp -d)
pkgbuild --root "$ROOT/pkgroot" --scripts "$ROOT/scripts" --install-location / \
  --identifier com.github.apple-silicon-printer-drivers --version "$VER" "$WORK/component.pkg"
# a product archive, because only those can show the closing screen in build/installer
sed "s/@VER@/$VER/" "$HERE/installer/distribution.xml" > "$WORK/distribution.xml"
productbuild --distribution "$WORK/distribution.xml" --resources "$HERE/installer" --package-path "$WORK" "$TMP"
rm -rf "${WORK:?}"

if [ -n "$INST_ID" ]; then
  echo "signing package with: $INST_ID"
  productsign --sign "$INST_ID" --timestamp "$TMP" "$OUT" && rm -f "$TMP"
  if xcrun notarytool history --keychain-profile notary >/dev/null 2>&1; then
    echo "notarizing…"
    xcrun notarytool submit "$OUT" --keychain-profile notary --wait
    xcrun stapler staple "$OUT"
    spctl -a -vv -t install "$OUT" 2>&1 | head -3
  else
    echo "no notarytool profile 'notary' — package signed but not notarized"
  fi
else
  mv "$TMP" "$OUT"
fi
echo "-> $OUT"
