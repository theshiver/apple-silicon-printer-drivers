"""Test queue setup with isolated files and fake CUPS commands; never change macOS queues."""
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "pkgroot/Library/Printers/Gutenprint"
MODEL = "brlaser-hl-1210w"


class PrinterSetupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gp = self.root / "driver"
        self.bin = self.root / "commands"
        self.bin.mkdir()
        (self.gp / "bin").mkdir(parents=True)
        (self.gp / "libexec").mkdir()
        shutil.copytree(PAYLOAD / "share/brlaser/ppd", self.gp / "share/brlaser/ppd")
        shutil.copytree(PAYLOAD / "share/splix/ppd", self.gp / "share/splix/ppd")
        self.helper = self.gp / "bin/gutenprint-add"
        self.helper.write_text((PAYLOAD / "bin/gutenprint-add").read_text().replace(
            "GP=/Library/Printers/Gutenprint", f'GP="{self.gp}"').replace(
            "PPDDIR=/Library/Printers/PPDs/Contents/Resources", f'PPDDIR="{self.root}/ppds"'))
        self.helper.chmod(0o755)
        self.script(self.gp / "libexec/cups-genppd.5.3", '''
if [ "$1" = -M ] && [ "${2:-}" = -v ]; then
  printf '%-20s%s\n' brother-hl-5040 'Brother HL-5040' brother-hl-5030 'Brother HL-5030' \
    bjc-MP250-series 'Canon MP250 series' escp2-r300 'Epson Stylus Photo R300' \
    bjc-Pro9000mk2-series 'Canon Pro9000 Mk.II series' brother-hl-2170w 'Brother HL-2170W' \
    hp-lj_p2015 'HP LaserJet P2015' hp-lj_pro_m201dw 'HP LaserJet Pro M201dw' \
    hp-lj_pro_m225dw 'HP LaserJet Pro MFP M225dw'
elif [ "$1" = -M ]; then
  printf '%s\n' brother-hl-5040 brother-hl-5030 bjc-MP250-series escp2-r300 bjc-Pro9000mk2-series \
    brother-hl-2170w hp-lj_p2015 hp-lj_pro_m201dw hp-lj_pro_m225dw
elif [ "$3" = bjc-MP250-series ]; then
  printf '*PPD-Adobe: "4.3"\n*ShortNickName: "Canon MP250 series"\n*cupsFilter: "application/vnd.cups-raster 100 rastertogutenprint.5.3"\n*OpenUI *StpCDXAdjustment/CD Adjustment: PickOne\n*StpCDXAdjustment 0/0 mm: ""\n*CloseUI: *StpCDXAdjustment\n*CustomStpCDXAdjustment True: "pop"\n*ParamCustomStpCDXAdjustment Value/Value: 1 points -15 15\n' > "$2/stp.ppd"
else
  exit 1
fi
''')
        self.script(self.gp / "libexec/rastertobrlaser", "exit 0")
        self.script(self.gp / "libexec/rastertoqpdl", "exit 0")
        self.script(self.bin / "id", "echo 0")
        self.script(self.bin / "lpinfo", 'printf "%s\\n" "$TEST_DEVICES"')
        self.script(self.bin / "lpadmin", 'printf "%s\\n" "$@" > "$TEST_LOG"; exit "${TEST_FAIL:-0}"')
        self.script(self.bin / "cupsenable", "exit 0")
        self.script(self.bin / "cupsaccept", "exit 0")
        self.env = dict(os.environ, PATH=f"{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin",
                        TEST_DEVICES="", TEST_LOG=str(self.root / "lpadmin.log"))

    def script(self, path, body):
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def run_helper(self, *args, success=True):
        result = subprocess.run([str(self.helper), *args], env=self.env,
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_list_combines_both_drivers(self):
        result = self.run_helper("--list")
        self.assertIn(f"{MODEL} Brother HL-1210W series", result)
        self.assertIn("brother-hl-5040 Brother HL-5040", result)
        # ids of 20+ characters run into the name in cups-genppd -M -v
        self.assertIn("bjc-Pro9000mk2-series Canon Pro9000 Mk.II series", result)
        self.assertEqual(self.run_helper("--list", "1210w").strip(), f"{MODEL} Brother HL-1210W series")

    def test_usb_names_and_existing_models(self):
        for uri, model in [
            ("usb://Brother/HL-1210W%20series?serial=123", MODEL),
            ("usb://Brother/HL-1210w?serial=123", MODEL),
            ("usb://Brother/HL-1200%20series?serial=123", "brlaser-hl-1200"),
            ("usb://Brother/HL-2270DW%20series?serial=123", "brlaser-hl-2270dw"),
            ("usb://Brother/HL-5030%20series?serial=123", "brlaser-hl-5030"),
            ("usb://Brother/HL-5040?serial=123", "brother-hl-5040"),
            ("usb://Brother/DCP-1610W%20series?serial=123", "brlaser-dcp-1610w"),
            ("usb://Brother/MFC-7320?serial=123", "brlaser-mfc-7320"),
            ("usb://Canon/MP250%20series?serial=123", "bjc-MP250-series"),
            ("usb://Canon/Pro9000%20Mk.II%20series?serial=123", "bjc-Pro9000mk2-series"),
            ("usb://EPSON/Stylus%20Photo%20R300?serial=123", "escp2-r300"),
            ("usb://Brother/HL-2170W%20series?serial=123", "brother-hl-2170w"),
            ("usb://HP/LaserJet%20Pro%20M201dw?serial=123", "hp-lj_pro_m201dw"),
            ("usb://HP/LaserJet%20Pro%20MFP%20M225dw?serial=123", "hp-lj_pro_m225dw"),
            ("usb://Hewlett-Packard/HP%20LaserJet%20P2015%20Series?serial=123", "hp-lj_p2015"),
            ("usb://Samsung/ML-1640%20Series?serial=123", "splix-samsung-ml-1640"),
            ("usb://Samsung/M2020%20Series?serial=123", "splix-samsung-m2020"),
            ("usb://Xerox/Phaser%203117?serial=123", "splix-xerox-phaser-3117"),
            ("usb://Dell/Dell%201100?serial=123", "splix-dell-1100"),
            ("usb://Brother/HL-1212W?serial=123", ""),
            ("usb://Other/HL-1210W?serial=123", ""),
        ]:
            with self.subTest(uri=uri):
                self.assertEqual(self.run_helper("--match-usb", uri).strip(), model)

    def test_network_queue_uses_brlaser_ppd(self):
        uri = "socket://192.168.1.50"
        self.run_helper(MODEL, "Brother_WiFi", uri)
        args = (self.root / "lpadmin.log").read_text().splitlines()
        self.assertEqual(args[args.index("-v") + 1], uri)
        self.assertEqual(args[args.index("-p") + 1], "Brother_WiFi")
        ppd = Path(args[args.index("-P") + 1]).read_text()
        self.assertIn('/Library/Printers/Gutenprint/libexec/rastertobrlaser"', ppd)
        self.assertNotIn("rastertogutenprint", ppd)
        self.assertIn('*DefaultResolution: 600dpi', ppd)
        self.assertNotIn('*InputSlot Tray2', ppd)
        self.assertNotIn('*MediaType TRANS', ppd)
        self.assertNotIn('*PageSize A6', ppd)

    def test_usb_selects_correct_brother(self):
        uri = "usb://Brother/HL-1210W%20series?serial=target"
        self.env["TEST_DEVICES"] = f"direct usb://Brother/HL-5040?serial=other\ndirect {uri}"
        self.run_helper(MODEL)
        self.assertIn(uri, (self.root / "lpadmin.log").read_text().splitlines())

    def test_other_brother_does_not_get_hl1210w_driver(self):
        self.env["TEST_DEVICES"] = "direct usb://Brother/HL-5040?serial=other"
        output = self.run_helper(MODEL)
        self.assertIn("no USB device auto-matched", output)
        self.assertFalse((self.root / "lpadmin.log").exists())
        self.assertTrue((self.root / f"ppds/Gutenprint-{MODEL}.ppd").exists())

    def test_splix_queue_uses_absolute_filter(self):
        self.env["TEST_DEVICES"] = ("direct usb://Samsung/ML-1650?serial=other\n"
                                    "direct usb://Samsung/ML-1640%20Series?serial=target")
        self.run_helper("splix-samsung-ml-1640")
        args = (self.root / "lpadmin.log").read_text().splitlines()
        self.assertEqual(args[args.index("-v") + 1], "usb://Samsung/ML-1640%20Series?serial=target")
        self.assertEqual(args[args.index("-D") + 1], "Samsung ML-1640 - Apple Silicon")
        ppd = Path(args[args.index("-P") + 1]).read_text()
        self.assertIn('"application/vnd.cups-raster 0 /Library/Printers/Gutenprint/libexec/rastertoqpdl"', ppd)

    def test_missing_splix_filter_fails_before_queue_creation(self):
        (self.gp / "libexec/rastertoqpdl").unlink()
        self.run_helper("splix-samsung-ml-1640", "Samsung", "socket://192.168.1.50", success=False)
        self.assertFalse((self.root / "lpadmin.log").exists())

    def test_gutenprint_ppd_drops_custom_options(self):
        self.run_helper("bjc-MP250-series", "Canon", "usb://Canon/MP250")
        args = (self.root / "lpadmin.log").read_text().splitlines()
        ppd = Path(args[args.index("-P") + 1]).read_text()
        self.assertIn("*StpCDXAdjustment 0/0 mm", ppd)
        self.assertNotIn("CustomStp", ppd)  # macOS 27 Printer Features OK breaks on these (#1)

    def test_queue_failure_is_reported(self):
        self.env["TEST_FAIL"] = "1"
        output = self.run_helper(MODEL, "Brother", "socket://192.168.1.50", success=False)
        self.assertNotIn("queue created", output)

    def test_missing_filter_fails_before_queue_creation(self):
        (self.gp / "libexec/rastertobrlaser").unlink()
        self.run_helper(MODEL, "Brother", "socket://192.168.1.50", success=False)
        self.assertFalse((self.root / "lpadmin.log").exists())

    def test_unknown_and_invalid_ids_do_not_install(self):
        for model in ("brlaser-unknown", "splix-unknown", "../../bad", "brlaser-../../bad", "splix-../../bad"):
            with self.subTest(model=model):
                self.run_helper(model, success=False)
        self.assertFalse((self.root / "ppds").exists())

    def test_website_catalog_and_ppd_agree(self):
        models = json.loads((ROOT / "docs/models.json").read_text())
        self.assertEqual([m["name"] for m in models if m["id"] == MODEL], ["Brother HL-1210W series"])
        self.assertIn(MODEL, (ROOT / "docs/brother/index.html").read_text())
        ppds = sorted(p.stem for p in (PAYLOAD / "share/brlaser/ppd").glob("*.ppd"))
        self.assertEqual(sorted(m["id"] for m in models if m["id"].startswith("brlaser-")), ppds)
        splix = {p.stem: re.search(r'\*ShortNickName: "(.*)"', p.read_text()).group(1)
                 for p in (PAYLOAD / "share/splix/ppd").glob("*.ppd")}
        self.assertEqual({m["id"]: m["name"] for m in models if m["id"].startswith("splix-")}, splix)
        self.assertIn("splix-samsung-ml-1640", (ROOT / "docs/samsung/index.html").read_text())
        self.assertFalse(any("unreleased" in m for m in models))

    def test_extra_pcl_models_are_shipped_and_listed(self):
        xml = (PAYLOAD / "share/gutenprint/5.3/xml/printers/pcl.xml").read_text()
        extra = (ROOT / "build/pcl-extra-printers.xml").read_text()
        self.assertIn(extra, xml)
        ids = re.findall(r'driver="([^"]+)"', extra)
        self.assertIn("brother-hl-2170w", ids)
        self.assertIn("hp-lj_pro_m201dw", ids)
        # each id once in the whole pcl family: no clash with an upstream entry
        for i in ids:
            self.assertEqual(xml.count(f'driver="{i}"'), 1, i)
        catalog = {m["id"]: m["name"] for m in json.loads((ROOT / "docs/models.json").read_text())}
        for name, i in re.findall(r'name="([^"]+)" driver="([^"]+)"', extra):
            self.assertEqual(catalog.get(i), name)


if __name__ == "__main__":
    unittest.main()
