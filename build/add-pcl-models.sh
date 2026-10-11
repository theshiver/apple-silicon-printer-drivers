#!/bin/sh
# Insert build/pcl-extra-printers.xml into Gutenprint's printers/pcl.xml (before the pcl family closes).
# Idempotent: a pcl.xml that already has the block is left alone.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
XML=$1
grep -q 'apple-silicon-printer-drivers' "$XML" && exit 0
perl -0pi -e 'BEGIN { local $/; open my $f, "<", "'"$HERE"'/pcl-extra-printers.xml" or die; $extra = <$f> } s#(\n    </family>\n  </printdef>)#\n$extra$1# or die "pcl family end not found\n"' "$XML"
