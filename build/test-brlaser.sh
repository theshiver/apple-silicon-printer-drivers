#!/bin/sh
# Exercise macOS PDF -> CUPS raster -> Brother output without installing a queue.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GP="$ROOT/pkgroot/Library/Printers/Gutenprint"
T=$(mktemp -d /tmp/brlaser-test.XXXXXX)
cleanup() {
  result=$?
  if [ "$result" -ne 0 ]; then cat "$T/"*.log 2>/dev/null || true; fi
  rm -rf "$T"
  exit "$result"
}
trap cleanup EXIT
FILTER="$GP/libexec/rastertobrlaser"
lipo -verify_arch arm64 "$FILTER"
codesign --verify "$FILTER"
# Validate with the staged filter path, since nothing is installed system-wide.
sed "s#/Library/Printers/Gutenprint/libexec/rastertobrlaser#$FILTER#" \
  "$GP/share/brlaser/ppd/brlaser-hl-1210w.ppd" > "$T/brother.ppd"
# A checkout is user-owned; postinstall sets root ownership for CUPS. Ignore
# that filter ownership check here and exercise the actual filter below.
cupstestppd -I filters "$T/brother.ppd"
printf 'Brother HL-1210W native arm64 smoke test\n' | \
  /usr/libexec/cups/filter/cgtexttopdf 1 user test 1 "" > "$T/test.pdf" 2>"$T/pdf.log"
for DPI in 600 1200; do
  for PAPER in A4 Letter; do
    OPTS="Resolution=${DPI}dpi PageSize=$PAPER"
    PPD="$T/brother.ppd" /usr/libexec/cups/filter/cgpdftoraster 1 user test 1 "$OPTS" "$T/test.pdf" > "$T/test.ras" 2>"$T/raster.log"
    PPD="$T/brother.ppd" "$FILTER" 1 user test 1 "$OPTS" "$T/test.ras" > "$T/test.prn" 2>"$T/filter.log"
    if grep -iE 'ERROR|corrupt' "$T/filter.log"; then exit 1; fi
    [ "$(wc -c < "$T/test.prn")" -gt 1000 ]
    grep -aq '@PJL EOJ' "$T/test.prn"
    PAPER_CODE=$(printf '%s' "$PAPER" | tr '[:lower:]' '[:upper:]')
    grep -aq "@PJL SET PAPER = $PAPER_CODE" "$T/test.prn"
    if [ "$DPI" = 1200 ]; then MODE=TRUE; else MODE=FALSE; fi
    grep -aq "@PJL SET RAS1200MODE = $MODE" "$T/test.prn"
    echo "OK: HL-1210W $DPI dpi, $PAPER ($(wc -c < "$T/test.prn" | tr -d ' ') bytes)"
  done
done
# Every other upstream model: valid PPD and one A4 page through the filter.
for P in "$GP"/share/brlaser/ppd/*.ppd; do
  sed "s#/Library/Printers/Gutenprint/libexec/rastertobrlaser#$FILTER#" "$P" > "$T/m.ppd"
  cupstestppd -q -I filters "$T/m.ppd"
  PPD="$T/m.ppd" /usr/libexec/cups/filter/cgpdftoraster 1 user test 1 "PageSize=A4" "$T/test.pdf" > "$T/test.ras" 2>"$T/raster.log"
  PPD="$T/m.ppd" "$FILTER" 1 user test 1 "PageSize=A4" "$T/test.ras" > "$T/test.prn" 2>"$T/filter.log"
  if grep -iE 'ERROR|corrupt' "$T/filter.log"; then exit 1; fi
  grep -aq '@PJL EOJ' "$T/test.prn"
done
echo "OK: $(ls "$GP"/share/brlaser/ppd/*.ppd | wc -l | tr -d ' ') brlaser PPDs"
