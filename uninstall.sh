#!/bin/sh
# Removes the Gutenprint MP250 driver and queue (does NOT restore Canon's driver; see /Users/Shared/canon-mp250-backup)
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
lpadmin -x Canon_MP250 2>/dev/null
rm -f /usr/local/bin/gutenprint-add
rm -rf /Library/Printers/Gutenprint /Library/Printers/PPDs/Contents/Resources/Gutenprint-*.ppd
pkgutil --forget com.github.apple-silicon-printer-drivers >/dev/null 2>&1
echo "removed"
