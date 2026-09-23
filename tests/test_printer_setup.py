"""Test queue setup with isolated files and fake CUPS commands; never change macOS queues."""
import json
import os
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
        self.helper = self.gp / "bin/gutenprint-add"
        self.helper.write_text((PAYLOAD / "bin/gutenprint-add").read_text().replace(
            "GP=/Library/Printers/Gutenprint", f'GP="{self.gp}"').replace(
            "PPDDIR=/Library/Printers/PPDs/Contents/Resources", f'PPDDIR="{self.root}/ppds"'))
        self.helper.chmod(0o755)
        self.script(self.gp / "libexec/cups-genppd.5.3", '''
if [ "$1" = -M ]; then
  printf 'brother-hl-5040 Brother HL-5040\nbrother-hl-5030 Brother HL-5030\nbjc-MP250-series Canon MP250 series\nescp2-r300 Epson Stylus Photo R300\n'
elif [ "$3" = bjc-MP250-series ]; then
  printf '*PPD-Adobe: "4.3"\n*ShortNickName: "Canon MP250 series"\n*cupsFilter: "application/vnd.cups-raster 100 rastertogutenprint.5.3"\n*OpenUI *StpCDXAdjustment/CD Adjustment: PickOne\n*StpCDXAdjustment 0/0 mm: ""\n*CloseUI: *StpCDXAdjustment\n*CustomStpCDXAdjustment True: "pop"\n*ParamCustomStpCDXAdjustment Value/Value: 1 points -15 15\n' > "$2/stp.ppd"
else
  exit 1
fi
''')
        self.script(self.gp / "libexec/rastertobrlaser", "exit 0")
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
        self.assertIn(f"{MODEL} Brother HL-1210W", result)
        self.assertIn("brother-hl-5040 Brother HL-5040", result)
        self.assertEqual(self.run_helper("--list", "1210w").strip(), f"{MODEL} Brother HL-1210W")

    def test_usb_names_and_existing_models(self):
        for uri, model in [
            ("usb://Brother/HL-1210W%20series?serial=123", MODEL),
            ("usb://Brother/HL-1210w?serial=123", MODEL),
            ("usb://Brother/HL-1200%20series?serial=123", "brlaser-hl-1200"),
            ("usb://Brother/HL-2270DW%20series?serial=123", "brlaser-hl-2270dw"),
            ("usb://Brother/HL-5030%20series?serial=123", "brlaser-hl-5030"),
            ("usb://Brother/HL-5040?serial=123", "brother-hl-5040"),
            ("usb://Canon/MP250%20series?serial=123", "bjc-MP250-series"),
            ("usb://EPSON/Stylus%20Photo%20R300?serial=123", "escp2-r300"),
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
        for model in ("brlaser-unknown", "../../bad", "brlaser-../../bad"):
            with self.subTest(model=model):
                self.run_helper(model, success=False)
        self.assertFalse((self.root / "ppds").exists())

    def test_website_catalog_and_ppd_agree(self):
        models = json.loads((ROOT / "docs/models.json").read_text())
        self.assertEqual([m["name"] for m in models if m["id"] == MODEL], ["Brother HL-1210W"])
        self.assertIn(MODEL, (ROOT / "docs/brother/index.html").read_text())
        ppds = sorted(p.stem for p in (PAYLOAD / "share/brlaser/ppd").glob("*.ppd"))
        self.assertEqual(sorted(m["id"] for m in models if m["id"].startswith("brlaser-")), ppds)
        self.assertFalse(any("unreleased" in m for m in models))


if __name__ == "__main__":
    unittest.main()
