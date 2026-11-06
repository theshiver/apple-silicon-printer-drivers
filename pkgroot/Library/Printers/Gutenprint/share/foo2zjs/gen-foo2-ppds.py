#!/usr/bin/env python3
"""Generate macOS PPDs for the foo2zjs family from upstream's Foomatic PPDs.

  build/gen-foo2-ppds.py <foo2zjs source dir> <output ppd dir> <known model names file>

Upstream's PPDs need foomatic-rip and Ghostscript, which macOS doesn't have. Rather than port
each wrapper's paper tables and clipping, this runs the real wrapper with stub gs and foo2*
commands and records the arguments it would have used, per paper size. Those go in the PPD
for build/rastertofoo.c.
"""
import os, pathlib, re, stat, subprocess, sys, tempfile

SRC, OUT, KNOWN = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
known = {l.strip().lower() for l in open(KNOWN) if l.strip()}
LIBEXEC = "/Library/Printers/Gutenprint/libexec"

# Upstream's hplj1000: printers that load firmware at power on. P1007 and P1008 are aliases.
FIRMWARE = {"HP LaserJet 1000": "sihp1000.dl", "HP LaserJet 1005": "sihp1005.dl", "HP LaserJet 1018": "sihp1018.dl",
            "HP LaserJet 1020": "sihp1020.dl", "HP LaserJet P1005": "sihpP1005.dl", "HP LaserJet P1006": "sihpP1006.dl",
            "HP LaserJet P1007": "sihpP1005.dl", "HP LaserJet P1008": "sihpP1006.dl",
            "HP LaserJet P1505": "sihpP1505.dl", "HP LaserJet P1505n": "sihpP1505.dl"}
# Other names for a model upstream lists twice; the first spelling is the one we keep.
SKIP = {"Generic-OAKT_Printer", "Generic-ZjStream_Printer", "Minolta-magicolor_2430_DL"}
BRANDS = {"KONICA MINOLTA": "Konica Minolta", "Fuji Xerox": "Fuji Xerox"}
# Print dialog names for what cgpdftoraster needs; 1-bit like SpliX, banded for color.
GRAY = "<</cupsColorSpace 3/cupsColorOrder 0/cupsBitsPerColor 1>>setpagedevice"
CMYK = "<</cupsColorSpace 6/cupsColorOrder 1/cupsBitsPerColor 1>>setpagedevice"

stub = pathlib.Path(tempfile.mkdtemp())
cap = stub / "cap"
tools = "foo2zjs foo2xqx foo2lava foo2qpdl foo2hbpl2 foo2hiperc foo2oak foo2slx foo2hp foo2ddst".split()
scripts = {"gs": 'printf "GS\\t" >>"$CAP"; printf "%s\\t" "$@" >>"$CAP"; echo >>"$CAP"; cat >/dev/null',
           "foo2zjs-pstops": "cat"}
for t in tools:
    scripts[t] = f'printf "FOO\\t{t}\\t" >>"$CAP"; printf "%s\\t" "$@" >>"$CAP"; echo >>"$CAP"; cat >/dev/null'
for name, body in scripts.items():
    p = stub / name
    p.write_text("#!/bin/sh\n" + body + "\n")
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
ENV = {**os.environ, "PATH": f"{stub}:{os.environ['PATH']}", "CAP": str(cap)}


def capture(command):
    """Run a wrapper command line; return (tool, args, gs device), or None if it refused."""
    cap.write_text("")
    wrapper, *args = command
    subprocess.run(["sh", str(SRC / f"{wrapper}.in"), *args], input=b"x\n", env=ENV, cwd=SRC, capture_output=True)
    lines = [l.split("\t")[:-1] for l in cap.read_text().splitlines() if l.strip()]
    foo = [l for l in lines if l[0] == "FOO"]
    gs = [l for l in lines if l[0] == "GS" and any(a.startswith("-sDEVICE=") for a in l)]
    if not foo or not gs:
        return None
    device = next(a for a in gs[-1] if a.startswith("-sDEVICE="))[9:]
    out, words = [], foo[-1][2:]
    while words:
        w = words.pop(0)
        # -J and -U take the job name and user: optional, and blank from a wrapper run by hand
        if w in ("-J", "-U"):
            words.pop(0)
        elif w:
            out.append(w)
    return foo[-1][1], out, device


def settings(ppd, option):
    return dict(re.findall(rf'^\*FoomaticRIPOptionSetting\s+{option}=([^:]+):\s*"([^"]*)"', ppd, re.M))


def default(ppd, option):
    m = re.search(rf"^\*Default{option}:\s*(\S+)", ppd, re.M)
    return m.group(1) if m else None


def command_for(ppd, page, color):
    """The wrapper command Foomatic would build for this page size and color mode."""
    base = re.search(r'^\*FoomaticRIPCommandLine:\s*"(.*?)%A', ppd, re.M).group(1).split()
    args = []
    for opt in ("Resolution", "Quality", "PrinterType", "Duplex"):
        vals, d = settings(ppd, opt), default(ppd, opt)
        if d in vals:
            args += vals[d].split()
    # one bit per plane is what cgpdftoraster gives us
    args += settings(ppd, "BitsPerPlane").get("1-BPP", "").split()
    modes = settings(ppd, "ColorMode")
    if color:
        # upstream's name for its color mode varies: Color, ICM, ...
        args += modes[next(k for k in modes if k not in ("Monochrome", "Gray"))].split()
    else:
        args += modes.get("Monochrome", "").split()
    args += settings(ppd, "PageSize")[page].split()
    return base + args


def block(ppd, keyword):
    return dict(re.findall(rf'^\*{keyword}\s+([^/:\s]+)(?:/[^:]*)?:\s*"([^"]*)"', ppd, re.M))


