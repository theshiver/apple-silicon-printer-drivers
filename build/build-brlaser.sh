#!/bin/sh
# Native brlaser filter and PPDs for every upstream Brother model (macOS, Xcode CLT, CMake).
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
OUT="$ROOT/pkgroot/Library/Printers/Gutenprint"
W=$(mktemp -d /tmp/brlaser-build.XXXXXX)
trap 'rm -rf "$W"' EXIT
# Owl-Maintain is the maintained brlaser fork Linux distributions package. Upstream
# pdewacht/brlaser v6 caps blocks at 64 lines, which makes the HL-1110/HL-1210W/
# DCP-1610W engine silently drop dense pages (issue #4, pdewacht/brlaser#40).
VER=6.2.8
SHA256=16dae855aa7fff0eef0c05398fab37678243d7d610fa5f9af0d3a2cc9bf08cb0

# An optional local archive allows the same verified build without network access.
if [ "$#" -gt 0 ]; then
  cp "$1" "$W/brlaser.tar.gz"
else
  curl -fL --retry 3 "https://codeload.github.com/Owl-Maintain/brlaser/tar.gz/refs/tags/v$VER" -o "$W/brlaser.tar.gz"
fi
printf '%s  %s\n' "$SHA256" "$W/brlaser.tar.gz" | shasum -a 256 -c -
tar -xzf "$W/brlaser.tar.gz" -C "$W"
cmake -S "$W/brlaser-$VER" -B "$W/build" \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES=arm64 -DCMAKE_OSX_DEPLOYMENT_TARGET=12.0 \
  -DCUPS_CONFIG=/usr/bin/cups-config
cmake --build "$W/build" --parallel "$(sysctl -n hw.ncpu 2>/dev/null || echo 2)"
ctest --test-dir "$W/build" --output-on-failure
# The shared upstream profile advertises media and trays the HL-1210W lacks.
# Keep supported paper sizes, plain paper and the single tray.
sed -E '/^MediaSize (A6|B6|EnvC5|EnvMonarch|EnvDL)$/d; /^InputSlot [2-5] /d; /^MediaType /d' \
  "$W/build/brlaser.drv" > "$W/hl1210w.drv"
/usr/bin/ppdc -d "$W/ppd" "$W/hl1210w.drv"
/usr/bin/ppdc -d "$W/all" "$W/build/brlaser.drv"

rm -rf "$OUT/share/brlaser/ppd"
rm -f "$OUT"/share/brlaser/brlaser-*.tar.gz
mkdir -p "$OUT/libexec" "$OUT/share/brlaser/ppd"
cp "$W/build/rastertobrlaser" "$OUT/libexec/"
codesign -s - -f "$OUT/libexec/rastertobrlaser"
ppd_fixup() {
  sed -e "s#, using Owl-Maintain/brlaser v$VER#, using brlaser v$VER - Apple Silicon#" \
      -e 's#33 rastertobrlaser#33 /Library/Printers/Gutenprint/libexec/rastertobrlaser#' "$1"
}
# Every upstream model as shipped by Linux distributions, id from its name:
# "Brother HL-2270DW series" -> brlaser-hl-2270dw.
for p in "$W"/all/*.ppd; do
  ID=$(sed -n 's/^\*ShortNickName: "Brother \(.*\)"/\1/p' "$p" | sed 's/ series$//' | tr 'A-Z' 'a-z' | tr -c 'a-z0-9\n' '-')
  # PCL models that already print through Gutenprint stay there; brlaser
  # would win the USB match and silently swap a working driver on upgrade.
  case "$ID" in hl-2250dn|hl-5040|hl-5140) continue;; esac
  ppd_fixup "$p" > "$OUT/share/brlaser/ppd/brlaser-$ID.ppd"
done
# HL-1210W: the trimmed profile replaces the generic one written above.
ppd_fixup "$W/ppd/br1210.ppd" > "$OUT/share/brlaser/ppd/brlaser-hl-1210w.ppd"
# Ship the exact corresponding source and license with the binary.
cp "$W/brlaser.tar.gz" "$OUT/share/brlaser/brlaser-$VER.tar.gz"
cp "$W/brlaser-$VER/COPYING" "$OUT/share/brlaser/COPYING"
cp "$HERE/build-brlaser.sh" "$OUT/share/brlaser/build-brlaser.sh"
echo "done -> $OUT (brlaser)"
