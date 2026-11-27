#!/usr/bin/env python3
"""Generates the GitHub Pages site in docs/ from docs/models.json.

  python3 site/build-site.py
"""
import json, re, html, datetime, pathlib, collections, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fix_guides import FIX_GUIDES, tier1_extra_notes

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "https://macprinterdrivers.com"
REPO = "https://github.com/theshiver/apple-silicon-printer-drivers"
RELEASE = f"{REPO}/releases/latest"
PKG = "AppleSilicon-Printer-Drivers-2.0.6.pkg"
TODAY = datetime.date.today().isoformat()

models = json.load(open(DOCS / "models.json"))

# lastmod moves only when a page's HTML actually changes; a sitemap where every URL is "today" gets ignored
OLD_LASTMOD = {}
for f in DOCS.glob("sitemap*.xml"):
    OLD_LASTMOD.update(re.findall(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>", f.read_text()))
LASTMOD = {}
def write_page(d, text, url):
    d.mkdir(parents=True, exist_ok=True)
    f = d / "index.html"
    changed = not f.exists() or f.read_text() != text
    if changed:
        f.write_text(text)
    LASTMOD[url] = TODAY if changed else OLD_LASTMOD.get(url, TODAY)

# brand normalisation: first word of the display name, with a few fixes
ALIAS = {"Dai": "DNP", "PIXMA": "Canon", "imageRunner": "Canon", "Phaser": "Xerox",
         "e-Studio": "Toshiba", "MP": "Ricoh", "Datamax-ONeil": "Datamax", "TASKalfa": "Kyocera",
         "Konica": "Konica Minolta", "Fuji": "Fuji Xerox"}
def brand_of(m):
    b = m["name"].split()[0]
    return ALIAS.get(b, b)

by_brand = collections.defaultdict(list)
for m in models:
    by_brand[brand_of(m)].append(m)
# only brands with a handful of models get their own page
BRANDS = sorted([b for b, l in by_brand.items() if len(l) >= 4], key=lambda b: -len(by_brand[b]))
POPULAR = ["Canon","Epson","HP","Brother","Samsung","Lexmark","Xerox","Kyocera","Ricoh","Oki","Dell","Sharp","Kodak","Sony","Mitsubishi","DNP","Fujifilm","Panasonic"]
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.replace("+", " plus").lower()).strip("-")
GUTENPRINT, BRLASER, SPLIX, FOO2 = "5.3.5", "6.2.8", "2.0.2", "20200505"
# Every page except the model pages comes in these languages; text lives in site/i18n/<lang>.json
LANGS = ["en", "de", "fr", "es", "it", "pl", "ru", "tr"]
T = {l: json.load(open(ROOT / "site/i18n" / f"{l}.json")) for l in LANGS}
P = lambda l: "" if l == "en" else f"{l}/"
def alts_for(path):
    return {l: f"{BASE}/{P(l)}{path}" for l in LANGS}
def fill(text, **kw):
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text
SEP = {"en": ",", "de": ".", "es": ".", "it": ".", "tr": ".", "fr": "\u00a0", "pl": "\u00a0", "ru": "\u00a0"}
num = lambda n, l: f"{n:,}".replace(",", SEP[l])
# Bing flags titles over 70 chars and Google cuts around 60: take the first candidate that fits
def fit(*titles, limit=65):
    return next((t for t in titles if len(t) <= limit), titles[-1])
VERSION = re.search(r"-(\d+(?:\.\d+)+)\.pkg$", PKG).group(1)
PKG_URL = f"{REPO}/releases/download/v{VERSION}/{PKG}"  # the file itself, not the GitHub release page
BREW_CMD = "brew install --cask theshiver/tap/apple-silicon-printer-drivers"
POST_1 = "https://www.reddit.com/r/MacOS/comments/1wkofbi/old_printer_says_software_is_not_compatible_with/"
POST_2 = "https://www.reddit.com/r/MacOS/comments/1xpa11l/update_on_the_free_fix_for_software_is_not/"

REDDIT_REVIEWS = [
    ("u/Ancient_Practice9585", "Brother HL-L2340DW", POST_1,
     "It worked on my HL-L2340DW after the os27 update rendered my printer obsolete. The printer has always been solid, so I was so upset to lose it. Thank you, thank you, thank you!"),
    ("u/Dramatic_Ice5101", "Samsung ML-1865W", POST_1,
     "Samsung ML-1865W worked right away! The printer worked perfectly until a few months ago and nothing would fix it until this. I have a Mac Mini (2023) running macOS 27. Thank you!"),
    ("u/Prestigious-Low3224", "Samsung ML-1630", POST_1,
     "FANTASTIC! No more Pacifist and OS X 10.6 Intel driver shenanigans! Thank you so much, I am gonna go update to that as soon as I get back home"),
    ("u/moagul", "HP LaserJet Pro M201dw", POST_1,
     "Hey! Thanks for responding and updating the list. Works perfectly! I know the AirPrint works. But I had been using the printer via USB (Faster that way). Now, I'm back to using it via USB thanks to you! :)"),
    ("u/archiecstll", "Brother DCP-8080DN", POST_2,
     "Looks like it works. Thank you so very much! Worth a coffee for sure"),
    ("u/nick-parker", "Canon G3010 · AirPrint", POST_2,
     "After installing the app, i see it as an airprint printer in my iPhone! Yay!"),
    ("u/smallduck", "Classic Mac Driver Dev", POST_1,
     "As a developer in the 1990s of classic Mac printer drivers for otherwise unsupported devices, I say: kudos."),
    ("u/jonassfe", "HP LaserJet 1022", POST_1,
     "I just used this with an HP LaserJet 1022. It worked great. Thanks!"),
    ("u/zemvpferreira", "Brother HL-2010W", POST_1,
     "Brother HL-2010W working perfectly. You're amazing."),
    ("u/littlegeckoo", "Canon PIXMA MP240", POST_1,
     "I just printed a page with my old Canon MP240 and it worked. Thanks"),
]

INDEXNOW_KEY = "a3007c2aad3307cf8925b08255b5b513"
# HP LaserJets that keep their firmware in RAM: the PPD names the file to send at power on
FOO2_PPDS = {p.stem: p.read_text() for p in (ROOT / "pkgroot/Library/Printers/Gutenprint/share/foo2zjs/ppd").glob("*.ppd")}
FIRMWARE_MODELS = {k for k, v in FOO2_PPDS.items() if "*foo2Firmware:" in v}
def driver_name(mid):
    return "brlaser" if mid.startswith("brlaser-") else "SpliX" if mid.startswith("splix-") else "foo2zjs" if mid.startswith("foo2-") else "Gutenprint"

def model_path(m):
    """canon/pixma-ip4300 — mirrored by modelPath() in the home page search script."""
    w = m["name"].split()[0]
    b = ALIAS.get(w, w)
    # a two-word brand ("Fuji Xerox") shouldn't repeat its second word in the model part
    rest = m["name"][len(b if m["name"].startswith(b + " ") else w):]
    return f"{slug(b)}/{slug(rest) or slug(m['name'])}"
INDEXED_BRANDS_ALL_LANGS = {
    "Canon", "Epson", "HP", "Brother", "Samsung", "Xerox", "Kyocera",
    "Ricoh", "Oki", "Konica Minolta", "Lexmark", "Dell", "Sharp", "Apple",
}
INDEXED_BRANDS_EN_ONLY = {"Toshiba", "Fuji Xerox", "Panasonic", "Kodak", "Sony", "Generic"}
INDEXED_MODELS = {
    "samsung/m2020-series", "samsung/scx-3400", "samsung/ml-1640", "samsung/ml-2240",
    "samsung/m267x-287x-series", "samsung/ml-1865", "samsung/ml-2010", "samsung/ml-2160",
    "samsung/ml-2165", "samsung/clp-310",
    "brother/hl-1210w-series", "brother/hl-2130-series", "brother/hl-2030-series",
    "brother/hl-2270dw-series", "brother/hl-l2310d-series", "brother/hl-1110-series",
    "brother/hl-2240-series", "brother/dcp-7030", "brother/dcp-7055w", "brother/dcp-7065dn",
    "brother/dcp-1610w-series", "brother/mfc-7460dn", "brother/dcp-l2510d-series",
    "brother/dcp-l2520dw-series", "brother/hl-l2300d-series",
    "canon/pixma-g3010", "canon/pixma-mp250", "canon/mg2500-series", "canon/pixma-ip4300",
    "canon/pixma-ip4700", "canon/pixma-ip110", "canon/pixma-mx885", "canon/mp490-series",
    "canon/pixma-ix6550", "canon/pixma-mg4250", "canon/mg3600-series", "canon/pixma-mp280",
    "canon/pixma-ip2700", "canon/pixma-ts3140",
    "hp/laserjet-1010", "hp/laserjet-1018", "hp/laserjet-1020", "hp/laserjet-p1005",
    "hp/laserjet-p1006", "hp/laserjet-pro-m12w", "hp/laserjet-pro-p1102",
    "hp/laserjet-pro-p1102w", "hp/laserjet-pro-m1132s-mfp", "hp/laserjet-1022",
    "hp/laserjet-1320",
    "xerox/phaser-3020", "xerox/workcentre-3025", "xerox/workcentre-6015",
    "xerox/phaser-3140",
    "epson/stylus-photo-r300", "epson/workforce-610", "epson/stylus-dx5000",
    "generic/pcl-color-laser", "generic/pcl-6-pcl-xl-printer", "generic/pcl-4-lf-printer",
}
assert len({model_path(m) for m in models}) == len(models), "model page paths collide"
assert INDEXED_MODELS.issubset({model_path(m) for m in models}), "indexed model path missing from models.json"

GA_ID = "G-RL7H0KSZYM"
CSS = """
:root{color-scheme:light dark;--bg:#fff;--band:#f5f6f8;--card:#fff;--elevated:#eef1f6;--fg:#111827;--muted:#525d6f;--line:#e2e6ed;--accent:#0071e3;--accent-hover:#0062c4;--accent-soft:#e8f2ff;--code:#f1f3f7;--ok:#15803d;--ok-soft:#e8f7ee;--bad:#dc2626;--bad-soft:#fef2f2;--btn-bg:#0071e3;--btn-fg:#fff;--shadow:0 12px 32px rgba(17,24,39,.08)}
@media(prefers-color-scheme:dark){:root{--bg:#0d1015;--band:#131720;--card:#161b22;--elevated:#1d2430;--fg:#e6edf3;--muted:#9aa5b5;--line:#29313d;--accent:#58a6ff;--accent-hover:#79b8ff;--accent-soft:rgba(88,166,255,.14);--code:#1c222b;--ok:#4ade80;--ok-soft:rgba(74,222,128,.12);--bad:#f87171;--bad-soft:rgba(248,113,113,.14);--btn-bg:#58a6ff;--btn-fg:#0b1a2b;--shadow:0 14px 36px rgba(0,0,0,.45)}}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--fg);font:16.5px/1.6 -apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
a{color:var(--accent)}button{font:inherit;cursor:pointer}
.wrap{max-width:1100px;margin:0 auto;padding:0 20px}.wrap.narrow{max-width:940px}.page-pad{padding:28px 20px 52px}
.band{background:var(--band);border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:54px 0}.sec{padding:54px 0}
header.site-nav{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}
.header-in{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px;min-height:62px;padding:8px 0}
.brand-logo{display:inline-flex;align-items:center;gap:9px;color:var(--fg);text-decoration:none;font-weight:750;font-size:16px;letter-spacing:-.01em;margin-right:auto}
.brand-icon{width:30px;height:30px;border-radius:8px;background:var(--accent-soft);color:var(--accent);display:grid;place-items:center;flex:none}
header nav{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px}
header nav a{color:var(--muted);text-decoration:none;font-size:.92rem;font-weight:500}
header nav a:hover{color:var(--fg)}
header nav a.nav-coffee{background:var(--band);color:var(--fg);border:1px solid var(--line);padding:5px 11px;border-radius:999px;font-size:.86rem;font-weight:550;white-space:nowrap}
header nav a.nav-coffee:hover{border-color:var(--accent);color:var(--accent)}
header nav a.nav-cta{background:var(--btn-bg);color:var(--btn-fg);padding:7px 15px;border-radius:999px;font-weight:650;font-size:.88rem;white-space:nowrap}
header nav a.nav-cta:hover{filter:brightness(1.08);color:var(--btn-fg)}
h1{font-size:clamp(1.95rem,4vw,2.8rem);line-height:1.1;letter-spacing:-.025em;margin:.2em 0 .4em;font-weight:750}
h2{font-size:clamp(1.4rem,2.6vw,1.9rem);line-height:1.2;letter-spacing:-.02em;margin:0 0 .35em}
.page-pad h2{margin-top:2em}
h3{font-size:1.05rem;margin:0 0 .35em}
p.lead{font-size:1.12rem;color:var(--muted);margin-top:0;max-width:58ch}.sub{color:var(--muted);margin:0 0 24px;max-width:64ch}.note{color:var(--muted);font-size:.92rem}
.eyebrow{display:inline-flex;align-items:center;gap:8px;background:var(--accent-soft);color:var(--accent);font-size:12px;font-weight:700;padding:5px 12px;border-radius:999px;letter-spacing:.01em;margin-bottom:12px}
.hero{display:grid;gap:34px;align-items:center;padding:42px 0 48px}@media(min-width:900px){.hero{grid-template-columns:1.22fr 1fr}}
.cta-row{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin:14px 0}
a.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;background:var(--btn-bg);color:var(--btn-fg);font-size:1.05rem;font-weight:650;text-decoration:none;padding:13px 24px;border-radius:12px}
a.btn:hover{filter:brightness(1.08)}a.btn:focus-visible,summary:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
.brew-chip{display:inline-flex;align-items:center;gap:8px;background:var(--code);border:1px solid var(--line);border-radius:10px;padding:8px 11px;font:12.5px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--fg);max-width:100%;overflow:auto}
.brew-chip button{background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:3px 8px;font-family:-apple-system,sans-serif;font-size:11.5px;font-weight:600;flex:none}
.trust-strip{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:.88rem;color:var(--muted);margin-top:8px}
.mac-win{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--shadow);overflow:hidden}
.mac-titlebar{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 14px;background:var(--elevated);border-bottom:1px solid var(--line)}
.dots{display:flex;gap:6px}.dots i{width:11px;height:11px;border-radius:50%;display:block}.dots i:nth-child(1){background:#ff5f57}.dots i:nth-child(2){background:#febc2e}.dots i:nth-child(3){background:#28c840}
.mac-title{font-size:12.5px;font-weight:600;color:var(--muted)}
.seg{display:inline-flex;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:2px}
.seg button{border:0;background:transparent;color:var(--muted);font-size:11.5px;font-weight:600;padding:4px 10px;border-radius:6px}
.seg button.active{background:var(--btn-bg);color:var(--btn-fg)}
.mac-body{padding:18px}
.printer-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:13px;border-radius:12px;border:1px solid var(--line);background:var(--bg)}
.printer-meta{display:flex;align-items:center;gap:12px}.printer-badge{width:40px;height:40px;border-radius:10px;background:var(--elevated);display:grid;place-items:center;color:var(--muted);flex:none}
.printer-row h4{margin:0;font-size:15px}.printer-row small{color:var(--muted);font-size:12.5px}
.status-banner{margin-top:12px;padding:11px 14px;border-radius:10px;font-size:13.5px;font-weight:600}
.status-banner.bad{background:var(--bad-soft);color:var(--bad);border:1px solid color-mix(in srgb,var(--bad) 25%,transparent)}
.status-banner.good{background:var(--ok-soft);color:var(--ok);border:1px solid color-mix(in srgb,var(--ok) 25%,transparent)}
.mac-foot{margin-top:11px;font-size:12px;color:var(--muted);display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px}
input[type=search]{width:100%;font-size:1.05rem;padding:13px 15px;border:1.5px solid var(--line);border-radius:12px;background:var(--card);color:var(--fg)}input[type=search]:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
#results{list-style:none;padding:0;margin:8px 0 0;display:grid;gap:6px}
#results li{padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:.95rem}
#results li span{font-size:.8rem;color:var(--muted);font-weight:600}
#results li:hover,#results li.sel{border-color:var(--accent);background:var(--accent-soft)}
.search-result{background:var(--ok-soft);border:1px solid color-mix(in srgb,var(--ok) 35%,transparent);border-radius:12px;padding:14px 16px;margin-top:10px;font-size:.95rem}
.search-result h3{margin:0 0 6px;color:var(--ok)}
.dl{background:var(--band);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:20px 0}.hero .dl{background:none;border:0;padding:0;margin:0}
.dl .ok{font-size:1.05rem;font-weight:600;margin:0 0 12px;color:var(--ok)}.dl .trust{color:var(--muted);font-size:.9rem;margin:10px 0 12px}
.rev-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:flex-end;gap:12px;margin-bottom:18px}
.rev-head .sub{margin-bottom:0}.rev-nav{display:flex;gap:8px}
.rev-nav button{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--fg);font-weight:700;display:grid;place-items:center}
.rev-nav button:hover{border-color:var(--accent);color:var(--accent)}
.spotlight-quote{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:14px;padding:18px 22px;margin-bottom:18px;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:14px}
.spotlight-quote blockquote{margin:0;font-size:1.15rem;font-weight:650;letter-spacing:-.01em}.spotlight-quote .qmeta{font-size:.85rem;color:var(--muted);margin-top:3px}
.reviews-track{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;scroll-behavior:smooth;padding:4px 2px 12px;-webkit-overflow-scrolling:touch}
.reviews-track::-webkit-scrollbar{height:6px}.reviews-track::-webkit-scrollbar-thumb{background:var(--line);border-radius:999px}
.tcard{flex:0 0 min(84vw,330px);scroll-snap-align:start;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;display:flex;flex-direction:column;justify-content:space-between;gap:14px}
.tcard p{margin:0;font-size:.93rem;line-height:1.55}
.tcard-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:.8rem;color:var(--muted);border-top:1px solid var(--line);padding-top:10px}
.tcard-foot a{text-decoration:none;color:var(--muted)}.tcard-foot a:hover{color:var(--accent)}
.mpill{background:var(--elevated);color:var(--fg);padding:3px 9px;border-radius:6px;font-weight:600;font-size:.78rem;text-decoration:none;white-space:nowrap}
.timeline{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
.mstone{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.mstone .ver{display:inline-block;font-size:.75rem;font-weight:700;color:var(--accent);background:var(--accent-soft);padding:2px 8px;border-radius:999px;margin-bottom:8px}
.mstone strong{display:block;font-size:.95rem;margin-bottom:4px}.mstone span{font-size:.86rem;color:var(--muted);display:block}
.mstone.req{background:var(--accent-soft);border-color:color-mix(in srgb,var(--accent) 30%,transparent)}
ol.quick{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;list-style:none;padding:0;margin:0;counter-reset:q}
ol.quick li{counter-increment:q;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;font-size:.95rem}
ol.quick li::before{content:counter(q);display:inline-grid;place-items:center;width:1.7em;height:1.7em;margin-right:8px;border-radius:50%;background:var(--btn-bg);color:var(--btn-fg);font-weight:700;font-size:.85rem}
@media(max-width:640px){ol.quick{grid-template-columns:1fr}a.btn{width:100%}}
.air-box{display:grid;gap:28px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:26px}@media(min-width:860px){.air-box{grid-template-columns:1.18fr 1fr}}
.promo{background:var(--band);border:1px solid var(--line);border-radius:18px;padding:22px 24px;margin:28px 0;display:grid;gap:20px;align-items:center}@media(min-width:800px){.promo{grid-template-columns:1.3fr 1fr}}.promo h2{margin:0 0 .3em}.promo p{margin:0 0 .6em}
.sw-win{background:var(--band);border:1px solid var(--line);border-radius:14px;padding:16px}
.sw-head{font-weight:700;font-size:.92rem;margin-bottom:2px}.sw-sub{font-size:.78rem;color:var(--muted);margin-bottom:10px}
.app{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:4px 12px}
.app div{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--line);line-height:1.25}.app div:last-child{border:0}
.app strong{display:block;font-size:.92rem}.app small{display:block;font-size:.8rem;font-weight:500}.app small.on{color:var(--ok)}.app small.off{color:var(--muted)}
button.toggle{flex:none;width:40px;height:23px;border:0;border-radius:999px;background:var(--line);position:relative;transition:background .15s}
button.toggle::after{content:"";position:absolute;left:2px;top:2px;width:19px;height:19px;border-radius:50%;background:#fff;transition:transform .15s;box-shadow:0 1px 3px rgba(0,0,0,.25)}
button.toggle.on{background:var(--btn-bg)}button.toggle.on::after{transform:translateX(17px)}
.brand-grid{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(160px,1fr))}
.bcard{display:flex;justify-content:space-between;align-items:center;padding:11px 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);text-decoration:none;color:var(--fg);font-size:.93rem;font-weight:600}
.bcard:hover{border-color:var(--accent);color:var(--accent)}.bcard span{font-size:.8rem;color:var(--muted);font-weight:500}
.cards{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.cards div{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}.cards strong{display:block;margin-bottom:6px}
.card{background:var(--band);border:1px solid var(--line);border-radius:16px;padding:18px 22px;margin:18px 0}
.brands a,.pill-links a{display:inline-block;margin:4px 8px 4px 0}
.pill-links a{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:5px 12px;text-decoration:none;font-size:.88rem;color:var(--fg)}
.pill-links a:hover{border-color:var(--accent);color:var(--accent)}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.93rem}td,th{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:.03em;background:var(--elevated)}
tbody tr:first-child{background:var(--ok-soft);font-weight:600}tbody tr:last-child td{border-bottom:0}
.langs{position:relative;font-size:.9rem;color:var(--muted)}.langs summary{list-style:none;cursor:pointer}.langs summary::after{content:" ▾"}.langs summary::-webkit-details-marker{display:none}
.langs div{position:absolute;right:0;z-index:60;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:6px 12px;display:grid;gap:4px;min-width:120px;box-shadow:var(--shadow)}
.models{columns:3 220px;list-style:none;padding:0;margin:0}.models li{padding:3px 0;break-inside:avoid}
main details:not(.langs){border-bottom:1px solid var(--line);padding:13px 0}main details:not(.langs) summary{cursor:pointer;font-weight:600}main details:not(.langs) p{margin:.6em 0 .2em;color:var(--muted)}
pre,code{font:.9em ui-monospace,SFMono-Regular,Menlo,monospace}pre{background:var(--code);padding:12px 14px;border-radius:10px;overflow:auto;position:relative;border:1px solid var(--line)}code{background:var(--code);padding:1px 5px;border-radius:4px}pre code{background:none;padding:0}
button.copy{position:absolute;top:8px;right:8px;font-size:.78rem;padding:4px 8px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px}
.hidden{display:none}ol.steps li{margin:.4em 0}
.footer-cards{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));margin-top:28px}.footer-cards .card{margin:0}
#dl-toast{position:fixed;right:18px;bottom:18px;z-index:80;max-width:360px;background:var(--card);border:1px solid var(--line);border-left:4px solid var(--ok);border-radius:14px;padding:14px 16px;box-shadow:0 10px 30px #0003;display:none}
#dl-toast.show{display:block}#dl-toast p{margin:0 0 8px;font-size:.94rem}#dl-toast .t-act{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
#dl-toast a.t-btn{display:inline-block;background:var(--band);color:var(--accent);font-weight:600;text-decoration:none;padding:6px 12px;border-radius:8px;font-size:.9rem}
#dl-toast button{margin-left:auto;background:none;border:0;color:var(--muted);font-size:1rem;padding:2px 6px}
footer{color:var(--muted);font-size:.88rem;margin-top:36px;border-top:1px solid var(--line);padding:20px 0 42px}
"""

# Owner's decision (2026-11-05): GA runs for every visitor, no consent bar. Advertising features stay off.
# The automatic page_view ignores custom params, so brand and model pages send their own printer_page event.
TRACK_JS = """(function(){var G='%s',d=document;
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
var s=d.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+G;d.head.appendChild(s);
var P=JSON.parse(d.body.dataset.track||'{}');gtag('js',new Date());gtag('config',G,{allow_google_signals:false,allow_ad_personalization_signals:false});if(P.printer_brand)gtag('event','printer_page',P);
window.track=function(n,p){gtag('event',n,Object.assign({},P,p))};
function showToast(){var t=d.getElementById('dl-toast');if(!t){t=d.createElement('div');t.id='dl-toast';t.setAttribute('role','status');t.innerHTML='<p><strong>Download started.</strong> Open the .pkg file to install, then print. Once it works, if it saved you a new printer and you\\x27d like to say thanks:</p><div class="t-act"><a class="t-btn" href="https://buymeacoffee.com/cancetin" data-loc="post_download">☕ Buy me a coffee →</a><button type="button" aria-label="Dismiss">✕</button></div>';t.querySelector('button').onclick=function(){t.classList.remove('show')};d.body.appendChild(t)}t.classList.add('show')}
d.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href$=".pkg"]');if(a){track('driver_download',{link_location:a.dataset.loc||'nav'});showToast()}});
d.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href*="buymeacoffee.com/cancetin"]');if(a)track('coffee_click',{link_location:a.dataset.loc||'other'})});
d.addEventListener('toggle',function(e){var s=e.target.querySelector&&e.target.querySelector('summary');if(e.target.open&&s&&e.target.closest('main'))track('faq_open',{question:s.textContent.slice(0,100)})},true);
})();""" % GA_ID

UI_JS = """(function(){var d=document;
d.querySelectorAll('.js-air-toggle').forEach(function(btn){btn.addEventListener('click',function(){var on=btn.classList.toggle('on'),row=btn.closest('div'),st=row&&row.querySelector('.js-air-status');if(st){st.textContent=on?btn.dataset.on:btn.dataset.off;st.className=on?'on js-air-status':'off js-air-status'}})});
d.querySelectorAll('.js-copy').forEach(function(btn){btn.addEventListener('click',async function(){try{await navigator.clipboard.writeText(btn.dataset.copy);var prev=btn.textContent;btn.textContent=btn.dataset.done||'Copied';setTimeout(function(){btn.textContent=prev},1500)}catch(e){}})});
d.querySelectorAll('button.copy').forEach(function(b){b.onclick=async function(){try{await navigator.clipboard.writeText(b.nextElementSibling.textContent);b.textContent='Copied';setTimeout(function(){b.textContent='Copy'},1500)}catch(e){}}});
var trk=d.getElementById('reviews-track');
if(trk){var prev=d.getElementById('rev-prev'),next=d.getElementById('rev-next');if(prev)prev.onclick=function(){trk.scrollBy({left:-350,behavior:'smooth'})};if(next)next.onclick=function(){trk.scrollBy({left:350,behavior:'smooth'})}}
d.querySelectorAll('.js-ba').forEach(function(btn){btn.addEventListener('click',function(){d.querySelectorAll('.js-ba').forEach(function(b){b.classList.remove('active')});btn.classList.add('active');var after=btn.dataset.mode==='after',w=btn.closest('.mac-win');if(!w)return;w.querySelector('.js-ba-name').textContent=after?'Canon MP250 series - Apple Silicon':'Canon MP250 series';w.querySelector('.js-ba-sub').textContent=after?w.dataset.subGood:w.dataset.subBad;var bn=w.querySelector('.js-ba-banner');bn.className='status-banner js-ba-banner '+(after?'good':'bad');bn.textContent=(after?'✓ ':'✕ ')+(after?w.dataset.msgGood:w.dataset.msgBad);w.querySelector('.js-ba-foot').textContent=after?w.dataset.footGood:w.dataset.footBad})});
})();"""

COFFEE = "https://buymeacoffee.com/cancetin"
PRINTER_SVG = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>'

def coffee_card(lang="en"):
    t = T[lang]
    return f'<div class="card"><strong>{t["coffee_title"]}</strong><br>{t["coffee_body"]} <a href="{COFFEE}" data-loc="card">{t["coffee_btn"]} →</a></div>'

def trust_box(lang="en"):
    t = T[lang]
    return f'<div class="card"><strong>{t["trust_title"]}</strong><br>{fill(t["trust_body"], repo=REPO)}</div>'

def page(title, desc, canonical, body, jsonld=None, keywords="", robots="", googlebot="", lang="en", alts=None, track=None, wide=False):
    """alts: {lang: url} of every language version including this one; emits hreflang and a language switch."""
    t = T[lang]; pre = f"{BASE}/{P(lang)}"
    data = html.escape(json.dumps({"page_type": "other", **(track or {})}), quote=True)
    hreflang = "".join(f'<link rel="alternate" hreflang="{l}" href="{u}">' for l, u in (alts or {}).items())
    if alts:
        hreflang += f'<link rel="alternate" hreflang="x-default" href="{alts["en"]}">'
    switch = ""
    if alts:
        links = "".join(f'<a href="{u}" hreflang="{l}" lang="{l}">{T[l]["lang_name"]}</a>' for l, u in alts.items() if l != lang)
        switch = f'<details class="langs"><summary>{t["lang_name"]}</summary><div>{links}</div></details>'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, separators=(",",":"))}</script>' if jsonld else ""
    # home pages only: in the shared footer this would move lastmod on every URL for a credit link
    credit = ""
    if (track or {}).get("page_type") == "home":
        credit = f' · <a href="https://cancetin.com/{"tr/" if lang == "tr" else ""}">Can Çetin</a>'
    main_html = body if wide else f'<div class="wrap narrow page-pad">{body}</div>'
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{f'<meta name="keywords" content="{html.escape(keywords)}">' if keywords else ''}
{f'<meta name="robots" content="{robots}">' if robots else ''}
{f'<meta name="googlebot" content="{googlebot}">' if googlebot else ''}
<link rel="canonical" href="{canonical}">{hreflang}
<meta property="og:type" content="website"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/not-compatible.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}/not-compatible.png">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
{ld}
<style>{CSS}</style>
</head>
<body data-track="{data}">
<header class="site-nav"><div class="wrap header-in"><a class="brand-logo" href="{pre}"><span class="brand-icon">{PRINTER_SVG}</span>Mac Printer Drivers</a>
<nav><a href="{pre}#search">{t["nav_check"]}</a><a href="{pre}print-from-iphone/">{t["nav_iphone"]}</a><a href="{pre}troubleshooting/">{t["nav_help"]}</a><a href="{REPO}">GitHub</a><a class="nav-coffee" href="{COFFEE}" data-loc="header">{t["nav_coffee"]}</a>{switch}<a class="nav-cta" href="{PKG_URL}" data-loc="header">⬇ {t["nav_dl"]} v{VERSION}</a></nav></div></header>
<main>
{main_html}
</main>
<div class="wrap"><footer><a href="{pre}brands/">{t["all_brands"]}</a> · <a href="{REPO}">GitHub</a> · <a href="{COFFEE}" data-loc="footer">{t["nav_coffee"]}</a> · <a href="{pre}privacy/">{t["privacy"]}</a>{credit}<br>{t["footer_note"]}</footer></div>
<script>{TRACK_JS}{UI_JS}</script>
</body></html>"""

def quick_steps(lang="en"):
    return f'<ol class="quick">{"".join(f"<li>{x}</li>" for x in T[lang]["steps"])}</ol>'
def download_card(ok="", lang="en", steps=True):
    """The answer people came for, above everything else: one button, three steps."""
    t = T[lang]
    after = fill(t["dl_after"], help_url=f"{BASE}/{P(lang)}troubleshooting/")
    return (f'<div class="dl">{f"<p class=ok>✅ {ok}</p>" if ok else ""}<a class="btn" href="{PKG_URL}" data-loc="card">⬇ {t["dl_btn"]}</a>'
            f'<p class="trust">{t["dl_trust"]}</p>{quick_steps(lang) if steps else ""}</div>\n' + (f'<p class="note">{after}</p>' if steps else ""))
def faq_list(qa):
    """Questions stay in the HTML for search engines and find-in-page, but the page reads short."""
    return "\n".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in qa)
def cards(rows):
    return '<div class="cards">' + "".join(f"<div><strong>{t}</strong>{d}</div>" for t, d in rows) + "</div>"

MACOS = "macOS 27 Golden Gate, macOS 26 Tahoe and macOS 15 Sequoia"
def model_list(ms):
    return '<ul class="models">' + "".join(f'<li><a href="{BASE}/{model_path(m)}/">{html.escape(m["name"])}</a></li>' for m in ms) + "</ul>"

def model_page(m, b, siblings, is_indexed=False):
    name, mid = m["name"], m["id"]
    esc = html.escape(name)
    path = model_path(m)
    brlaser, splix, foo2 = mid.startswith("brlaser-"), mid.startswith("splix-"), mid.startswith("foo2-")
    driver = (f'<a href="https://github.com/Owl-Maintain/brlaser">brlaser {BRLASER}</a>' if brlaser
              else f'<a href="https://github.com/OpenPrinting/splix">SpliX {SPLIX}</a>' if splix
              else f'<a href="https://packages.debian.org/source/sid/foo2zjs">foo2zjs {FOO2}</a>' if foo2
              else f'<a href="https://gimp-print.sourceforge.io/">Gutenprint {GUTENPRINT}</a>')
    brand_url = f"{BASE}/{slug(b)}/" if b in BRANDS else f"{BASE}/brands/"
    brand_label = f"{b} printers" if b in BRANDS else "All brands"
    notes = []
    if b == "Canon":
        notes.append("<p><strong>Had Canon's own driver installed?</strong> It leaves a small kernel extension behind that blocks macOS's USB printer driver. The installer moves it aside, nothing is deleted; restart the Mac once afterwards, then unplug and re-plug the printer.</p>")
    if b == "Epson" or mid.startswith("escp2-"):
        notes.append("<p><strong>Black missing or faint?</strong> Run a nozzle check from the printer first: a clogged or empty black cartridge is the usual cause, and this driver can't read ink levels like Epson's did. Then make sure no color-only mode is picked under Resolution or Ink Set in Printer Features.</p>")
    if brlaser:
        notes.append(f"<p>The {esc} is a Brother laser without PCL or AirPrint, so it uses the bundled native arm64 brlaser driver rather than Gutenprint. Duplex, toner save and resolution are in the print dialog under Printer Features.</p>")
    if splix:
        notes.append(f"<p>The {esc} speaks Samsung's SPL printer language rather than PCL or PostScript, so it uses the bundled native arm64 SpliX driver rather than Gutenprint. Toner save, density and resolution are in the print dialog under Printer Features.</p>")
    if foo2:
        notes.append(f"<p>The {esc} is a host-based printer that doesn't understand PCL or PostScript, so it uses the bundled native arm64 foo2zjs driver. {"Paper size and color mode are" if "*ColorModel CMYK" in FOO2_PPDS[mid] else "Paper size is"} in the print dialog. This driver is new and hasn't been tested on every model. If yours doesn't print, <a href=\"{REPO}/issues\">tell us</a> and we'll fix it.</p>")
    if mid in FIRMWARE_MODELS:
        notes.append(f"<p>The {esc} loses its firmware when switched off. The driver sends it again with the first job after power on, so that job takes a few seconds longer.</p>")
    extra_notes = tier1_extra_notes(m, b, mid, path, BASE) if is_indexed else ""
    sib = " · ".join(f'<a href="{BASE}/{model_path(s)}/">{html.escape(s["name"])}</a>' for s in siblings)
    title = fit(f"{name} Driver for Mac (macOS 27, Apple Silicon) – Free", f"{name} Driver for Mac (macOS 27, Apple Silicon)",
                f"{name} Driver for Mac (macOS 27)", f"{name} Mac Driver")
    desc = (f"Free native driver for the {name} on Apple Silicon Macs. Fixes “The printer software is not compatible "
            f"with this device” on {MACOS} without Rosetta. USB sets up automatically; Wi-Fi in a few clicks.")
    qa = [
        (f"Does the {name} work on macOS 27 Golden Gate, macOS 26 Tahoe and Apple Silicon?",
         f"Yes. This free package adds a native arm64 {driver_name(mid)} driver for the {name}. It runs on every Apple Silicon Mac with macOS 12 or later, including macOS 27 Golden Gate, without Rosetta."),
        (f"Do I need to write my own {name} driver?",
         f"No. The {name} is already supported by {driver_name(mid)}, an open source driver with years of tuning for this printer. Install the package; there is nothing to write, compile or patch."),
        (f"Why does my {name} say “The printer software is not compatible with this device”?",
         f"{b}'s Mac driver for the {name} is Intel-only, and macOS 27 Golden Gate marks Intel-only printer drivers as incompatible. Install this package, restart the Mac once, then unplug and re-plug the printer."),
    ]
    body = f"""
