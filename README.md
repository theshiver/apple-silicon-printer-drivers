# Canon PIXMA MP250 — native Apple Silicon (arm64) driver for macOS

Canon's last macOS driver for the MP250 series (2016) is **Intel-only**. It kept working on
Apple Silicon Macs through Rosetta 2, but macOS 27 now flags it as
**"The printer software is not compatible with this device"** / *Software Incompatible*, and
Apple has announced Rosetta will be largely removed after macOS 27.

This package replaces the Canon driver with a **native arm64 build of
[Gutenprint 5.3.4](https://gimp-print.sourceforge.io/)** and Apple's own generic USB printer
class driver. No Rosetta, no Canon software, nothing Intel.

Tested: MacBook Air (Apple Silicon), macOS 27.0 (26A428), MP250 over USB.

## Install (one step)

1. Download `Canon-MP250-arm64-Gutenprint-<ver>.pkg` from **Releases**.
2. Connect the printer over USB and switch it on.
3. Run the package. It is not notarized, so either right-click → Open, or in Terminal:

   ```sh
   sudo installer -pkg ~/Downloads/Canon-MP250-arm64-Gutenprint-1.0.0.pkg -target /
   ```

The post-install step:

- moves Canon's Intel-only driver (`/Library/Printers/Canon`, `BJUSBLoad.kext`, `CanonIJMP250series.ppd.gz`)
  to `/Users/Shared/canon-mp250-backup` (nothing is deleted),
- removes old queues that used the Canon driver,
- creates a queue named **Canon_MP250** (*Canon MP250 (Gutenprint)*) and makes it the default.

**If `BJUSBLoad.kext` was present, reboot once afterwards** and unplug/replug the printer. That
kext pins Canon's x86_64 USB class driver to the device in the I/O Registry; until the reboot,
jobs may sit at "Sending data to printer".

If the printer was not connected during install, add it later in
*System Settings → Printers & Scanners → Add*, and under *Use* pick *Select Software…* →
**Canon MP250 series - CUPS+Gutenprint v5.3.4**.

## What is installed

| Path | Purpose |
|---|---|
| `/Library/Printers/Gutenprint/libexec/rastertogutenprint.5.3` | arm64 CUPS raster filter (static Gutenprint, ad-hoc signed) |
| `/Library/Printers/Gutenprint/libexec/commandtocanon` | maintenance commands (head clean, nozzle check) |
| `/Library/Printers/Gutenprint/share/gutenprint/5.3/xml` | printer/dither/paper definitions |
| `/Library/Printers/PPDs/Contents/Resources/Gutenprint-Canon-MP250.ppd` | PPD with absolute filter paths |

Everything lives under `/Library/Printers` because Apple's `cupsd` sandbox only lets filters read
from there (and a few system paths); `/usr/local` is not readable by filters.

## Scanner

The MP250's scanner needs Canon's ICA driver, which is also Intel-only and is **not** covered
here. Native options: [SANE `pixma` backend](http://www.sane-project.org/) via Homebrew, or VueScan.

## Uninstall

```sh
sudo ./uninstall.sh
```

Canon's original files stay in `/Users/Shared/canon-mp250-backup` if you ever want them back.

## Building from source

`build/build-gutenprint.sh` reproduces the shipped binaries (needs Xcode Command Line Tools and
Homebrew `gettext`). `build/make-pkg.sh <version>` produces the `.pkg` from `pkgroot/` + `scripts/`.

Notes for anyone adapting this to another Gutenprint-supported Canon/Epson model:

- configure with `CFLAGS="-O2 -D_DARWIN_C_SOURCE"` — otherwise `netinet/ip.h` fails on `u_char`,
- `--prefix=/Library/Printers/Gutenprint` so the compiled-in XML data path is sandbox-readable,
- rewrite the PPD's `*cupsFilter` lines to absolute paths (`/usr/libexec/cups` is SIP-protected),
- if the vendor shipped a codeless `AppleUSBMergeNub` kext under `/Library/Extensions`, it must go,
  or the `usb` backend keeps trying to load the vendor's x86_64 class driver plugin.

## License

Gutenprint is GPL-2.0 (see `LICENSE-gutenprint`); source: gutenprint-5.3.4.tar.xz from SourceForge.
Scripts in this repo: MIT.
