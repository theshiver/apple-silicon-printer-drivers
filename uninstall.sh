#!/bin/sh
# Removes the Gutenprint and bundled brlaser and SpliX drivers, its PPDs, queues and the gutenprint-add helper.
# Vendor files moved aside by the installer stay in /Users/Shared/printer-driver-backup.
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
[ -n "${SUDO_USER:-}" ] && sudo -H -u "$SUDO_USER" /Library/Printers/Gutenprint/bin/airprint-share set 2>/dev/null
for f in /etc/cups/ppd/*.ppd; do
  [ -f "$f" ] || continue; q=$(basename "$f" .ppd)
  grep -qsE 'rastertogutenprint|/Library/Printers/Gutenprint/libexec/rastertobrlaser|/Library/Printers/Gutenprint/libexec/rastertoqpdl' "$f" && lpadmin -x "$q" && echo "removed queue $q"
done
rm -f /usr/local/bin/gutenprint-add
rm -rf "/Applications/Print from iPhone & iPad.app"
rm -rf /Library/Printers/Gutenprint /Library/Printers/PPDs/Contents/Resources/Gutenprint-*.ppd
pkgutil --forget com.github.apple-silicon-printer-drivers >/dev/null 2>&1
echo "removed"
