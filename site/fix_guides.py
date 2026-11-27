"""Error guide pages and Tier-1 model hardware notes for site/build-site.py."""

FIX_GUIDES = [
    {
        "slug": "rosetta-printer-driver-macos-27",
        "title": "Reinstall Rosetta for Printer on macOS 27? Better Native Fix",
        "desc": "Should you reinstall Rosetta 2 on macOS 27 Golden Gate to fix “The printer software is not compatible with this device”, or switch to a native Apple Silicon driver?",
        "keywords": "reinstall rosetta printer macos 27, softwareupdate install-rosetta printer, bad cpu type in executable printer mac, macos 27 golden gate rosetta printer, the printer software is not compatible with this device rosetta",
        "h1": "Should you reinstall Rosetta for your printer on macOS 27?",
        "lead": "macOS 27 Golden Gate drops Rosetta 2 by default during the upgrade, breaking Intel-only printer drivers. Here is when reinstalling Rosetta works, why it stops again in macOS 28, and how to fix your printer natively instead.",
        "sections": [
            (
                "Why macOS 27 Golden Gate broke your printer",
                "<p>Older Canon, Brother, Epson, HP and Samsung drivers ship Intel-only CUPS filters inside <code>/Library/Printers/</code>. "
                "When macOS 27 upgrades without Rosetta 2, CUPS cannot execute those binaries. System Settings shows "
                "<em>“The printer software is not compatible with this device”</em>, or the print queue logs <code>Bad CPU type in executable</code>.</p>"
                "<p>Unlike regular Mac apps, background printer filters do not trigger a macOS popup asking to install Rosetta.</p>",
            ),
            (
                "Option A: Reinstall Rosetta 2 (temporary bridge)",
                "<p>If you only want your vendor driver back for now, Apple still lets you install Rosetta 2 manually in macOS 27:</p>"
                "<pre><button class=\"copy\">Copy</button><code>softwareupdate --install-rosetta --agree-to-license</code></pre>"
                "<ol class=\"steps\">"
                "<li>Run the command above in Terminal and wait for it to finish.</li>"
                "<li>Open <strong>System Settings → Printers &amp; Scanners</strong> and remove the broken printer queue.</li>"
                "<li>Restart your Mac, then add the printer again.</li>"
                "</ol>"
                "<p><strong>Where Rosetta falls short:</strong> some vendor drivers still fail signature or filter checks on macOS 27 even after Rosetta is installed, "
                "and Apple ends general Rosetta support for apps in <strong>macOS 28</strong>.</p>",
            ),
            (
                "Option B: Native Apple Silicon drivers (permanent, no Rosetta)",
                "<p>Instead of translating old Intel filters, you can install native <code>arm64</code> open-source drivers compiled specifically for Apple Silicon Macs "
                "(Gutenprint, brlaser, SpliX and foo2zjs). They run directly on M1–M4+ Macs with no Rosetta dependency and keep working across macOS updates.</p>"
                "<table><thead><tr><th>Approach</th><th>Survives macOS 28?</th><th>Works for older USB printers?</th><th>Setup</th></tr></thead>"
                "<tbody><tr><td><strong>Native Apple Silicon driver</strong></td><td>Yes (native arm64)</td><td>Yes (3,777 models)</td><td>Signed .pkg installer</td></tr>"
                "<tr><td>Reinstall Rosetta 2</td><td>No (Rosetta ends in macOS 28)</td><td>Only if vendor kexts/filters still load</td><td>Terminal command + re-add queue</td></tr>"
                "<tr><td>AirPrint</td><td>Yes (built into macOS)</td><td>Wi-Fi/Ethernet AirPrint printers only</td><td>System Settings → Use: AirPrint</td></tr></tbody></table>",
            ),
        ],
        "faq": [
            (
                "What if reinstalling Rosetta didn't fix my printer?",
                "Remove the old printer entry in System Settings → Printers & Scanners, install the native Apple Silicon driver package above, restart once, and add the printer using the entry ending in “Apple Silicon”.",
            ),
            (
                "Does this driver work alongside Rosetta?",
                "Yes. Native arm64 filters do not conflict with Rosetta 2, and if you had Canon's older Intel USB driver installed, the installer safely moves the blocking kernel extension aside without deleting it.",
            ),
            (
                "Will Apple remove Rosetta completely?",
                "Apple announced that macOS 27 is the final release with general Rosetta 2 support for Intel apps, ending in macOS 28. Native arm64 drivers do not use Rosetta at all.",
            ),
        ],
        "related": [
            ("Printer not working after macOS 27 update", "/fix/printer-not-working-after-macos-update/"),
            ("Fix “Stopped - 'Filter' failed” on Mac", "/fix/filter-failed-mac-printer/"),
            ("Fix “Software for this printer isn't available”", "/fix/software-for-this-printer-isnt-available/"),
        ],
        "brands": ["Brother", "Canon", "HP", "Epson", "Samsung"],
    },
    {
        "slug": "software-for-this-printer-isnt-available",
        "title": "Fix “Software for This Printer Isn't Available” on Mac",
        "desc": "macOS says “Software for this printer isn't available from Apple”? Check AirPrint first, then install native Apple Silicon drivers for 3,777 Canon, Brother, HP, Epson & Samsung printers.",
        "keywords": "software for this printer isn't available from apple, software for this printer is not available mac, apple silicon printer driver missing, macos 27 golden gate printer software unavailable",
        "h1": "Fix “Software for this printer isn't available from Apple”",
        "lead": "macOS shows this error when neither Apple's built-in catalog nor Software Update has a driver for your printer. Check AirPrint first; if your printer is older or USB-only, install the native Apple Silicon driver package.",
        "sections": [
            (
                "1. Check if your printer supports AirPrint first",
                "<p>Most network printers built after ~2015 do not need any downloadable driver on Mac:</p>"
                "<ol class=\"steps\">"
                "<li>Connect the printer to the same Wi-Fi or Ethernet network as your Mac (AirPrint does not work over USB on most printers).</li>"
                "<li>Open <strong>System Settings → Printers &amp; Scanners</strong> and click <strong>Add Printer, Scanner, or Fax…</strong>.</li>"
                "<li>Select your printer and check the <strong>Use:</strong> dropdown at the bottom. If <strong>AirPrint</strong> or <strong>Secure AirPrint</strong> appears, choose it and click <strong>Add</strong>.</li>"
                "</ol>",
            ),
            (
                "2. Why Apple stopped hosting older vendor drivers",
                "<p>Apple no longer downloads legacy manufacturer driver packages through Software Update for discontinued printers, and many vendor installers on manufacturer websites are Intel-only or fail on macOS 26 Tahoe and macOS 27 Golden Gate.</p>"
                "<p>When you install this package, 3,777 native Apple Silicon PPD profiles become available immediately under <strong>Select Software…</strong> in Printers &amp; Scanners.</p>",
            ),
            (
                "3. How to add the printer after installing",
                "<ol class=\"steps\">"
                "<li>Download and run the signed <code>.pkg</code> installer above.</li>"
                "<li>If connected over <strong>USB</strong>, the installer sets up supported models automatically. If nothing appears, unplug and re-plug the USB cable (directly into the Mac, avoiding unpowered hubs).</li>"
                "<li>For <strong>Wi-Fi / network</strong> printers or manual setup: click <strong>Add Printer…</strong>, select your printer, set <strong>Use: Select Software…</strong>, search for your model ending in <strong>“Apple Silicon”</strong>, and click <strong>Add</strong>.</li>"
                "</ol>",
            ),
        ],
        "faq": [
            (
                "Why is my printer still missing from Select Software?",
                "Check the home page search box first. Scanners, Brother DCP-T/MFC-T ink-tank models, and newer printers without open-source drivers are not included. If your model uses AirPrint, connect it over Wi-Fi instead of USB.",
            ),
            (
                "Does Reset Printing System help?",
                "Resetting the printing system clears corrupted CUPS queues, which helps if a previous driver left broken files behind, but it will not create a missing driver. Install the driver package first, then add the printer.",
            ),
        ],
        "related": [
            ("Mac printing blank pages or Generic PostScript", "/fix/generic-postscript-printer-blank-pages/"),
            ("Printer not working after macOS 27 update", "/fix/printer-not-working-after-macos-update/"),
            ("Reinstall Rosetta vs. native driver", "/fix/rosetta-printer-driver-macos-27/"),
        ],
        "brands": ["Canon", "Brother", "HP", "Epson", "Samsung"],
    },
    {
        "slug": "filter-failed-mac-printer",
        "title": "Fix “Stopped - 'Filter' Failed” Printer Error on Mac",
        "desc": "Seeing Stopped - 'Filter' failed in the Mac print queue on macOS 27 Golden Gate or Apple Silicon? Fix crashed CUPS filters, reset the queue, or switch to native arm64 drivers.",
        "keywords": "stopped filter failed mac, filter failed macos printer, cups filter failed apple silicon, macos 27 filter failed printer, samsung brother canon filter failed mac, data failed mac printer",
        "h1": "Fix “Stopped - 'Filter' failed” on Mac",
        "lead": "“Stopped - 'Filter' failed” (or “Stopped - 'Data' failed” on some Brother queues) means the macOS CUPS filter crashed before data reached your printer. On Apple Silicon and macOS 27 Golden Gate, the most common trigger is an outdated Intel vendor filter or a broken PPD reference.",
        "sections": [
            (
                "1. Try the quick built-in macOS checks first",
                "<ol class=\"steps\">"
                "<li><strong>Test AirPrint (Wi-Fi printers):</strong> remove the queue in <strong>System Settings → Printers &amp; Scanners</strong>, click <strong>Add</strong>, and choose <strong>Use: AirPrint</strong> if available. AirPrint bypasses third-party filters completely.</li>"
                "<li><strong>Test from Apple Preview:</strong> if the error happens only in Chrome or Acrobat, export to PDF and print from Preview to rule out an app-specific PDF rendering bug.</li>"
                "<li><strong>Reset the printing system:</strong> right-click (or Control-click) the printer list in <strong>Printers &amp; Scanners</strong> and choose <strong>Reset printing system…</strong> to clear corrupt queues.</li>"
                "</ol>",
            ),
            (
                "2. Check why the filter failed in Console / CUPS log",
                "<p>If resetting the queue didn't solve it, the vendor's filter binary inside <code>/Library/Printers/</code> is failing to run on Apple Silicon or macOS 27:</p>"
                "<pre><button class=\"copy\">Copy</button><code>grep -iE \"filter|Bad CPU|gutenprint|brlaser|qpdl\" /var/log/cups/error_log | tail -n 20</code></pre>"
                "<p>If you see <code>Bad CPU type in executable</code>, <code>Library not loaded</code>, or a missing filter inside <code>/Library/Printers/</code>, your old Intel driver is broken and needs a native Apple Silicon replacement.</p>",
            ),
            (
                "3. Replace the crashed vendor filter with native arm64 drivers",
                "<ol class=\"steps\">"
                "<li>Delete the failing printer queue in <strong>System Settings → Printers &amp; Scanners</strong>.</li>"
                "<li>Install the native Apple Silicon driver package above (every filter—<code>rastertogutenprint.5.3</code>, <code>rastertobrlaser</code>, <code>rastertoqpdl</code> and <code>rastertofoo-*</code>—is compiled natively for <code>arm64</code> and signed).</li>"
                "<li>Re-add the printer and make sure you pick the entry ending in <strong>“Apple Silicon”</strong>, not the old manufacturer entry.</li>"
                "</ol>",
            ),
        ],
        "faq": [
            (
                "Why did Samsung or Xerox laser printing fail with 'Filter' failed?",
                "Older Samsung and Xerox SPL drivers relied on Intel binaries or missing PostScript filters. Native arm64 SpliX (rastertoqpdl) replaces that filter chain without Rosetta.",
            ),
            (
                "I installed the package but the queue still says Filter failed.",
                "Your queue is almost certainly still bound to the old manufacturer PPD. Remove that queue completely in Printers & Scanners and add the new entry whose name ends in “Apple Silicon”.",
            ),
        ],
        "related": [
            ("Reinstall Rosetta vs. native driver", "/fix/rosetta-printer-driver-macos-27/"),
            ("Mac printing blank pages or Generic PostScript", "/fix/generic-postscript-printer-blank-pages/"),
            ("Printer not working after macOS 27 update", "/fix/printer-not-working-after-macos-update/"),
        ],
        "brands": ["Samsung", "Brother", "Canon", "Xerox", "HP"],
    },
    {
        "slug": "generic-postscript-printer-blank-pages",
        "title": "Mac Printing Blank Pages or Generic PostScript Printer Fix",
        "desc": "macOS added your printer as a Generic PostScript Printer or prints blank pages and garbage text? Switch to the exact native Apple Silicon model driver.",
        "keywords": "generic postscript printer mac blank pages, mac printing blank pages, generic pcl printer macos, missing printer features mac, select software apple silicon printer",
        "h1": "Fix “Generic PostScript Printer” and blank pages on Mac",
        "lead": "When macOS cannot find an exact driver for an older printer, it often falls back to “Generic PostScript Printer” or “Generic PCL Printer”—causing blank pages, raw text gibberish, or missing paper and duplex options.",
        "sections": [
            (
                "1. Why Generic PostScript prints blank pages or garbage",
                "<p>Inkjets (Canon PIXMA, Epson Stylus/WorkForce) and host-based or SPL lasers (Brother HL-1110/1210W, Samsung ML/SCX/M2020, HP LaserJet 1018/1020/P1005) do <strong>not</strong> speak PostScript. "
                "Sending PostScript data to a non-PostScript printer causes it to eject blank sheets, print pages of raw code, or silently drop the job.</p>",
            ),
            (
                "2. Switch from Generic PostScript to your exact Apple Silicon model",
                "<ol class=\"steps\">"
                "<li>Install the free native Apple Silicon driver package above.</li>"
                "<li>Open <strong>System Settings → Printers &amp; Scanners</strong> and remove the <em>Generic PostScript</em> queue.</li>"
                "<li>Click <strong>Add Printer…</strong>, select your printer, open the <strong>Use:</strong> dropdown and choose <strong>Select Software…</strong>.</li>"
                "<li>Type your model number and pick the entry ending in <strong>“Apple Silicon”</strong> (for example, <code>Canon MP250 series - Apple Silicon</code>).</li>"
                "</ol>",
            ),
            (
                "3. Printing blank pages even with the right model?",
                "<p><strong>Inkjet (Canon / Epson):</strong> run a physical nozzle check from the printer's own buttons first—a dried or empty black cartridge often leaves pages blank while color tests appear fine. Also check <strong>Printer Features → Color Model</strong> in the print dialog.</p>"
                "<p><strong>HP LaserJet 1018 / 1020 / P1005 / P1006:</strong> these models lose their firmware when powered off. Version 2.0.1+ uploads firmware automatically on USB plug-in and before the first print job; wait 5–10 seconds after powering the printer on before printing.</p>",
            ),
        ],
        "faq": [
            (
                "Where are duplex, resolution and black-and-white options?",
                "In the Mac print dialog, expand Printer Features (called Printer Options on macOS 27). Quality is under Resolution, and grayscale printing is under Color Model.",
            ),
            (
                "Can I use Generic PCL if my exact office laser isn't listed?",
                "Yes—if your laser printer supports PCL 5e or PCL 6/XL, try our Generic PCL 6/PCL XL or Generic PCL Color Laser profile after checking the search box.",
            ),
        ],
        "related": [
            ("Fix “Stopped - 'Filter' failed” on Mac", "/fix/filter-failed-mac-printer/"),
            ("Fix “Software for this printer isn't available”", "/fix/software-for-this-printer-isnt-available/"),
            ("Printer not working after macOS 27 update", "/fix/printer-not-working-after-macos-update/"),
        ],
        "brands": ["Canon", "Epson", "Samsung", "Brother", "Generic"],
    },
    {
        "slug": "printer-not-working-after-macos-update",
        "title": "Printer Not Working After macOS 27 Golden Gate Update? Fix",
        "desc": "Printer stopped working after updating to macOS 27 Golden Gate, Tahoe or Sequoia? Complete checklist for incompatible drivers, USB detection, Wi-Fi queues and Canon/HP/Brother quirks.",
        "keywords": "printer not working after macos 27 update, macos 27 golden gate printer not working, printer stopped working after mac update, macos tahoe printer stopped working",
        "h1": "Printer stopped working after the macOS 27 Golden Gate update?",
        "lead": "Nothing is wrong with your printer hardware. macOS 27 Golden Gate removes default Rosetta 2 translation and flags Intel-only vendor drivers as incompatible. Follow this diagnostic order to get printing again in under two minutes.",
        "sections": [
            (
                "Step 1: Confirm whether you need a driver or just AirPrint",
                "<p>Check if your printer supports AirPrint on Wi-Fi or Ethernet: remove the old queue in <strong>Printers &amp; Scanners</strong>, click <strong>Add</strong>, and look for <strong>Use: AirPrint</strong>. "
                "If AirPrint isn't offered—or your printer is USB-only—check your model on our <a href=\"https://macprinterdrivers.com/#search\">home page search</a> and install the free native Apple Silicon package above.</p>",
            ),
            (
                "Step 2: Delete the old incompatible queue after installing",
                "<p>Installing the package adds a new printer entry ending in <strong>“Apple Silicon”</strong>, but does not delete your old queue. "
                "If you print to the old entry, you will still see <em>“The printer software is not compatible with this device”</em>. Remove the old queue in <strong>Printers &amp; Scanners</strong> and print to the new one.</p>",
            ),
            (
                "Step 3: Brand-specific quirks after a macOS update",
                "<ul>"
                "<li><strong>Canon USB printers:</strong> Canon's old driver leaves a kernel extension that blocks macOS USB printing. The installer moves it aside automatically, but you must <strong>restart your Mac once</strong>, then unplug and re-plug the USB cable.</li>"
                "<li><strong>HP LaserJet 1018 / 1020 / P1005 / P1006:</strong> these host-based lasers require RAM firmware upload after power-on; our launchd hotplug helper and filter handle this automatically.</li>"
                "<li><strong>USB hubs and docks:</strong> if macOS doesn't detect the printer at all, plug the USB cable directly into the Mac (or through a simple USB-C adapter) instead of an unpowered hub.</li>"
                "<li><strong>Wi-Fi / Ethernet printers:</strong> the installer auto-configures USB printers only. For network printers, use <strong>Add Printer → Use: Select Software…</strong> and pick your model ending in <strong>“Apple Silicon”</strong>.</li>"
                "</ul>",
            ),
        ],
        "faq": [
            (
                "Will I lose scanning on an all-in-one printer?",
                "This package provides printing drivers only. For scanning on older all-in-ones, check macOS Image Capture (ICA), VueScan (paid), or SANE (free).",
            ),
            (
                "Can I also print from my iPhone or iPad to a USB printer?",
                "Yes. The installer includes the Print from iPhone & iPad app, which shares any printer set up on your Mac over AirPrint while the Mac stays awake.",
            ),
        ],
        "related": [
            ("Reinstall Rosetta vs. native driver", "/fix/rosetta-printer-driver-macos-27/"),
            ("Fix “Stopped - 'Filter' failed” on Mac", "/fix/filter-failed-mac-printer/"),
            ("Fix “Software for this printer isn't available”", "/fix/software-for-this-printer-isnt-available/"),
        ],
        "brands": ["Brother", "Canon", "HP", "Epson", "Samsung"],
    },
]

