#!/bin/sh
# Insert an extra-printers block into a Gutenprint printers/*.xml (before its family closes).
# Usage: add-pcl-models.sh <printers/pcl.xml> [extra-file in build/, default pcl-extra-printers.xml]
#        add-pcl-models.sh <printers/escp2.xml> escp2-extra-printers.xml
# Idempotent: an XML that already has the block is left alone.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
XML=$1
export EXTRA="$HERE/${2:-pcl-extra-printers.xml}"
grep -q 'apple-silicon-printer-drivers' "$XML" && exit 0
perl -0pi -e 'BEGIN { local $/; open my $f, "<", $ENV{EXTRA} or die; $extra = <$f> } s#(\n    </family>\n  </printdef>)#\n$extra$1# or die "family end not found\n"' "$XML"