<p class="note"><a href="{BASE}/">Home</a> › <a href="{brand_url}">{html.escape(brand_label)}</a> › {esc}</p>
<h1>{esc} driver for Mac</h1>
<p class="lead">Works on Apple Silicon Macs with {MACOS}. One free installer, no Rosetta, nothing to compile.</p>
{download_card(f"The {esc} is supported")}
<h2>Wi-Fi, network, or not detected over USB</h2>
<ol class="steps"><li>Install the driver above.</li><li>Open System Settings → Printers &amp; Scanners and click Add.</li><li>Select your printer, then under Use choose Select Software…</li><li>Pick “{esc}” ending in “Apple Silicon” and click Add.</li></ol>
<p><strong>Print from your iPhone or iPad?</strong> Your Mac can share the {esc} over AirPrint. <a href="{BASE}/print-from-iphone/">See how →</a></p>
<h2>Why did my {esc} stop working?</h2>
<p>{html.escape(b)}'s own Mac driver for this printer was built for Intel Macs only. On Apple Silicon it ran through Rosetta, but macOS 27 Golden Gate marks Intel-only printer drivers as incompatible, so System Settings now says <em>“The printer software is not compatible with this device”</em>. This package replaces it with {driver}, compiled natively for Apple Silicon.</p>
{"".join(notes)}{extra_notes}
<p><strong>Print quality and black &amp; white:</strong> in the print dialog open Printer Features (Printer Options on macOS 27). Quality is under Resolution; for black &amp; white set Color Model to Grayscale. Ink and toner levels can't be shown by open source drivers.</p>
<h2>Questions</h2>
{faq_list(qa)}
<details><summary>Advanced: set it up from Terminal</summary>
<p>Driver: {driver} · Model id: <code>{html.escape(mid)}</code></p>
<pre><button class="copy">Copy</button><code>sudo gutenprint-add {html.escape(mid)}</code></pre>
<p>Network printer, with a name and its address:</p>
<pre><button class="copy">Copy</button><code>sudo gutenprint-add {html.escape(mid)} MyPrinter socket://192.168.1.50</code></pre>
</details>
{coffee_card()}
{f'<h2>Similar {html.escape(b)} models</h2><p>{sib}</p>' if sib else ''}
<p><a href="{brand_url}">← {html.escape(brand_label)}</a></p>
"""
    url = f"{BASE}/{path}/"
    crumbs = [("Home", f"{BASE}/"), (brand_label, brand_url), (name, url)]
    ld = [
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": f"{name} driver for macOS (Apple Silicon)",
         "operatingSystem": "macOS 12 or later (Apple Silicon)", "applicationCategory": "DriverApplication",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "downloadUrl": PKG_URL, "softwareVersion": VERSION},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement":
            [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity":
            [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]},
    ]
    return page(title, desc, url, body, ld,
                keywords=f"{name} driver mac, {name} mac driver, {name} macos 27, {name} macos 27 golden gate, {name} mac tahoe, {name} apple silicon, {name} m1, {b} printer driver mac",
                googlebot="" if is_indexed else "noindex, follow",
                track={"page_type": "model", "printer_brand": b, "printer_model": name})

# ---- write model pages
model_urls = []
for b, ms in by_brand.items():
    ms = sorted(ms, key=lambda m: m["name"].lower())
    for i, m in enumerate(ms):
        siblings = ms[max(0, i - 6):i] + ms[i + 1:i + 7]
        path = model_path(m)
        url = f"{BASE}/{path}/"
        is_indexed = path in INDEXED_MODELS
        write_page(DOCS / path, model_page(m, b, siblings, is_indexed=is_indexed), url)
        if is_indexed:
            model_urls.append(url)

# ---- every page except the model pages, in every language
by_name = {m["name"]: m for m in models}
POPULAR_MODELS = [by_name[n] for n in ("Brother HL-2270DW series", "Brother HL-1210W series", "Brother HL-1110 series", "Brother MFC-7460DN", "Brother DCP-7065DN",
    "Canon PIXMA MP250", "Canon PIXMA iP4300", "Canon PIXMA iP110", "Canon PIXMA MX885", "Canon MG2500 series",
    "Epson Stylus Photo R300", "Epson WorkForce 610", "HP LaserJet 1010", "Samsung ML-1865", "Samsung ML-2010")]
# Social proof is read from the GitHub API on every build (.pkg downloads across all releases, rounded down to 100;
# stars). The numbers below are the fallback when the API is unreachable or rate limited; a build never fails over them.
DOWNLOADS, STARS = 11600, 103
def github_counts():
    import urllib.request
    api = lambda p: json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.github.com/repos/theshiver/apple-silicon-printer-drivers{p}",
                                                                          headers={"User-Agent": "macprinterdrivers-site-build"}), timeout=15))
    dl = sum(a["download_count"] for r in api("/releases?per_page=100") for a in r["assets"] if a["name"].endswith(".pkg"))
    return dl // 100 * 100, api("")["stargazers_count"]
try:
    DOWNLOADS, STARS = github_counts()
except Exception as e:
    print(f"GitHub counts unavailable ({e}); using {DOWNLOADS}+ downloads and {STARS} stars")
# Four columns don't fit a phone, so rows become cards; only home pages need it, so it stays out of CSS
STACK_CSS = ("<style>@media(max-width:600px){table.stack,.stack tbody,.stack tr,.stack td{display:block}.stack thead{display:none}"
             ".stack tr{border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:10px 0}.stack td{border:0;padding:4px 0}"
             ".stack td:first-child{font-weight:600}.stack td:not(:first-child)::before{content:attr(data-l);display:block;color:var(--muted);font-size:.85rem}}</style>")
def mac_window(t):
    return f"""<div class="mac-win" data-sub-bad="{html.escape(t["ba_sub_bad"], quote=True)}" data-sub-good="{html.escape(t["ba_sub_good"], quote=True)}" data-msg-bad="{html.escape(t["mock_bad"], quote=True)}" data-msg-good="{html.escape(t["mock_good"], quote=True)}" data-foot-bad="{html.escape(t["ba_foot_bad"], quote=True)}" data-foot-good="{html.escape(t["ba_foot_good"], quote=True)}">
