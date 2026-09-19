#!/bin/sh
# Removes the Gutenprint driver, its PPDs, queues and the gutenprint-add helper.
# Vendor files moved aside by the installer stay in /Users/Shared/printer-driver-backup.
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
for q in $(lpstat -p 2>/dev/null | awk '{print $2}'); do
  grep -qs 'rastertogutenprint' "/etc/cups/ppd/$q.ppd" 2>/dev/null && lpadmin -x "$q" && echo "removed queue $q"
done
rm -f /usr/local/bin/gutenprint-add
rm -rf /Library/Printers/Gutenprint /Library/Printers/PPDs/Contents/Resources/Gutenprint-*.ppd
pkgutil --forget com.github.apple-silicon-printer-drivers >/dev/null 2>&1
echo "removed"
