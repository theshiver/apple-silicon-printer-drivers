#!/bin/sh
# Native Brother HL-1210W filter and PPD (macOS, Xcode CLT, CMake).
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
OUT="$ROOT/pkgroot/Library/Printers/Gutenprint"
W=$(mktemp -d /tmp/brlaser-build.XXXXXX)
trap 'rm -rf "$W"' EXIT
VER=6
SHA256=fe7c117eb7e837b6a1751f61a813c218f68a5d8fc40f3403f6a4b1cf5a4758dd

# An optional local archive allows the same verified build without network access.
if [ "$#" -gt 0 ]; then
  cp "$1" "$W/brlaser.tar.gz"
else
  curl -fL --retry 3 "https://codeload.github.com/pdewacht/brlaser/tar.gz/refs/tags/v$VER" -o "$W/brlaser.tar.gz"
fi
printf '%s  %s\n' "$SHA256" "$W/brlaser.tar.gz" | shasum -a 256 -c -
tar -xzf "$W/brlaser.tar.gz" -C "$W"
cmake -S "$W/brlaser-$VER" -B "$W/build" \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=12.0 \
  -DCUPS_CONFIG=/usr/bin/cups-config
cmake --build "$W/build" --parallel "$(sysctl -n hw.ncpu 2>/dev/null || echo 2)"
ctest --test-dir "$W/build" --output-on-failure
# The shared upstream profile advertises media and trays this printer lacks.
# Keep supported paper sizes, plain paper and the single tray. Folio is not
# exposed because brlaser v6 has no Folio command mapping.
sed -E '/^MediaSize (A6|B6|EnvC5|EnvMonarch|EnvDL)$/d; /^InputSlot [2-5] /d; /^MediaType /d' \
  "$W/build/brlaser.drv" > "$W/hl1210w.drv"
/usr/bin/ppdc -d "$W/ppd" "$W/hl1210w.drv"

mkdir -p "$OUT/libexec" "$OUT/share/brlaser/ppd"
cp "$W/build/rastertobrlaser" "$OUT/libexec/"
codesign -s - -f "$OUT/libexec/rastertobrlaser"
# HL-1210W uses the upstream HL-1200 profile. v6 includes the 64-line block
# limit needed for complex pages: https://github.com/pdewacht/brlaser/issues/40
sed -e 's/HL-1200/HL-1210W/g' \
    -e 's/using brlaser v6/using brlaser v6 - Apple Silicon/' \
    -e 's#33 rastertobrlaser#33 /Library/Printers/Gutenprint/libexec/rastertobrlaser#' \
    "$W/ppd/br1200.ppd" > "$OUT/share/brlaser/ppd/brlaser-hl-1210w.ppd"
# Ship the exact corresponding source and license with the binary.
cp "$W/brlaser.tar.gz" "$OUT/share/brlaser/brlaser-$VER.tar.gz"
cp "$W/brlaser-$VER/COPYING" "$OUT/share/brlaser/COPYING"
cp "$HERE/build-brlaser.sh" "$OUT/share/brlaser/build-brlaser.sh"
echo "done -> $OUT (brlaser)"