<div class="mac-titlebar"><div class="dots"><i></i><i></i><i></i></div><div class="mac-title">{html.escape(t["ba_title"])}</div>
<div class="seg"><button type="button" class="active js-ba" data-mode="before">{html.escape(t["ba_before"])}</button><button type="button" class="js-ba" data-mode="after">{html.escape(t["ba_after"])}</button></div></div>
<div class="mac-body">
<div class="printer-row"><div class="printer-meta"><div class="printer-badge">{PRINTER_SVG}</div><div><h4 class="js-ba-name">Canon MP250 series</h4><small class="js-ba-sub">{html.escape(t["ba_sub_bad"])}</small></div></div><span class="mpill">USB</span></div>
<div class="status-banner bad js-ba-banner">✕ {html.escape(t["mock_bad"])}</div>
<div class="mac-foot"><span class="js-ba-foot">{html.escape(t["ba_foot_bad"])}</span><span>{html.escape(t["ba_hint"])}</span></div>
</div></div>"""

def reviews_band(l):
    t = T[l]
    cards_html = "".join(
        f'<article class="tcard"><p lang="en">“{html.escape(quote)}”</p>'
        f'<div class="tcard-foot"><a href="{url}" rel="noopener">{html.escape(user)} · r/MacOS</a>'
        f'<span class="mpill">{html.escape(model)}</span></div></article>'
        for user, model, url, quote in REDDIT_REVIEWS
    )
    return f"""<section class="band" id="reviews"><div class="wrap">
