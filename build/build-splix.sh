#!/bin/sh
# Native SpliX filter and PPDs for Samsung / Xerox / Dell SPL (GDI) lasers (macOS, Xcode CLT).
#   build/build-splix.sh [splix.tar.gz jbigkit.tar.gz]   (local archives: same verified build offline)
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$HERE/.."
OUT="$ROOT/pkgroot/Library/Printers/Gutenprint"
W=$(mktemp -d /tmp/splix-build.XXXXXX)
trap 'rm -rf "$W"' EXIT
# OpenPrinting/splix is the maintained upstream Linux distributions package.
VER=2.0.2
SHA256=182af811aad4d610de0094a83e69037c67c45fa5fdd5ca1b4e93d34dbfd4fa89
# JBIG compression for the color and newer mono models (CLP-300, Phaser 6110, ...).
JBIGVER=2.1
JBIGSHA256=de7106b6bfaf495d6865c7dd7ac6ca1381bd12e0d81405ea81e7f2167263d932

if [ "$#" -gt 0 ]; then
  cp "$1" "$W/splix.tar.gz"; cp "$2" "$W/jbigkit.tar.gz"
else
  curl -fL --retry 3 "https://codeload.github.com/OpenPrinting/splix/tar.gz/refs/tags/$VER" -o "$W/splix.tar.gz"
  curl -fL --retry 3 "https://www.cl.cam.ac.uk/~mgk25/jbigkit/download/jbigkit-$JBIGVER.tar.gz" -o "$W/jbigkit.tar.gz"
fi
printf '%s  %s\n%s  %s\n' "$SHA256" "$W/splix.tar.gz" "$JBIGSHA256" "$W/jbigkit.tar.gz" | shasum -a 256 -c -
tar -xzf "$W/splix.tar.gz" -C "$W"
tar -xzf "$W/jbigkit.tar.gz" -C "$W"
S="$W/splix-$VER"; J="$W/jbigkit-$JBIGVER/libjbig"
# Swapped pages: restore the one the main thread waits for (manual duplex jobs over 30 pages
# hang otherwise) and swap into the job's $TMPDIR, since Apple's cupsd sandbox blocks /tmp.
patch -d "$S" -p1 < "$HERE/splix-cache.patch"

# Upstream's Makefile wants pkg-config cups (macOS has none); the filter is a plain list of
# sources (src/module.mk, rastertoqpdl_SRC), so compile it directly with the SDK's libcups.
# pstoqpdl is left out: it needs Ghostscript, and cgpdftoraster already feeds rastertoqpdl.
FLAGS="-arch arm64 -mmacosx-version-min=12.0 -O2"
SRCS=$(sed -n '/^rastertoqpdl_SRC/,/^$/p' "$S/src/module.mk" | tr -d '\\' | sed 's/rastertoqpdl_SRC[[:space:]]*+=//' | tr -s ' \t\n' ' ')
mkdir -p "$W/obj"
for c in jbig85.c jbig_ar.c; do
  cc $FLAGS -c "$J/$c" -o "$W/obj/${c%.c}.o"
done
for f in $SRCS; do
  c++ $FLAGS -std=c++11 -Wno-deprecated-declarations -I"$S/include" -I"$J" \
    -DTHREADS=2 -DCACHESIZE=30 -c "$S/$f" -o "$W/obj/$(basename "$f" .cpp).o"
done
c++ $FLAGS -o "$W/rastertoqpdl" "$W"/obj/*.o -lcups -lcupsimage -lpthread

# PPDs: expand upstream's #import includes (ppd/compile.sh drv), then compile every model.
# DISABLE_JBIG stays off, so the JBIG models are built too (ppd/Makefile).
( cd "$S/ppd"
  for d in samsung dell xerox lexmark toshiba hp; do ./compile.sh "$d.drv.in" drv; done
  for d in samsung dell xerox lexmark toshiba hp; do /usr/bin/ppdc -d "$W/all" "$d.drv"; done )

rm -rf "$OUT/share/splix"
mkdir -p "$OUT/libexec" "$OUT/share/splix/ppd"
cp "$W/rastertoqpdl" "$OUT/libexec/"
codesign -s - -f "$OUT/libexec/rastertoqpdl"
# Gutenprint's PCL entries for the same printers keep working queues on upgrade
# (same rule as brlaser's HL-2250DN): leave those models to Gutenprint.
KNOWN=$(STP_DATA_PATH="$OUT/share/gutenprint/5.3/xml" "$OUT/libexec/cups-genppd.5.3" -M -v 2>/dev/null \
  | cut -c21- | tr 'A-Z' 'a-z')
N=0
for p in "$W"/all/*.ppd; do
  # ModelName carries the brand for every model (hp.drv's ShortNickName is just "10x").
  NAME=$(sed -n 's/^\*ModelName: "\(.*\)"/\1/p' "$p")
  if printf '%s\n' "$KNOWN" | grep -qxF "$(printf '%s' "$NAME" | tr 'A-Z' 'a-z')"; then
    echo "skip $NAME (Gutenprint)"; continue
  fi
  # "Samsung ML-1640" -> splix-samsung-ml-1640, "HP Laser 10x Series" -> splix-hp-laser-10x
  ID=splix-$(printf '%s' "$NAME" | sed 's/ [Ss]eries$//' | tr 'A-Z' 'a-z' | tr -c 'a-z0-9\n' '-' | sed 's/--*/-/g; s/-$//')
  sed -e "s#^\*ShortNickName: .*#*ShortNickName: \"$NAME\"#" \
      -e 's#^\(\*NickName: ".*\)"$#\1 - Apple Silicon"#' \
      -e 's#\(\*cupsFilter: *"application/vnd.cups-raster [0-9]* \)rastertoqpdl"#\1/Library/Printers/Gutenprint/libexec/rastertoqpdl"#' \
      "$p" > "$OUT/share/splix/ppd/$ID.ppd"
  N=$((N + 1))
done
# Ship the exact corresponding source and licenses with the binary.
cp "$W/splix.tar.gz" "$OUT/share/splix/splix-$VER.tar.gz"
cp "$W/jbigkit.tar.gz" "$OUT/share/splix/jbigkit-$JBIGVER.tar.gz"
cp "$S/COPYING" "$OUT/share/splix/COPYING"
cp "$HERE/build-splix.sh" "$HERE/splix-cache.patch" "$OUT/share/splix/"
echo "done -> $OUT (splix, $N models)"
