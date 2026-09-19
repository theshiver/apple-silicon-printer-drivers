# Security & transparency

## What the installer does — exactly

The `.pkg` copies files to `/Library/Printers/Gutenprint/` and then runs
[`scripts/postinstall`](scripts/postinstall) as root. That script, in full:

1. Sets permissions on `/Library/Printers/Gutenprint` and symlinks `gutenprint-add` into `/usr/local/bin`.
2. If Canon's Intel-only IJ driver is present, **moves** (never deletes) these to `/Users/Shared/printer-driver-backup`:
   `/Library/Extensions/BJUSBLoad.kext`, `/Library/Printers/Canon`, `/Library/Printers/PPDs/Contents/Resources/CanonIJ*.ppd.gz`.
   It also removes printer queues that reference the (now unusable) Canon filters.
3. Runs `lpinfo -v`, matches USB printers against Gutenprint's model list, and creates queues with `lpadmin`.

It does not touch anything else, does not phone home, and needs no network.

## Verifying a release

Every release is built **from source on GitHub Actions** (Apple Silicon runner) by
[`.github/workflows/release.yml`](.github/workflows/release.yml) and carries a Sigstore build-provenance attestation:

```sh
gh attestation verify AppleSilicon-Printer-Drivers-<ver>.pkg --owner theshiver
shasum -a 256 -c SHA256SUMS.txt
```

You can also inspect the package before installing:

```sh
pkgutil --expand AppleSilicon-Printer-Drivers-<ver>.pkg /tmp/pkg && cat /tmp/pkg/Scripts/postinstall
```

The package is ad-hoc signed, not notarized (no paid Apple Developer account behind this project).
macOS may warn on double-click; `sudo installer -pkg … -target /` works as documented.

## Reporting

Open a GitHub issue, or email the address on the maintainer's profile for anything sensitive.