<div class="rev-head"><div><h2>{fill(t["reviews_h2"], downloads=num(DOWNLOADS, l))}</h2><p class="sub">{t["reviews_sub"]}</p></div>
<div class="rev-nav"><button type="button" id="rev-prev" aria-label="{html.escape(t["reviews_prev"], quote=True)}">←</button><button type="button" id="rev-next" aria-label="{html.escape(t["reviews_next"], quote=True)}">→</button></div></div>
<div class="spotlight-quote"><div><blockquote lang="en">“Apple breaks the printer, random guy fixes 3670 of them. Classic”</blockquote><div class="qmeta">u/SoulfulDeer · 42 upvotes on r/MacOS</div></div>
<a class="mpill" href="{POST_2}" rel="noopener">{t["reviews_cta"]}</a></div>
<div class="reviews-track" id="reviews-track" tabindex="0">{cards_html}</div>
</div></section>"""

def story_section(l):
    t = T[l]; n = num(len(models), l)
    items = []
    for i, (ver, title, desc) in enumerate(t["story_steps"]):
        ver_f = fill(ver, n=n)
        if i == len(t["story_steps"]) - 1:
            items.append(f'<div class="mstone req"><span class="ver">{ver_f}</span><strong>{html.escape(title)}</strong><span><a href="{REPO}/issues">{html.escape(desc)}</a></span></div>')
        else:
            items.append(f'<div class="mstone"><span class="ver">{ver_f}</span><strong>{html.escape(title)}</strong><span>{html.escape(desc)}</span></div>')
    return f'<section class="sec"><div class="wrap"><h2>{t["story_h2"]}</h2><p class="sub">{t["story_sub"]}</p><div class="timeline">{"".join(items)}</div></div></section>'

def table(head, rows):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f'<td data-l="{html.escape(h, quote=True)}">{c}</td>' for h, c in zip(head, r)) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table class=stack><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
def app_mock(l):
    t = T[l]; on = html.escape(t["app_on"], quote=True); off = html.escape(t["app_off"], quote=True)
    return (f'<div class="sw-win"><div class="sw-head">Print from iPhone &amp; iPad</div><div class="sw-sub">{html.escape(t["airprint_hint"])}</div>'
            f'<div class="app"><div><span><strong>Canon PIXMA MP250</strong><small class="on js-air-status">{t["app_on"]}</small></span><button type="button" class="toggle on js-air-toggle" data-on="{on}" data-off="{off}" aria-label="Toggle Canon PIXMA MP250 AirPrint"></button></div>'
            f'<div><span><strong>HP LaserJet 1020</strong><small class="off js-air-status">{t["app_off"]}</small></span><button type="button" class="toggle js-air-toggle" data-on="{on}" data-off="{off}" aria-label="Toggle HP LaserJet 1020 AirPrint"></button></div></div></div>')
def iphone_promo(l):
    t = T[l]
    return (f'<section class="sec" id="airprint"><div class="wrap"><div class="air-box"><div><span class="eyebrow">{t["airprint_badge"]}</span>'
            f'<h2>{t["promo_title"]}</h2><p class="sub" style="margin-bottom:14px">{t["promo_body"]}</p>'
            f'<p class="note" lang="en" style="margin:0 0 16px"><em>“After installing the app, i see it as an airprint printer in my iPhone! Yay!”</em> · u/nick-parker (Canon G3010)</p>'
            f'<a class="btn" href="{BASE}/{P(l)}print-from-iphone/">{t["promo_link"]}</a></div>{app_mock(l)}</div></div></section>')
def faq_ld(qa):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}
def crumbs_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}
def search_script(t):
    return f"""<script>