TIER1_SPECIFIC_NOTES = {
    "samsung/m2020-series": (
        "Samsung Xpress M2020 / M2020W / M2022 monochrome lasers use Samsung's SPL printer language rather than PostScript or PCL. "
        "Over Wi-Fi on the M2020W, add the printer via System Settings → Printers & Scanners → Select Software… and pick the “Apple Silicon” entry; USB sets up automatically. "
        "If an older Samsung package left a broken queue with “Filter” failed, delete the old queue first."
    ),
    "samsung/scx-3400": (
        "The Samsung SCX-3400 / SCX-3405 multifunction laser prints natively via arm64 SpliX (rastertoqpdl) on Apple Silicon. "
        "Note that this package covers printing only; flatbed/ADF scanning requires Apple Image Capture, VueScan, or SANE."
    ),
    "samsung/ml-1640": (
        "The Samsung ML-1640 is a USB-only monochrome SPL laser without AirPrint. "
        "Once installed, connect it directly to your Mac (avoiding unpowered hubs) and select the new “Apple Silicon” queue instead of any leftover Samsung Intel queue."
    ),
    "samsung/ml-2160": (
        "The Samsung ML-2160 / ML-2165 series speaks SPL and was left behind when Samsung's macOS support shifted to HP. "
        "Use the native arm64 SpliX entry; duplex and toner save options are in Printer Features."
    ),
    "samsung/ml-2165": (
        "The Samsung ML-2165 / ML-2165W uses the SPL protocol rather than PostScript. "
        "For the wireless ML-2165W, connect it to your Wi-Fi first, then add it manually with Use: Select Software… → Samsung ML-2165 - Apple Silicon."
    ),
    "samsung/clp-310": (
        "The Samsung CLP-310 is a color SPL laser printer. Unlike monochrome Samsung models, color jobs use the updated native rastertoqpdl filter chain "
        "(without the broken pstoqpdl wrapper that triggers “Filter” failed errors)."
    ),
    "brother/hl-1210w-series": (
        "The Brother HL-1210W / HL-1212W compact mono laser does not support AirPrint and relies on Brother's host-based protocol. "
        "Because Brother's legacy macOS driver needs Rosetta on macOS 27 Golden Gate, our native arm64 brlaser driver runs directly on Apple Silicon without Rosetta. "
        "Over Wi-Fi, add it manually under Select Software… and pick “Brother HL-1210W series - Apple Silicon”."
    ),
    "brother/hl-2130-series": (
        "The Brother HL-2130 is a USB-only monochrome laser that lacks AirPrint and PostScript. "
        "The installer configures it automatically over USB using the native arm64 brlaser filter; remove any old Brother queue that still shows “Software not compatible”."
    ),
    "brother/hl-2270dw-series": (
        "The Brother HL-2270DW supports automatic duplex printing over USB, Ethernet, or Wi-Fi, but predates AirPrint on most firmware revisions. "
        "Two-sided printing, toner save, and 600/1200 dpi options work natively via brlaser."
    ),
    "brother/hl-l2310d-series": (
        "The Brother HL-L2310D is a USB duplex mono laser without AirPrint. "
        "Automatic two-sided printing is enabled in the PPD; check Printer Features in the macOS print dialog for toner save and resolution."
    ),
    "brother/dcp-7055w": (
        "The Brother DCP-7055W multifunction laser prints over USB or Wi-Fi using native arm64 brlaser. "
        "Printing is fully supported; scanning is not included in this driver package."
    ),
    "brother/dcp-7030": (
        "The Brother DCP-7030 is a USB multifunction monochrome laser. This package restores printing natively on Apple Silicon without Rosetta; "
        "for scanning, use macOS Image Capture or VueScan."
    ),
    "brother/mfc-7460dn": (
        "The Brother MFC-7460DN supports USB and wired Ethernet with hardware duplex printing. "
        "For Ethernet queues, add the printer via System Settings → Printers & Scanners → Select Software… → “Brother MFC-7460DN - Apple Silicon”."
    ),
    "brother/dcp-l2510d-series": (
        "The Brother DCP-L2510D is a USB duplex laser MFP. Native arm64 brlaser handles printing and two-sided jobs on macOS 27 Golden Gate without Rosetta; "
        "scanning is handled separately by ICA/VueScan."
    ),
    "canon/pixma-g3010": (
        "The Canon PIXMA G3010 MegaTank inkjet prints over USB or Wi-Fi via native arm64 Gutenprint. "
        "If you previously installed Canon's Intel driver, restart your Mac once after installing so the blocking Canon USB kernel extension is cleared. "
        "Note: this package covers printing only, not scanning."
    ),
    "canon/pixma-mp250": (
        "The Canon PIXMA MP250 is a classic USB all-in-one inkjet whose official Canon driver stopped at Intel Macs. "
        "Restart once after installing if Canon's old driver was ever installed on this Mac, then print to the new “Apple Silicon” queue. Printing only (no scanner driver)."
    ),
    "canon/mg2500-series": (
        "The Canon PIXMA MG2500 series (MG2510, MG2520, MG2522, MG2540, MG2550) is USB-only and has no AirPrint. "
        "Gutenprint drives it natively on Apple Silicon; if black ink looks missing, run a nozzle check on the printer first and verify Color Model in Printer Features."
    ),
    "canon/pixma-ip4300": (
        "The Canon PIXMA iP4300 photo inkjet supports duplex and high-resolution photo modes natively through arm64 Gutenprint. "
        "If macOS added it as a Generic driver or refused the old Canon package, delete the old queue and pick “Canon PIXMA iP4300 - Apple Silicon”."
    ),
    "canon/pixma-ip4700": (
        "The Canon PIXMA iP4700 works natively over USB on macOS 27 Golden Gate via Gutenprint. "
        "Restart once after installing if Canon's Intel USB driver was previously present."
    ),
    "hp/laserjet-1010": (
        "Unlike the 1018 and 1020, the HP LaserJet 1010 uses Gutenprint's PCL driver directly and does not require RAM firmware upload. "
        "Connect over USB directly to the Mac; if macOS picked Generic PostScript, switch to “HP LaserJet 1010 - Apple Silicon”."
    ),
    "hp/laserjet-1018": (
        "The HP LaserJet 1018 is a host-based Zenographics laser that loses its firmware whenever switched off. "
        "Our installer includes both the native arm64 foo2zjs filter and a launchd USB hotplug loader that automatically uploads sihp1018.dl when plugged in or before the first job."
    ),
    "hp/laserjet-1020": (
        "The HP LaserJet 1020 (and 1020 Plus) stores its firmware in volatile RAM. "
        "After installing, our launchd hotplug helper detects the printer over USB and uploads sihp1020.dl automatically—no third-party Windows VM or manual terminal script needed. "
        "Wait 5–10 seconds after powering the printer on before sending the first page."
    ),
    "hp/laserjet-p1005": (
        "The HP LaserJet P1005 is a host-based printer that requires sihpP1005.dl firmware after each power cycle. "
        "The native arm64 foo2xqx filter and USB hotplug loader handle firmware upload automatically on macOS 27 Golden Gate."
    ),
    "hp/laserjet-p1006": (
        "The HP LaserJet P1006 requires sihpP1006.dl firmware on power-on and does not support AirPrint or PCL. "
        "Our native arm64 foo2xqx driver checks device firmware status and uploads it automatically on the first job."
    ),
    "hp/laserjet-pro-p1102": (
        "The HP LaserJet Pro P1102 is a host-based printer whose official HP Easy Start driver often fails on macOS 27 Golden Gate. "
        "Our native arm64 foo2zjs driver sets it up over USB without Rosetta or HP Smart."
    ),
    "hp/laserjet-pro-m12w": (
        "The HP LaserJet Pro M12w works over USB (auto-configured) or Wi-Fi (via Add Printer → Select Software… → “HP LaserJet Pro M12w - Apple Silicon”) "
        "using the native arm64 foo2zjs filter."
    ),
    "xerox/phaser-3020": (
        "The Xerox Phaser 3020 uses Samsung-derived SPL rather than PostScript, which is why Xerox's old Intel driver triggers “Software not compatible” or “Filter” failed on macOS 27. "
        "Native arm64 SpliX (rastertoqpdl) restores both USB and Wi-Fi printing."
    ),
    "xerox/workcentre-3025": (
        "The Xerox WorkCentre 3025 all-in-one prints natively via arm64 SpliX over USB or Wi-Fi. "
        "Printing works without Rosetta; scanning is not covered by this driver package."
    ),
    "generic/pcl-6-pcl-xl-printer": (
        "Use the Generic PCL 6/PCL XL profile when your exact laser printer model isn't listed but supports PCL 6 / PCL XL. "
        "Select it under System Settings → Printers & Scanners → Add → Use: Select Software… → “Generic PCL 6/PCL XL Printer - Apple Silicon”."
    ),
}


