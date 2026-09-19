# Printer drivers for Apple Silicon Macs (Canon MP250 and ~3,500 others)

**🔎 Website with model search: https://theshiver.github.io/mp250-arm-driver/** — type your printer, get the command.

**The problem:** many older printers (Canon PIXMA, Epson Stylus, HP DeskJet/LaserJet, Brother, Samsung…)
only ever got *Intel* macOS drivers. On an Apple Silicon Mac they ran through Rosetta, and macOS 27
now shows **"The printer software is not compatible with this device"** — and Rosetta is going away.

**The fix:** this package installs [Gutenprint 5.3.4](https://gimp-print.sourceforge.io/), an open-source
driver, compiled **natively for Apple Silicon**. No Rosetta, no vendor software.

It was built for the **Canon PIXMA MP250**, but the same package drives every printer Gutenprint supports.

---

## Step by step: Canon MP250

1. Plug the printer into the Mac with USB and switch it on.
2. Download the `.pkg` from the **[latest release](https://github.com/theshiver/mp250-arm-driver/releases/latest)**.
3. Open **Terminal** (Spotlight → type `Terminal`) and paste this, then press Enter and type your password:

   ```sh
   sudo installer -pkg ~/Downloads/Canon-MP250-arm64-Gutenprint-1.1.0.pkg -target /
   ```

4. **If you had Canon's driver installed before: restart the Mac, then unplug and replug the printer once.**
5. Print something. The printer is called **Canon MP250 (Gutenprint)** and is already the default.

That's it. The installer also moves Canon's old Intel driver to `/Users/Shared/canon-mp250-backup` (nothing is deleted).

---

## Step by step: any other printer

Do steps 1–3 above with your printer connected (the package is the same for every model), then:

**A. Find your printer's id** — search by name, no password needed:

```sh
gutenprint-add --list "iP4300"
```

Output looks like `bjc-PIXMA-iP4300    Canon PIXMA iP4300`. The first word is the id.

**B. Install it** — type `sudo gutenprint-add` followed by the id:

```sh
sudo gutenprint-add bjc-PIXMA-iP4300
```

It creates the printer queue automatically when the printer is on USB. Done.

### Copy-paste examples

| Printer | Command |
|---|---|
| Canon PIXMA MP250 | *(automatic — nothing to type)* |
| Canon PIXMA iP4300 | `sudo gutenprint-add bjc-PIXMA-iP4300` |
| Canon PIXMA MG5100 | `sudo gutenprint-add bjc-PIXMA-MG5100` |
| Canon PIXMA MX922 | `sudo gutenprint-add bjc-PIXMA-MX922` |
| Canon SELPHY CP400 | `sudo gutenprint-add canon-cp400` |
| Epson Stylus Photo R300 | `sudo gutenprint-add escp2-r300` |
| Epson Stylus Photo 1400 | `sudo gutenprint-add escp2-1400` |
| Epson WorkForce 30 | `sudo gutenprint-add escp2-wf30` |
| HP DeskJet 500 | `sudo gutenprint-add pcl-500` |
| HP LaserJet 1010 | `sudo gutenprint-add hp-lj_1010` |
| HP Color LaserJet 4500 | `sudo gutenprint-add hp-clj_4500` |
| Brother HL-5040 | `sudo gutenprint-add brother-hl-5040` |
| Samsung ML-2150 | `sudo gutenprint-add samsung-ml-2150` |
| Lexmark Optra E | `sudo gutenprint-add lexmark-optra_e` |
| Xerox Phaser 6130N | `sudo gutenprint-add xerox-phaser_6130n` |
| Kyocera FS-1000 | `sudo gutenprint-add kyocera-fs-1000` |
| Ricoh Aficio 401 | `sudo gutenprint-add ricoh-afc_401` |
| Oki B430 | `sudo gutenprint-add oki-b430` |
| Dell 3100cn | `sudo gutenprint-add dell-3100cn` |
| Sharp AR-161 | `sudo gutenprint-add sharp-ar-161` |
| Kodak 6800 (dye-sub) | `sudo gutenprint-add kodak-6800` |
| DNP DS40 (dye-sub) | `sudo gutenprint-add dnp-ds40` |
| Mitsubishi CP-3020D (dye-sub) | `sudo gutenprint-add mitsubishi-3020d` |
| Sony UP-DR150 (dye-sub) | `sudo gutenprint-add sony-updr150` |
| Fujifilm ASK-300 (dye-sub) | `sudo gutenprint-add fujifilm-ask-300` |

**Printer on Wi-Fi / network instead of USB?** Add the queue yourself:
`sudo gutenprint-add <id> <QueueName> <device-uri>` — e.g.
`sudo gutenprint-add escp2-r300 Epson_R300 socket://192.168.1.50`.
(`lpinfo -v` lists the URIs macOS sees.)
Or use *System Settings → Printers & Scanners → Add → Use: Select Software…* and pick
"*<your printer> - CUPS+Gutenprint v5.3.4*".

---

## Supported brands

About **3,578 models** are in the database. The main brands:

1. **Canon** — PIXMA iP / iX / MP / MG / MX / TS / TR / Pro, BJC, S-series, i-series, SELPHY CP (~1,250)
2. **Epson** — Stylus Color / Photo / Pro, Stylus C / D / R / RX / SX, Expression, WorkForce, Artisan (~590)
3. **HP** — DeskJet, LaserJet, Color LaserJet, OfficeJet, PhotoSmart, Business Inkjet (~400)
4. **Brother** — HL, DCP, MFC laser series
5. **Samsung** — ML, CLP, CLX, SCX
6. **Lexmark** — Optra, E / C / T / X series, 4076
7. **Xerox** — Phaser, WorkCentre, DocuPrint
8. **Kyocera** — FS, KM, Ecosys
9. **Ricoh** (+ Gestetner, Lanier, NRG, Savin, Infotec) — Aficio, SP (~740)
10. **Oki** — B / C series
11. **Dell** — laser series
12. **Sharp** — AR series
13. **Kodak** — 605 / 6800 / 6850 / 7000 / 8800 dye-sub
14. **DNP / Dai Nippon** — DS40 / DS80 / RX1 / DS620
15. **Mitsubishi** — CP-D / CP-K / CP-3020 dye-sub
16. **Sony** — UP-DR / UP-CR dye-sub
17. **Fujifilm** — ASK dye-sub
18. **Citizen, Shinko, Olympus** — dye-sub photo printers

Search to be sure: `gutenprint-add --list "<part of the name>"`.

**Not covered:** printers that need a vendor-only protocol Gutenprint doesn't speak — most modern
Canon/HP/Brother laser MFPs, Canon "G" ink-tank series, and anything that already works via
**AirPrint** (if macOS finds your printer by itself, you don't need this).

**Scanner:** multifunction printers' scanners are not handled here (the MP250's Canon scanner driver is
Intel-only). Native options: [SANE `pixma`](http://www.sane-project.org/) via Homebrew, or VueScan.

---

## Uninstall

```sh
sudo ./uninstall.sh
```

Removes the driver, all `Gutenprint-*.ppd` files and `gutenprint-add`. Canon's original files stay in
`/Users/Shared/canon-mp250-backup` if you want them back.

---

## Technical details (for the curious)

What gets installed:

| Path | Purpose |
|---|---|
| `/Library/Printers/Gutenprint/libexec/rastertogutenprint.5.3` | arm64 CUPS raster filter (static Gutenprint, ad-hoc signed) |
| `/Library/Printers/Gutenprint/libexec/commandtocanon`, `commandtoepson` | maintenance commands (head clean, nozzle check) |
| `/Library/Printers/Gutenprint/libexec/cups-genppd.5.3` | PPD generator (used by `gutenprint-add`) |
| `/Library/Printers/Gutenprint/bin/gutenprint-add` (+ symlink in `/usr/local/bin`) | helper described above |
| `/Library/Printers/Gutenprint/share/gutenprint/5.3/xml` | printer / dither / paper definitions |
| `/Library/Printers/PPDs/Contents/Resources/Gutenprint-*.ppd` | PPDs with absolute filter paths |

Why it is built this way — things that bit us on macOS 27:

- Apple's `cupsd` runs filters in a sandbox that can read `/Library/Printers` but **not** `/usr/local`,
  and `/usr/libexec/cups` is SIP-protected. So everything lives under `/Library/Printers/Gutenprint`
  and the PPD's `*cupsFilter` lines use absolute paths.
- Gutenprint needs `CFLAGS="-O2 -D_DARWIN_C_SOURCE"` or `netinet/ip.h` fails on `u_char`.
- Canon ships a codeless `AppleUSBMergeNub` kext (`/Library/Extensions/BJUSBLoad.kext`) that pins its
  x86_64 USB class-driver plugin to the printer in the I/O Registry. While it is loaded the `usb`
  backend refuses to fall back to Apple's generic class driver — that is why the installer removes it
  and why a reboot + replug is needed once.
- macOS 27 marks any queue whose filters lack an arm64 slice as *Software Incompatible* on every
  `cupsd` start, even when the job would still run under Rosetta.

Reproducible build: `build/build-gutenprint.sh` (needs Xcode Command Line Tools + Homebrew `gettext`),
then `build/make-pkg.sh <version>`.

## License

Gutenprint is GPL-2.0 (see `LICENSE-gutenprint`); source: gutenprint-5.3.4.tar.xz from SourceForge.
Scripts in this repo: MIT.