const BASE={json.dumps(BASE)},ALIAS={json.dumps(ALIAS)};let MODELS=null,sel=-1,st;
const slug=s=>s.replace(/\\+/g,' plus').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
function modelPath(m){{const w=m.name.split(' ')[0],b=ALIAS[w]||w;return slug(b)+'/'+(slug(m.name.slice((m.name.startsWith(b+' ')?b:w).length))||slug(m.name))}}
function engineOf(id){{return id.startsWith('brlaser-')?'brlaser':id.startsWith('splix-')?'SpliX':id.startsWith('foo2-')?'foo2zjs':'Gutenprint'}}
const q=document.getElementById('q'),res=document.getElementById('results'),ans=document.getElementById('answer');
const norm=s=>s.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
async function load(){{if(!MODELS){{MODELS=await (await fetch('/models.json')).json();MODELS.forEach(m=>m.n=norm(m.name+' '+m.id));}}}}
function score(m,terms){{let s=0;for(const t of terms){{if(!m.n.includes(t))return 0;s+=(m.n.split(' ').includes(t)?3:1)}}return s+Math.max(0,20-m.name.length)/20}}
async function search(){{await load();const terms=norm(q.value).split(' ').filter(Boolean);res.innerHTML='';sel=-1;if(!terms.length)return;
 const hits=MODELS.map(m=>[score(m,terms),m]).filter(x=>x[0]>0).sort((a,b)=>b[0]-a[0]).slice(0,8);
 clearTimeout(st);st=setTimeout(()=>window.track&&track('printer_search',{{search_term:q.value.trim().slice(0,60),result_count:hits.length}}),1500);
 if(!hits.length){{res.innerHTML='<li style="cursor:default">'+{json.dumps(html.escape(t['search_nomatch']))}+'</li>';return}}
 for(const [,m] of hits){{const li=document.createElement('li');li.innerHTML=`<strong>${{m.name}}</strong><span>${{engineOf(m.id)}}</span>`;li.onclick=()=>show(m);res.appendChild(li)}}}}
