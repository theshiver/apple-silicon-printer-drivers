"""Test AirPrint sharing with fake commands and a temporary home; never starts a real printer."""
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tempfile
import unittest
import xml.dom.minidom

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "pkgroot/Library/Printers/Gutenprint/bin"


class AirPrintTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / "home"
        self.ppds = self.root / "ppd"
        fake = self.root / "commands"
        for d in (self.home, self.ppds, fake):
            d.mkdir()
        (self.ppds / "Canon_MP250.ppd").write_text("*ColorDevice: True\n")
        (self.ppds / "Brother_HL.ppd").write_text("*ColorDevice: False\n*OpenUI *Duplex/2-Sided: PickOne\n")
        lpstat = fake / "lpstat"
        lpstat.write_text("""#!/bin/sh
if [ "$1" = -v ]; then echo "device for $2: socket://127.0.0.1:9/"; exit; fi
if [ "$1" = -l ]; then echo "printer $3 is idle."; [ "$3" = Office ] && printf '\\tDescription: Office & Co\\n'; exit; fi
echo "printer Canon_MP250 is idle.  enabled since Wed Nov  4 20:18:50 2026"
echo "printer Brother_HL disabled since Wed Nov  4 20:18:50 2026 -"
echo "	reason unknown"
echo "printer Office is idle.  enabled since Fri Sep 19 14:43:48 2025"
echo "printer Canon_MP250__Mac_ is idle.  enabled since Fri Sep 19 14:43:48 2025"
""")
        lpstat.chmod(0o755)
        self.calls = self.root / "calls"
        launchctl = fake / "launchctl"
        launchctl.write_text(f'#!/bin/sh\necho "$@" >> "{self.calls}"\n')
        launchctl.chmod(0o755)
        self.share = self.root / "airprint-share"
        self.share.write_text((BIN / "airprint-share").read_text().replace("PPDS=/etc/cups/ppd", f'PPDS="{self.ppds}"'))
        self.share.chmod(0o755)
        self.env = {**os.environ, "HOME": str(self.home), "PATH": f"{fake}:{os.environ['PATH']}"}
        self.agents = self.home / "Library/LaunchAgents"

    def run_share(self, *args, ok=True):
        r = subprocess.run([str(self.share), *args], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode == 0, ok, r.stderr)
        return r.stdout.split()

    def agent(self, queue):
        with open(self.agents / f"com.github.apple-silicon-printer-drivers.airprint.{queue}.plist", "rb") as f:
            return plistlib.load(f)

    def test_lists_every_printer_except_our_own_announcement(self):
        self.assertEqual(sorted(self.run_share("list")), ["Brother_HL", "Canon_MP250", "Office"])

    def test_off_by_default(self):
        self.assertEqual(self.run_share("shared"), [])

    def test_refuses_an_unknown_printer_and_its_own_announcement(self):
        self.run_share("set", "Nope", ok=False)
        self.run_share("set", "Canon_MP250__Mac_", ok=False)
        self.assertFalse(self.agents.exists())

    def test_uses_the_printer_name_and_escapes_it(self):
        self.run_share("set", "Office")
        self.assertEqual(self.agent("Office")["ProgramArguments"][-1], "Office & Co (Mac)")

    def test_info_reports_name_state_and_reach(self):
        self.run_share("set", "Office")
        r = subprocess.run([str(self.share), "info"], env=self.env, capture_output=True, text=True)
        self.assertIn("Office\tOffice & Co\t1\t0", r.stdout.splitlines())
        self.assertIn("Canon_MP250\tCanon MP250\t0\t0", r.stdout.splitlines())

    def test_a_queue_without_a_ppd_counts_as_color(self):
        self.run_share("set", "Office")
        args = self.agent("Office")["ProgramArguments"]
        self.assertEqual(args[args.index("-s") + 1], "10,5")

    def test_set_starts_agents_with_the_right_settings(self):
        self.run_share("set", "Canon_MP250", "Brother_HL")
        canon, brother = self.agent("Canon_MP250"), self.agent("Brother_HL")
        self.assertEqual(canon["EnvironmentVariables"]["AIRPRINT_QUEUE"], "Canon_MP250")
        args = canon["ProgramArguments"]
        self.assertEqual(args[-1], "Canon MP250 (Mac)")
        self.assertEqual(args[args.index("-s") + 1], "10,5")
        self.assertNotIn("-2", args)
        self.assertIn("-2", brother["ProgramArguments"])
        self.assertEqual(brother["ProgramArguments"][brother["ProgramArguments"].index("-s") + 1], "10")
        ports = {a["ProgramArguments"][a["ProgramArguments"].index("-p") + 1] for a in (canon, brother)}
        self.assertEqual(len(ports), 2)
        self.assertEqual(self.calls.read_text().count("bootstrap"), 2)

    def test_set_replaces_the_shared_printers(self):
        self.run_share("set", "Canon_MP250", "Brother_HL")
        self.run_share("set", "Brother_HL")
        self.assertEqual(self.run_share("shared"), ["Brother_HL"])
        self.assertEqual(self.calls.read_text().count("bootstrap"), 2)
        self.assertEqual(self.calls.read_text().count("bootout"), 1)
        self.run_share("set")
        self.assertEqual(self.run_share("shared"), [])

    def forward(self, content_type, **ipp):
        lp = self.root / "lp"
        out = self.root / "lp.out"
        lp.write_text(f'#!/bin/sh\necho "$@" > "{out}"\n')
        lp.chmod(0o755)
        script = self.root / "airprint-forward"
        script.write_text((BIN / "airprint-forward").read_text().replace("LP=/usr/bin/lp", f'LP="{lp}"'))
        script.chmod(0o755)
        env = {**os.environ, "AIRPRINT_QUEUE": "Canon_MP250", "CONTENT_TYPE": content_type, **ipp}
        r = subprocess.run([str(script), "/spool/job.pdf"], env=env, capture_output=True, text=True)
        return r.returncode, out.read_text().split() if out.exists() else None

    def test_forward_passes_job_options_to_the_queue(self):
        code, args = self.forward("application/pdf", IPP_COPIES="2", IPP_MEDIA="iso_a4_210x297mm",
                                  IPP_SIDES="two-sided-long-edge", IPP_PRINT_COLOR_MODE="monochrome")
        self.assertEqual(code, 0)
        joined = " ".join(args)
        for part in ("-d Canon_MP250", "-n 2", "-o media=iso_a4_210x297mm", "-o sides=two-sided-long-edge", "-o ColorModel=Gray"):
            self.assertIn(part, joined)
        self.assertEqual(args[-1], "/spool/job.pdf")

    def test_forward_reads_the_paper_size_an_iphone_sends(self):
        col = "{media-size={x-dimension=10160 y-dimension=15240} media-right-margin=0}"
        code, args = self.forward("application/pdf", IPP_MEDIA_COL=col)
        self.assertEqual(code, 0)
        self.assertIn("media=Custom.101.6x152.4mm", args)

    def test_forward_refuses_urf_it_cannot_convert(self):
        code, args = self.forward("image/urf")
        self.assertEqual(code, 1)
        self.assertIsNone(args)


class InstallerTest(unittest.TestCase):
    def test_distribution_is_arm64_and_shows_the_closing_screen(self):
        text = (ROOT / "build/installer/distribution.xml").read_text()
        xml.dom.minidom.parseString(text)
        self.assertIn('hostArchitectures="arm64"', text)
        self.assertIn('<conclusion file="conclusion.html"', text)
        self.assertIn("sponsors/theshiver", (ROOT / "build/installer/conclusion.html").read_text())

    @unittest.skipUnless(shutil.which("swiftc"), "macOS only")
    def test_app_builds(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run([str(ROOT / "build/build-airprint-app.sh"), f"{d}/a.app"], check=True)
            self.assertTrue(Path(f"{d}/a.app/Contents/MacOS/SharePrinters").exists())


if __name__ == "__main__":
    unittest.main()
