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

The release package is signed with a Developer ID Installer certificate and notarized by Apple. Check it with:

```sh
spctl -a -vv -t install AppleSilicon-Printer-Drivers-<ver>.pkg     # → "accepted, source=Notarized Developer ID"
pkgutil --check-signature AppleSilicon-Printer-Drivers-<ver>.pkg
```

Each tag is also built from source on GitHub Actions (Apple Silicon runner) by
[`.github/workflows/release.yml`](.github/workflows/release.yml); those `ci-*` assets carry a Sigstore
build-provenance attestation (`gh attestation verify ci-AppleSilicon-Printer-Drivers-<ver>.pkg --owner theshiver`).

You can also inspect the package before installing:

```sh
pkgutil --expand AppleSilicon-Printer-Drivers-<ver>.pkg /tmp/pkg && cat /tmp/pkg/Scripts/postinstall
```

Prefer the command line? `sudo installer -pkg AppleSilicon-Printer-Drivers-<ver>.pkg -target /` does the same as double-clicking.

## Reporting

Open a GitHub issue, or email the address on the maintainer's profile for anything sensitive.