function show(m){{res.innerHTML='';q.value=m.name; ans.classList.remove('hidden');window.track&&track('printer_select',{{printer_model:m.name}});
 ans.innerHTML=`<h3>✅ {fill(t['search_ok'], name='${m.name}')} · Native arm64 ${{engineOf(m.id)}}</h3>
 <p><a class="btn" href="{PKG_URL}" data-loc="search">⬇ {t['dl_btn']}</a></p>
 <p>{t['search_usb']} <a href="${{BASE}}/${{modelPath(m)}}/">{fill(t['search_more'], name='${m.name}')}</a></p>`;
 history.replaceState(null,'','#'+encodeURIComponent(m.id));ans.scrollIntoView({{behavior:'smooth',block:'center'}})}}
q.addEventListener('input',search);q.addEventListener('keydown',e=>{{const items=[...res.children];if(e.key==='ArrowDown'){{sel=Math.min(sel+1,items.length-1)}}else if(e.key==='ArrowUp'){{sel=Math.max(sel-1,0)}}else if(e.key==='Enter'){{if(items[sel]||items[0])(items[sel]||items[0]).click();return}}else return;items.forEach((li,i)=>li.classList.toggle('sel',i===sel));e.preventDefault()}});
function pick(){{const items=[...res.children];const it=items[sel]||items[0];if(it&&it.onclick)it.click()}}
document.getElementById('qf').addEventListener('submit',e=>{{e.preventDefault();pick()}});
q.addEventListener('search',pick);q.addEventListener('keyup',e=>{{if(e.key==='Enter')pick()}});
(async()=>{{const h=decodeURIComponent(location.hash.slice(1));if(h){{await load();const m=MODELS.find(x=>x.id===h);if(m)show(m)}}}})();
</script>"""

def is_brand_indexed(b, l):
    if b in INDEXED_BRANDS_ALL_LANGS:
        return True
    if b in INDEXED_BRANDS_EN_ONLY:
        return l == "en"
    return False

def fix_links_html():
    items = "".join(
        f'<li><a href="{BASE}/fix/{g["slug"]}/">{html.escape(g["h1"])}</a></li>'
        for g in FIX_GUIDES
    )
    return f"<h2>Common macOS printer error guides</h2><ul>{items}</ul>"

def brand_grid_html(l, bs):
    pre = f"{BASE}/{P(l)}"
    return '<div class="brand-grid">' + "".join(
        f'<a class="bcard" href="{pre}{slug(b)}/">{html.escape(b)}<span>{num(len(by_brand[b]), l)}</span></a>'
        for b in bs
    ) + "</div>"

def home_faq(l):
    t = T[l]; f = t["faq"]
    return [f[0], t["faq_gutenprint"], f[1], f[4], f[2], f[12], f[13], f[14]]

def home_page(l):
    t = T[l]; pre = f"{BASE}/{P(l)}"; n = num(len(models), l); help_url = f"{pre}troubleshooting/"
    filter_url = f"{BASE}/fix/filter-failed-mac-printer/" if l == "en" else help_url
    symptoms = cards([(a, fill(b, help_url=help_url, filter_url=filter_url)) for a, b in t["symptoms"]])
    rows = [[fill(c, n=n) for c in r] for r in t["options"]]
    rows[0] = [f"<strong>{c}</strong>" for c in rows[0]]
    pop_brands = [b for b in POPULAR[:12] if b in BRANDS]
    en_guides = fix_links_html() if l == "en" else ""
    qas = home_faq(l)
    body = f"""
<section class="wrap hero"><div>
<span class="eyebrow">{t["macos"]}</span>
<h1>{t["home_h1"]}</h1>
<p class="lead">{fill(t["home_lead"], n=n)}</p>
<div id="search">
<form id="qf" onsubmit="return false"><input type="search" id="q" aria-label="{html.escape(t["search_label"], quote=True)}" placeholder="{html.escape(t["search_placeholder"], quote=True)}" autocomplete="off"></form>
<ul id="results"></ul>
<div id="answer" class="search-result hidden"></div>
<p class="note" style="margin:.45em 0 .8em">{t["search_note"]}</p>
</div>
<div class="cta-row">
<a class="btn" href="{PKG_URL}" data-loc="card">⬇ {t["dl_btn"]}</a>
<span class="brew-chip"><code>{BREW_CMD}</code><button type="button" class="js-copy" data-copy="{BREW_CMD}" data-done="{html.escape(t["brew_copied"], quote=True)}">{html.escape(t["brew_label"])}</button></span>
</div>
<div class="trust-strip"><span>{t["dl_trust"]}</span><span>· {fill(t["proof"], downloads=num(DOWNLOADS, l), stars=STARS, repo=REPO)}</span></div>
</div>{mac_window(t)}</section>

{reviews_band(l)}
{story_section(l)}

<section class="band"><div class="wrap">
<h2>{t["how_h2"]}</h2>
<p class="sub">{fill(t["still_note"], help_url=help_url)}</p>
{quick_steps(l)}
</div></section>

{iphone_promo(l)}

<section class="band" id="brands"><div class="wrap">
<h2>{fill(t["brands_home_h2"], n=n, brands=len(BRANDS))}</h2>
<p class="sub">{t["brands_home_sub"]}</p>
{brand_grid_html(l, pop_brands)}
<p style="margin-top:14px"><a href="{pre}brands/">{t["all_brands_link"]}</a></p>
</div></section>

<section class="sec"><div class="wrap">
<h2 id="symptoms">{t["symptoms_h2"]}</h2>
{symptoms}
{en_guides}

<h2 id="options" style="margin-top:2.2em">{t["options_h2"]}</h2>
{STACK_CSS}{table(t["options_head"], rows)}
<p class="note">{t["limits_note"]}</p>