def tier1_extra_notes(m, b, mid, path, base):
    parts = []
    if path in TIER1_SPECIFIC_NOTES:
        parts.append(f"<p><strong>Model notes:</strong> {TIER1_SPECIFIC_NOTES[path]}</p>")
    if mid.startswith("brlaser-"):
        parts.append(
            f"<p><strong>Why Brother's driver fails on macOS 27 Golden Gate:</strong> Brother's older Intel drivers fail with "
            f"<em>“The printer software is not compatible with this device”</em> or <code>Bad CPU type in executable</code>. "
            f"See our <a href=\"{base}/fix/rosetta-printer-driver-macos-27/\">Rosetta vs. native driver guide</a>.</p>"
        )
    elif mid.startswith("splix-"):
        parts.append(
            f"<p><strong>Fixing “Filter” failed on {b}:</strong> Older {b} SPL queues crash when macOS cannot execute 32/64-bit Intel filters. "
            f"Delete the old queue first, then see our <a href=\"{base}/fix/filter-failed-mac-printer/\">Filter Failed fix guide</a> if any job stalls.</p>"
        )
    elif mid.startswith("foo2-"):
        parts.append(
            f"<p><strong>Host-based laser note:</strong> If macOS previously added the {m['name']} as a Generic PostScript Printer, pages will come out blank. "
            f"Remove that queue and follow our <a href=\"{base}/fix/generic-postscript-printer-blank-pages/\">Generic PostScript &amp; blank pages guide</a>.</p>"
        )
    else:
        parts.append(
            f"<p><strong>macOS 27 Golden Gate troubleshooting:</strong> Still seeing “Software for this printer isn't available” or blank pages? "
            f"Check our <a href=\"{base}/fix/printer-not-working-after-macos-update/\">macOS 27 post-update checklist</a>.</p>"
        )
    return "".join(parts)
