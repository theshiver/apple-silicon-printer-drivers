#!/bin/sh
# Exercise macOS PDF -> CUPS raster -> foo2zjs family output for every model without installing a queue.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GP="$ROOT/pkgroot/Library/Printers/Gutenprint"
T=$(mktemp -d /tmp/foo2-test.XXXXXX)
cleanup() {
  result=$?
  if [ "$result" -ne 0 ]; then cat "$T/"*.log 2>/dev/null || true; fi
  rm -rf "$T"
  exit "$result"
}
trap cleanup EXIT
printf 'foo2zjs native arm64 smoke test\n' | \
  /usr/libexec/cups/filter/cgtexttopdf 1 user test 1 "" > "$T/test.pdf" 2>"$T/pdf.log"
N=0
for P in "$GP"/share/foo2zjs/ppd/*.ppd; do
  FILTER=$GP/libexec/$(sed -n 's#^\*cupsFilter:.*/\(rastertofoo-[a-z0-9]*\)"$#\1#p' "$P")
  lipo "$FILTER" -verify_arch arm64
  codesign --verify "$FILTER"
  # Validate with the staged filter path, since nothing is installed system-wide.
  sed "s#/Library/Printers/Gutenprint/libexec/#$GP/libexec/#" "$P" > "$T/m.ppd"
  # A checkout is user-owned; postinstall sets root ownership for CUPS.
  cupstestppd -q -I filters "$T/m.ppd"
  FW=$(sed -n 's/^\*foo2Firmware: "\(.*\)"/\1/p' "$P")
  [ -z "$FW" ] || [ -s "$GP/share/foo2zjs/firmware/$FW" ]
  MODES=Gray
  grep -q '^\*ColorModel CMYK' "$P" && MODES="Gray CMYK"
  PAPER=$(sed -n 's/^\*DefaultPageSize: //p' "$P")
  for MODE in $MODES; do
    OPTS="PageSize=$PAPER ColorModel=$MODE"
    PPD="$T/m.ppd" /usr/libexec/cups/filter/cgpdftoraster 1 user test 1 "$OPTS" "$T/test.pdf" > "$T/test.ras" 2>"$T/raster.log"
    PPD="$T/m.ppd" "$FILTER" 1 user test 1 "$OPTS" "$T/test.ras" > "$T/test.prn" 2>"$T/filter.log"
    if grep -E '^ERROR' "$T/filter.log"; then echo "failed: $P $MODE"; exit 1; fi
    grep -q '^PAGE: 1' "$T/filter.log"
    [ "$(wc -c < "$T/test.prn")" -gt 200 ] || { echo "no output: $P $MODE"; exit 1; }
  done
  N=$((N + 1))
done
echo "OK: $N foo2zjs PPDs"