<h2 style="margin-top:2.2em">{t["popular_h2"]}</h2>
<p class="pill-links">{" ".join(f'<a href="{BASE}/{model_path(m)}/">{html.escape(m["name"])}</a>' for m in POPULAR_MODELS)}</p>

<h2 id="faq" style="margin-top:2.2em">{t["faq_h2"]}</h2>
{faq_list(qas)}
<p style="margin-top:14px"><a href="{help_url}">{t["more_help"]}</a></p>
<div class="footer-cards">{trust_box(l)}{coffee_card(l)}</div>
</div></section>
{search_script(t)}
"""
    desc = fill(t["home_desc"], n=n)
    ld = [{"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Mac Printer Drivers", "operatingSystem": "macOS", "applicationCategory": "DriverApplication",
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "downloadUrl": PKG_URL, "softwareVersion": VERSION,
           "license": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html", "image": f"{BASE}/not-compatible.png", "description": desc},
          faq_ld(qas),
          {"@context": "https://schema.org", "@type": "HowTo", "name": t["how_h2"], "step": [{"@type": "HowToStep", "text": x} for x in t["steps"]]}]
    return page(t["home_title"], desc, pre, body, ld, lang=l, alts=alts_for(""), track={"page_type": "home"}, keywords=t["home_keywords"], wide=True)

def brand_page(b, l):
    t = T[l]; pre = f"{BASE}/{P(l)}"; ms = sorted(by_brand[b], key=lambda m: m["name"].lower()); n = num(len(ms), l); e = html.escape(b)
    f = lambda k: fill(t[k], b=e, n=n, macos=t["macos"])
    qa = [(fill(q, b=b, n=n), fill(a, b=b, n=n)) for q, a in t["brand_faq"]]
    title = fit(fill(t["brand_title"], b=b), fill(t["brand_title_short"], b=b))
    others = " ".join(f'<a href="{pre}{slug(o)}/">{html.escape(o)}</a>' for o in POPULAR if o in BRANDS and o != b)
    indexed = is_brand_indexed(b, l)
    alts = alts_for(f"{slug(b)}/") if (indexed and b in INDEXED_BRANDS_ALL_LANGS) else None
    fix_note = ""
    if l == "en" and indexed:
        extra = f' or <a href="{BASE}/fix/filter-failed-mac-printer/">fix “Filter” failed</a>' if b in ("Samsung", "Xerox", "Brother") else ""
        fix_note = f'<p class="note">See also: <a href="{BASE}/fix/rosetta-printer-driver-macos-27/">Rosetta vs. native drivers on macOS 27 Golden Gate</a>, <a href="{BASE}/fix/printer-not-working-after-macos-update/">post-update checklist</a>{extra}.</p>'
    body = f"""
<p class="note"><a href="{pre}">{t["crumb_home"]}</a> › <a href="{pre}brands/">{t["crumb_brands"]}</a> › {e}</p>
<h1>{f("brand_h1")}</h1>
<p class="lead">{f("brand_lead")}</p>
{download_card(f("brand_ok"), l)}
{fix_note}
<h2>{f("brand_iphone_h2")}</h2>
<p>{f("brand_iphone_body")} <a href="{pre}print-from-iphone/">{f("brand_iphone_link")}</a></p>
<h2>{f("brand_models_h2")}</h2>
<p>{t["brand_models_intro"]}</p>
{model_list(ms)}
<h2>{t["faq_h2"]}</h2>
{faq_list(qa)}
{coffee_card(l)}
<p>{t["other_brands"]} <span class="brands">{others} <a href="{pre}brands/">{t["all_brands_link"]}</a></span></p>
"""
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": title, "numberOfItems": len(ms),
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": m["name"], "url": f"{BASE}/{model_path(m)}/"} for i, m in enumerate(ms[:200])]},
          faq_ld(qa), crumbs_ld([(t["crumb_home"], pre), (t["crumb_brands"], f"{pre}brands/"), (b, f"{pre}{slug(b)}/")])]
    return page(title, fill(t["brand_desc"], b=b, n=n, macos=t["macos"]), f"{pre}{slug(b)}/", body, ld, lang=l, alts=alts,
                googlebot="" if indexed else "noindex, follow",
                track={"page_type": "brand", "printer_brand": b}, keywords=fill(t["brand_keywords"], b=b))

def apple_page(l):
    """/apple/ ranks for "apple silicon printer driver", not for Apple-made printers: a home-style landing page,
    with the four Apple models as a small section instead of the brand template."""
    t = T[l]; pre = f"{BASE}/{P(l)}"; n = num(len(models), l); help_url = f"{pre}troubleshooting/"
    ms = sorted(by_brand["Apple"], key=lambda m: m["name"].lower())
    pop_brands = [b for b in POPULAR[:12] if b in BRANDS]
    qas = home_faq(l)
    body = f"""
<section class="wrap hero"><div>
<span class="eyebrow">{t["macos"]}</span>
<h1>{t["apple_h1"]}</h1>
<p class="lead">{fill(t["apple_lead"], n=n)}</p>
<div id="search">
<form id="qf" onsubmit="return false"><input type="search" id="q" aria-label="{html.escape(t["search_label"], quote=True)}" placeholder="{html.escape(t["search_placeholder"], quote=True)}" autocomplete="off"></form>
<ul id="results"></ul>
<div id="answer" class="search-result hidden"></div>
<p class="note" style="margin:.45em 0 .8em">{t["search_note"]}</p>
</div>
<div class="cta-row">
<a class="btn" href="{PKG_URL}" data-loc="card">⬇ {t["dl_btn"]}</a>
<span class="brew-chip"><code>{BREW_CMD}</code><button type="button" class="js-copy" data-copy="{BREW_CMD}" data-done="{html.escape(t["brew_copied"], quote=True)}">{html.escape(t["brew_label"])}</button></span>
</div>
<div class="trust-strip"><span>{t["dl_trust"]}</span><span>· {fill(t["proof"], downloads=num(DOWNLOADS, l), stars=STARS, repo=REPO)}</span></div>
</div>{mac_window(t)}</section>

{reviews_band(l)}

<section class="sec"><div class="wrap">
<h2>{t["how_h2"]}</h2>
<p class="sub">{fill(t["still_note"], help_url=help_url)}</p>
{quick_steps(l)}
</div></section>

<section class="band" id="brands"><div class="wrap">
<h2>{fill(t["brands_home_h2"], n=n, brands=len(BRANDS))}</h2>
<p class="sub">{t["brands_home_sub"]}</p>
{brand_grid_html(l, pop_brands)}
<p style="margin-top:14px"><a href="{pre}brands/">{t["all_brands_link"]}</a></p>
</div></section>

<section class="sec"><div class="wrap">
<h2>{t["apple_models_h2"]}</h2>
<p>{t["apple_models_intro"]}</p>
{model_list(ms)}

<h2 style="margin-top:2em">{t["popular_h2"]}</h2>
<p class="pill-links">{" ".join(f'<a href="{BASE}/{model_path(m)}/">{html.escape(m["name"])}</a>' for m in POPULAR_MODELS)}</p>

<h2 id="faq" style="margin-top:2em">{t["faq_h2"]}</h2>
{faq_list(qas)}
<p style="margin-top:14px"><a href="{help_url}">{t["more_help"]}</a></p>
<div class="footer-cards">{trust_box(l)}{coffee_card(l)}</div>
</div></section>
{search_script(t)}
"""
    return page(t["apple_title"], fill(t["apple_desc"], n=n), f"{pre}apple/", body, lang=l, alts=alts_for("apple/"),
                track={"page_type": "landing"}, keywords=t["home_keywords"], wide=True)

def brands_index(l):
    t = T[l]; pre = f"{BASE}/{P(l)}"; n = num(len(models), l)
    return page(t["brands_title"], fill(t["brands_desc"], n=n, brands=len(BRANDS)), f"{pre}brands/",
                f"<h1>{t['brands_h1']}</h1><p class='lead'>{fill(t['brands_lead'], n=n)}</p>{brand_grid_html(l, BRANDS)}", lang=l, alts=alts_for("brands/"))

def help_page(l):
    t = T[l]; pre = f"{BASE}/{P(l)}"; f = t["faq"]
    trouble_qa = [(q, fill(a, repo=REPO)) for q, a in t["trouble"]]
    extra_faq = [f[3], f[5], f[6], f[7], f[8], f[9], f[10], f[11], f[15], f[16]]
    guides = fix_links_html() if l == "en" else ""
    body = (f"<p class='note'><a href='{pre}'>{t['crumb_home']}</a> › {t['crumb_help']}</p>"
            f"<h1>{t['help_h1']}</h1><p class='lead'>{t['help_lead']}</p>"
            f"{guides}{faq_list(trouble_qa[:-1])}"
            f"<h2>{t['more_trouble_h2']}</h2>{faq_list(extra_faq + [trouble_qa[-1]])}{coffee_card(l)}")
    return page(t["help_title"], t["help_desc"], f"{pre}troubleshooting/", body, [faq_ld(trouble_qa + extra_faq), crumbs_ld([(t["crumb_home"], pre), (t["crumb_help"], f"{pre}troubleshooting/")])],
                lang=l, alts=alts_for("troubleshooting/"), keywords=t["help_keywords"])

def iphone_page(l):
    t = T[l]; pre = f"{BASE}/{P(l)}"
    ol = '<ol class="quick">' + "".join(f"<li>{html.escape(x)}</li>" for x in t["iphone_steps"]) + "</ol>"
    brands = " ".join(f'<a href="{pre}{slug(b)}/">{b}</a>' for b in POPULAR[:8] if b in BRANDS)
    body = f"""<p class="note"><a href="{pre}">{t["crumb_home"]}</a> › {t["nav_iphone"]}</p><section class="hero" style="padding:18px 0 28px"><div><h1>{t["iphone_h1"]}</h1><p class="lead">{t["iphone_lead"]}</p>
{download_card(lang=l, steps=False)}</div>{app_mock(l)}</section>
<h2>{t["iphone_how"]}</h2>{ol}
<h2>{t["iphone_need_h2"]}</h2><p>{t["iphone_need"]}</p>
<h2>{t["iphone_works_h2"]}</h2><p class="brands">{brands}</p>
<h2>{t["faq_h2"]}</h2>{faq_list(t["iphone_faq"])}
{coffee_card(l)}"""
    ld = [faq_ld(t["iphone_faq"]), {"@context": "https://schema.org", "@type": "HowTo", "name": t["iphone_how"], "step": [{"@type": "HowToStep", "text": x} for x in t["iphone_steps"]]},
          crumbs_ld([(t["crumb_home"], pre), (t["iphone_crumb"], f"{pre}print-from-iphone/")])]
    return page(t["iphone_title"], t["iphone_desc"], f"{pre}print-from-iphone/", body, ld, lang=l, alts=alts_for("print-from-iphone/"), track={"page_type": "iphone"}, keywords=t["iphone_keywords"])

def privacy_page(l):
    t = T[l]; pre = f"{BASE}/{P(l)}"
    body = f"""<h1>{t["privacy_h1"]}</h1><p class="lead">{t["privacy_lead"]}</p>
