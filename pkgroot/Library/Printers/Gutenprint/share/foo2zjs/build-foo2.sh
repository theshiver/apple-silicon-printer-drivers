#!/bin/sh
# Native foo2zjs family filters, PPDs and HP firmware (macOS, Xcode CLT).
#   build/build-foo2.sh [foo2zjs.tar.xz printer-all.tar.gz]   (local archives: same verified build offline)
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
OUT="$ROOT/pkgroot/Library/Printers/Gutenprint"
W=$(mktemp -d /tmp/foo2-build.XXXXXX)
trap 'rm -rf "$W"' EXIT
# Debian's archive of foo2zjs: upstream's own site is gone, and this hash is in Debian's signed .dsc.
VER=20200505dfsg0
SHA256=87465e6a31f8501b90508d50e97901d2cce8b5b3de5418cc156e66d5c500421b
# Debian strips the HP firmware from that archive; these images are the same files from this repository.
FWREPO=b6601e32dd6f8958a2e1422264e53cda938269ee

if [ "$#" -gt 0 ]; then
  cp "$1" "$W/foo2zjs.tar.xz"; cp "$2" "$W/fw.tar.gz"
else
  curl -fL --retry 3 "https://deb.debian.org/debian/pool/main/f/foo2zjs/foo2zjs_$VER.orig.tar.xz" -o "$W/foo2zjs.tar.xz"
  curl -fL --retry 3 "https://codeload.github.com/faradayfury/printer-all/tar.gz/$FWREPO" -o "$W/fw.tar.gz"
fi
printf '%s  %s\n' "$SHA256" "$W/foo2zjs.tar.xz" | shasum -a 256 -c -
tar -xJf "$W/foo2zjs.tar.xz" -C "$W"
tar -xzf "$W/fw.tar.gz" -C "$W"
S="$W/foo2zjs-$VER"; F="$W/printer-all-$FWREPO/foo2zjs"
( cd "$F" && shasum -a 256 -c "$HERE/foo2-firmware.sha256" )

FLAGS="-arch arm64 -mmacosx-version-min=12.0 -O2 -w"
rm -rf "$OUT/share/foo2zjs"
rm -f "$OUT"/libexec/rastertofoo-*
mkdir -p "$OUT/libexec" "$OUT/share/foo2zjs/ppd" "$OUT/share/foo2zjs/firmware"
cc $FLAGS -c "$S/jbig.c" -o "$W/jbig.o"
cc $FLAGS -c "$S/jbig_ar.c" -o "$W/jbig_ar.o"
cc $FLAGS -Wno-deprecated-declarations -c "$HERE/rastertofoo.c" -o "$W/rastertofoo.o"
for T in foo2zjs foo2xqx foo2lava foo2qpdl foo2hbpl2 foo2hiperc foo2oak foo2slx foo2hp foo2ddst; do
  cc $FLAGS -Dmain=foo2_main -I"$S" -c "$S/$T.c" -o "$W/$T.o"
  cc -arch arm64 -mmacosx-version-min=12.0 -o "$OUT/libexec/rastertofoo-$T" "$W/rastertofoo.o" "$W/$T.o" "$W/jbig.o" "$W/jbig_ar.o" -lcups -lcupsimage
  codesign -s - -f "$OUT/libexec/rastertofoo-$T"
done

# The firmware images become the .dl stream the printer expects, as upstream's getweb does.
cc $FLAGS -o "$W/arm2hpdl" "$S/arm2hpdl.c"
for I in "$F"/*.img; do
  "$W/arm2hpdl" "$I" > "$OUT/share/foo2zjs/firmware/$(basename "$I" .img).dl"
done

# Models the other drivers already cover stay with them, so working queues keep working on upgrade.
{ STP_DATA_PATH="$OUT/share/gutenprint/5.3/xml" "$OUT/libexec/cups-genppd.5.3" -M -v 2>/dev/null | cut -c21-
  grep -h '^\*ShortNickName' "$OUT"/share/brlaser/ppd/*.ppd "$OUT"/share/splix/ppd/*.ppd | cut -d'"' -f2
} > "$W/known.txt"
python3 "$HERE/gen-foo2-ppds.py" "$S" "$OUT/share/foo2zjs/ppd" "$W/known.txt"

# Ship the exact corresponding source and licenses with the binaries.
cp "$W/foo2zjs.tar.xz" "$OUT/share/foo2zjs/foo2zjs-$VER.orig.tar.xz"
cp "$S/COPYING" "$OUT/share/foo2zjs/COPYING"
cp "$HERE/build-foo2.sh" "$HERE/rastertofoo.c" "$HERE/gen-foo2-ppds.py" "$HERE/foo2-firmware.sha256" "$OUT/share/foo2zjs/"
echo "done -> $OUT (foo2zjs, $(ls "$OUT/share/foo2zjs/ppd" | wc -l | tr -d ' ') models)"
