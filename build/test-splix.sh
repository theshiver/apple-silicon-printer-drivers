#!/bin/sh
# Exercise macOS PDF -> CUPS raster -> SpliX (SPL/QPDL) output for every model without installing a queue.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GP="$ROOT/pkgroot/Library/Printers/Gutenprint"
T=$(mktemp -d /tmp/splix-test.XXXXXX)
cleanup() {
  result=$?
  if [ "$result" -ne 0 ]; then cat "$T/"*.log 2>/dev/null || true; fi
  rm -rf "$T"
  exit "$result"
}
trap cleanup EXIT
FILTER="$GP/libexec/rastertoqpdl"
lipo "$FILTER" -verify_arch arm64
codesign --verify "$FILTER"
printf 'SpliX native arm64 smoke test\n' | \
  /usr/libexec/cups/filter/cgtexttopdf 1 user test 1 "" > "$T/test.pdf" 2>"$T/pdf.log"
for P in "$GP"/share/splix/ppd/*.ppd; do
  # Validate with the staged filter path, since nothing is installed system-wide.
  sed "s#/Library/Printers/Gutenprint/libexec/rastertoqpdl#$FILTER#" "$P" > "$T/m.ppd"
  # A checkout is user-owned; postinstall sets root ownership for CUPS.
  cupstestppd -q -I filters "$T/m.ppd"
  for PAPER in A4 Letter; do
    PPD="$T/m.ppd" /usr/libexec/cups/filter/cgpdftoraster 1 user test 1 "PageSize=$PAPER" "$T/test.pdf" > "$T/test.ras" 2>"$T/raster.log"
    PPD="$T/m.ppd" "$FILTER" 1 user test 1 "PageSize=$PAPER" "$T/test.ras" > "$T/test.prn" 2>"$T/filter.log"
    if grep -iE 'ERROR|corrupt' "$T/filter.log"; then echo "failed: $P $PAPER"; exit 1; fi
    # one PJL job with a QPDL page in it
    grep -aq '@PJL ENTER LANGUAGE *= *QPDL' "$T/test.prn"
    grep -aq '%-12345X' "$T/test.prn"
    [ "$(wc -c < "$T/test.prn")" -gt 200 ]
  done
done
# Manual duplex past the 30-page memory cache: upstream hangs here (build/splix-cache.patch),
# and swapped pages must go to the job's TMPDIR, not /tmp.
sed "s#/Library/Printers/Gutenprint/libexec/rastertoqpdl#$FILTER#" "$GP/share/splix/ppd/splix-samsung-ml-1640.ppd" > "$T/m.ppd"
i=1; while [ $i -le 45 ]; do printf 'page %s\f' $i; i=$((i + 1)); done | \
  /usr/libexec/cups/filter/cgtexttopdf 1 user test 1 "" > "$T/long.pdf" 2>"$T/pdf.log"
PPD="$T/m.ppd" /usr/libexec/cups/filter/cgpdftoraster 1 user test 1 "PageSize=A4" "$T/long.pdf" > "$T/test.ras" 2>"$T/raster.log"
mkdir "$T/spool"
TMPDIR="$T/spool" PPD="$T/m.ppd" perl -e 'alarm 60; exec @ARGV' "$FILTER" 1 user test 1 "PageSize=A4 Duplex=DuplexNoTumble" "$T/test.ras" > "$T/test.prn" 2>"$T/filter.log"
grep -q 'swapped to disk' "$T/filter.log"
[ "$(grep -c '^PAGE:' "$T/filter.log")" -ge 45 ]
[ -z "$(ls "$T/spool")" ]
echo "OK: 45-page manual duplex"
echo "OK: $(ls "$GP"/share/splix/ppd/*.ppd | wc -l | tr -d ' ') SpliX PPDs"