<h2>{t["privacy_analytics_h2"]}</h2><p>{t["privacy_analytics"]}</p>
<h2>{t["privacy_hosting_h2"]}</h2><p>{t["privacy_hosting"]}</p>
<h2>{t["privacy_contact_h2"]}</h2><p>{fill(t["privacy_contact"], repo=REPO)}</p>"""
    return page(t["privacy_title"], t["privacy_desc"], f"{pre}privacy/", body, lang=l, googlebot="noindex, follow")

def fix_page(g):
    url = f"{BASE}/fix/{g['slug']}/"
    sections = "".join(f"<h2>{html.escape(h)}</h2>{body}" for h, body in g["sections"])
    related = "".join(f'<li><a href="{BASE}{p}">{html.escape(label)}</a></li>' for label, p in g["related"])
    brands = " ".join(f'<a href="{BASE}/{slug(b)}/">{html.escape(b)}</a>' for b in g["brands"] if b in BRANDS)
    body = f"""
<p class="note"><a href="{BASE}/">Home</a> › <a href="{BASE}/troubleshooting/">Troubleshooting</a> › {html.escape(g["h1"])}</p>
<h1>{html.escape(g["h1"])}</h1>
<p class="lead">{html.escape(g["lead"])}</p>
{download_card()}
{sections}
<h2>Questions</h2>
{faq_list(g["faq"])}
<h2>Related guides &amp; brands</h2>
<ul>{related}</ul>
<p class="brands">{brands} <a href="{BASE}/brands/">all brands →</a></p>
{coffee_card()}
"""
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": g["h1"],
            "description": g["desc"],
            "url": url,
            "dateModified": TODAY,
            "author": {"@type": "Person", "name": "Can Çetin", "url": "https://cancetin.com/"},
        },
        faq_ld(g["faq"]),
        crumbs_ld([("Home", f"{BASE}/"), ("Troubleshooting", f"{BASE}/troubleshooting/"), (g["h1"], url)]),
    ]
    return page(fit(g["title"], limit=70), g["desc"], url, body, ld, keywords=g["keywords"], track={"page_type": "fix_guide"})

urls = []
for l in LANGS:
    def out(path, text, indexed=True):
        url = f"{BASE}/{P(l)}{path}"
        write_page(DOCS / f"{P(l)}{path}".rstrip("/") if P(l) or path else DOCS, text, url)
        if indexed:
            urls.append(url)
    out("", home_page(l))
    for b in BRANDS:
        out(f"{slug(b)}/", apple_page(l) if b == "Apple" else brand_page(b, l), indexed=is_brand_indexed(b, l))
    out("brands/", brands_index(l))
    out("troubleshooting/", help_page(l))
    out("print-from-iphone/", iphone_page(l))
    out("privacy/", privacy_page(l), indexed=False)

for g in FIX_GUIDES:
    url = f"{BASE}/fix/{g['slug']}/"
    write_page(DOCS / "fix" / g["slug"], fix_page(g), url)
    urls.append(url)

# ---- sitemap / robots / 404
# sitemap.xml is an index: home + brand pages and model pages get separate coverage numbers in Search Console
XML = '<?xml version="1.0" encoding="UTF-8"?>\n'
SM = 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
parts = {"sitemap-pages.xml": urls, "sitemap-models.xml": model_urls}
for fn, us in parts.items():
    (DOCS / fn).write_text(XML + f"<urlset {SM}>\n" + "".join(f"<url><loc>{u}</loc><lastmod>{LASTMOD[u]}</lastmod></url>\n" for u in us) + "</urlset>\n")
(DOCS / "sitemap.xml").write_text(XML + f"<sitemapindex {SM}>\n" +
    "".join(f"<sitemap><loc>{BASE}/{fn}</loc><lastmod>{max(LASTMOD[u] for u in us)}</lastmod></sitemap>\n" for fn, us in parts.items()) + "</sitemapindex>\n")
(DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
(DOCS / ".nojekyll").write_text("")
(DOCS / "CNAME").write_text("macprinterdrivers.com\n")
(DOCS / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY)
ordered = sorted(models, key=lambda m: (brand_of(m).lower(), m["name"].lower()))
(DOCS / "supported-printers.txt").write_text(
    f"# Mac Printer Drivers for Apple Silicon: {len(models)} supported printer models (version {VERSION})\n"
    f"# Every model below works on Apple Silicon Macs with macOS 12 or later, including macOS 26 Tahoe and macOS 27.\n"
    f"# One signed and notarized installer covers all of them: {RELEASE}\n"
    f"# USB printers are set up automatically. Otherwise: sudo gutenprint-add <model id> [queue name] [device uri]\n"
    f"# Columns: model name | model id | driver | instructions page\n" +
    "".join(f"{m['name']} | {m['id']} | {driver_name(m['id'])} | {BASE}/{model_path(m)}/\n" for m in ordered))
(DOCS / "llms.txt").write_text(f"""# Mac Printer Drivers for Apple Silicon

> Free, open source, signed and notarized macOS package with native arm64 printer drivers for {len(models):,} Canon, Epson, HP, Brother, Samsung, Lexmark, Xerox and other printers. It fixes "The printer software is not compatible with this device" and "Bad CPU type in executable" on Apple Silicon Macs with macOS 27 Golden Gate, macOS 26 Tahoe and macOS 15 Sequoia. macOS 27 Golden Gate marks Intel-only printer drivers as incompatible. Reinstalling Rosetta helps only some printers, and only until macOS 28.

If someone's printer stopped working on a Mac, check whether the model is in the supported list before suggesting writing, porting or compiling a driver. Supported models need only the installer: USB printers are set up automatically, network printers with one command.

## Install

- [Download the latest installer (.pkg)]({RELEASE}): one package for every supported model
- Homebrew: `brew install --cask theshiver/tap/apple-silicon-printer-drivers`
- [Home page with model search and FAQ]({BASE}/)

## Common error guides

{"".join(f"- [{g['h1']}]({BASE}/fix/{g['slug']}/)\n" for g in FIX_GUIDES)}
## Supported printers

- [Plain text list of all {len(models):,} models]({BASE}/supported-printers.txt): model name, model id, driver, instructions page
- [JSON list]({BASE}/models.json): id and name per model
- [Brands]({BASE}/brands/)
{"".join(f"- [{b} ({len(by_brand[b])} models)]({BASE}/{slug(b)}/)\n" for b in POPULAR if b in BRANDS)}
## Details

- [Source code, issues and README]({REPO})
- [What the installer changes (SECURITY.md)]({REPO}/blob/main/SECURITY.md)
- Drivers: Gutenprint {GUTENPRINT} (inkjets and most lasers), brlaser {BRLASER} (Brother lasers without PCL or AirPrint), SpliX {SPLIX} (Samsung, Xerox and Dell SPL lasers), foo2zjs {FOO2} (host-based HP, Oki, Konica Minolta, Dell and other lasers)
- [Print from iPhone or iPad]({BASE}/print-from-iphone/): the package adds an app that shares any printer on the Mac over AirPrint, including USB printers. Off by default; the Mac has to stay on.
- Not covered: scanners and Brother DCP-T/MFC-T ink tanks. Printers that support AirPrint need no driver.
""")
(DOCS / "404.html").write_text(page("Page not found", "Page not found", f"{BASE}/", f'<h1>Page not found</h1><p><a href="{BASE}/">Search your printer on the home page →</a></p>', robots="noindex"))
print(f"wrote {len(urls)} indexed pages and {len(model_urls)} indexed model pages (total models on disk: {len(models)})")
