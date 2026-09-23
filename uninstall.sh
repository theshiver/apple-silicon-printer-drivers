#!/bin/sh
# Removes the Gutenprint and bundled brlaser drivers, its PPDs, queues and the gutenprint-add helper.
# Vendor files moved aside by the installer stay in /Users/Shared/printer-driver-backup.
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
for f in /etc/cups/ppd/*.ppd; do
  [ -f "$f" ] || continue; q=$(basename "$f" .ppd)
  grep -qsE 'rastertogutenprint|/Library/Printers/Gutenprint/libexec/rastertobrlaser' "$f" && lpadmin -x "$q" && echo "removed queue $q"
done
rm -f /usr/local/bin/gutenprint-add
rm -rf /Library/Printers/Gutenprint /Library/Printers/PPDs/Contents/Resources/Gutenprint-*.ppd
pkgutil --forget com.github.apple-silicon-printer-drivers >/dev/null 2>&1
echo "removed"