def model_name(ppd):
    name = re.search(r'^\*ModelName:\s*"(.*)"', ppd, re.M).group(1)
    for a, b in BRANDS.items():
        name = name.replace(a, b)
    return name.replace("Fuji_Xerox", "Fuji Xerox")


def write_ppd(path, name, ppd):
    # foo2oak has no plane input, so the HP Color LaserJet 1500 prints mono here
    color = (re.search(r"^\*ColorDevice:\s*True", ppd, re.M) is not None and "foo2oak" not in ppd
             and any(k not in ("Monochrome", "Gray") for k in settings(ppd, "ColorMode")))
    sizes, dims, areas = settings(ppd, "PageSize"), block(ppd, "PaperDimension"), block(ppd, "ImageableArea")
    rows, grays, colors, tool = [], {}, {}, None
    for size in sizes:
        if size not in dims or size not in areas:
            continue
        got = capture(command_for(ppd, size, False))
        if not got or got[2] != "pbmraw":
            continue
        tool, args, _ = got
        c = capture(command_for(ppd, size, True)) if color else None
        # foo2* tell pksmraw from bitcmyk by the input itself, so the filter always sends planes
        if color and (not c or c[2] not in ("pksmraw", "bitcmyk")):
            continue
        grays[size] = " ".join(args)
        if c:
            colors[size] = " ".join(c[1])
        rows.append(size)
    if not rows:
        return None
    res = re.search(r"-r(\d+)x(\d+)", next(iter(grays.values())))
    dpi = f"{res.group(1)}x{res.group(2)}dpi"
    page = "A4" if "A4" in rows else rows[0]
    brand = name.split()[0]
    device = re.search(r'^\*1284DeviceID:\s*"(.*)"', ppd, re.M)
    text = ['*PPD-Adobe: "4.3"', '*FormatVersion: "4.3"', '*FileVersion: "1.0"', '*LanguageVersion: English',
            '*LanguageEncoding: ISOLatin1', '*PCFileName: "FOO2.PPD"', f'*Manufacturer: "{brand}"',
            f'*Product: "({name})"', f'*ModelName: "{name}"', f'*ShortNickName: "{name[:31]}"',
            f'*NickName: "{name} - Apple Silicon"', '*PSVersion: "(3010.000) 0"', '*LanguageLevel: "3"',
            f'*ColorDevice: {"True" if color else "False"}', f'*DefaultColorSpace: {"CMYK" if color else "Gray"}',
            '*FileSystem: False', '*Throughput: "1"', '*LandscapeOrientation: Plus90', '*TTRasterizer: Type42',
            '*cupsVersion: 1.4', '*cupsModelNumber: 0', '*cupsManualCopies: False',
            f'*cupsFilter: "application/vnd.cups-raster 0 {LIBEXEC}/rastertofoo-{tool}"']
    if device:
        text.append(f'*1284DeviceID: "{device.group(1)}"')
    if name in FIRMWARE:
        text.append(f'*foo2Firmware: "{FIRMWARE[name]}"')
    for key, label in (("PageSize", "Media Size"), ("PageRegion", "Media Size")):
        text += [f"*OpenUI *{key}/{label}: PickOne", f"*OrderDependency: 10 AnySetup *{key}", f"*Default{key}: {page}"]
        for s in rows:
            w, h = dims[s].split()
            text.append(f'*{key} {s}: "<</PageSize[{w} {h}]/ImagingBBox null>>setpagedevice"')
        text.append(f"*CloseUI: *{key}")
    text.append(f"*DefaultImageableArea: {page}")
    text += [f'*ImageableArea {s}: "{areas[s]}"' for s in rows]
    text.append(f"*DefaultPaperDimension: {page}")
    text += [f'*PaperDimension {s}: "{dims[s]}"' for s in rows]
    text += ["*OpenUI *Resolution/Resolution: PickOne", "*OrderDependency: 20 AnySetup *Resolution",
             f"*DefaultResolution: {dpi}",
             f'*Resolution {dpi}: "<</HWResolution[{res.group(1)} {res.group(2)}]>>setpagedevice"', "*CloseUI: *Resolution"]
    text += ["*OpenUI *ColorModel/Color Mode: PickOne", "*OrderDependency: 10 AnySetup *ColorModel",
             f"*DefaultColorModel: {'CMYK' if color else 'Gray'}", f'*ColorModel Gray/Grayscale: "{GRAY}"']
    if color:
        text.append(f'*ColorModel CMYK/Color: "{CMYK}"')
    text.append("*CloseUI: *ColorModel")
    text += [f'*foo2GrayArgs {s}: "{grays[s]}"' for s in rows]
    text += [f'*foo2Args {s}: "{colors[s]}"' for s in rows if s in colors]
    path.write_text("\n".join(text) + "\n")
    return tool


OUT.mkdir(parents=True, exist_ok=True)
made, skipped = {}, []
for src in sorted((SRC / "PPD").glob("*.ppd")):
    if src.stem in SKIP:
        continue
    ppd = src.read_text(errors="replace")
    name = model_name(ppd)
    if name.lower() in known:
        skipped.append(f"{name} (already supported)")
        continue
    mid = "foo2-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    tool = write_ppd(OUT / f"{mid}.ppd", name, ppd)
    if tool:
        made.setdefault(tool, []).append(name)
    else:
        skipped.append(f"{name} (wrapper gave no usable arguments)")
for t, names in sorted(made.items()):
    print(f"{t}: {len(names)}")
print("skipped:", *skipped, sep="\n  ")
print(f"total: {sum(map(len, made.values()))}")
