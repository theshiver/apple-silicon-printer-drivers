#!/bin/sh
# Reproducible build of the shipped binaries (macOS on Apple Silicon, Xcode CLT, Homebrew gettext).
# Produces pkgroot/Library/Printers/Gutenprint/{libexec,share}. PPDs are generated at install time.
set -e
VER=5.3.4
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$HERE/.."; W="$(mktemp -d /tmp/gp-build.XXXX)"
cd "$W"
curl -L -o gp.tar.xz "https://sourceforge.net/projects/gimp-print/files/gutenprint-5.3/$VER/gutenprint-$VER.tar.xz/download"
tar xf gp.tar.xz && cd gutenprint-$VER
export PATH="/opt/homebrew/opt/gettext/bin:/opt/homebrew/bin:$PATH"
./configure --prefix=/Library/Printers/Gutenprint --with-cups --without-gimp2 --disable-libgutenprintui2 \
  --enable-cups-ppds --disable-translated-cups-ppds --disable-globalized-cups-ppds --disable-nls \
  --without-readline --disable-test --disable-testpattern CFLAGS="-O2 -D_DARWIN_C_SOURCE"
make -j"$(sysctl -n hw.ncpu)"
make install DESTDIR="$W/stage"
OUT="$ROOT/pkgroot/Library/Printers/Gutenprint"
# Preserve the checked-in helper and any separately built drivers.
rm -rf "$OUT/share/gutenprint"
mkdir -p "$OUT/libexec" "$OUT/share"
cp -R "$W/stage/Library/Printers/Gutenprint/share/gutenprint" "$OUT/share/"
cp "$W/stage/usr/libexec/cups/filter/rastertogutenprint.5.3" "$W/stage/usr/libexec/cups/filter/commandtocanon" "$W/stage/usr/libexec/cups/filter/commandtoepson" "$W/stage/usr/sbin/cups-genppd.5.3" "$OUT/libexec/"
codesign -s - -f "$OUT/libexec/"*
echo "done -> $OUT"
