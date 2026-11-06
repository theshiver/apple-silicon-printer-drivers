#!/usr/bin/env python3
"""Generates the GitHub Pages site in docs/ from docs/models.json.

  python3 site/build-site.py
"""
import json, re, html, datetime, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
BASE = "https://theshiver.github.io/apple-silicon-printer-drivers"
REPO = "https://github.com/theshiver/apple-silicon-printer-drivers"
RELEASE = f"{REPO}/releases/latest"
PKG = "AppleSilicon-Printer-Drivers-2.0.0.pkg"
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
         "e-Studio": "Toshiba", "MP": "Ricoh", "Datamax-ONeil": "Datamax", "TASKalfa": "Kyocera"}
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
GUTENPRINT, BRLASER, SPLIX = "5.3.5", "6.2.8", "2.0.2"
# German pages: Germany sends the most clicks; start with home and the three brands people search for
DE_BRANDS = ["Brother", "Canon", "Epson"]
def alts_for(path):
    return {"en": f"{BASE}/{path}", "de": f"{BASE}/de/{path}"}
# Bing flags titles over 70 chars and Google cuts around 60: take the first candidate that fits
def fit(*titles, limit=65):
    return next((t for t in titles if len(t) <= limit), titles[-1])
de_num = lambda n: f"{n:,}".replace(",", ".")
VERSION = re.search(r"-(\d+(?:\.\d+)+)\.pkg$", PKG).group(1)
PKG_URL = f"{REPO}/releases/download/v{VERSION}/{PKG}"  # the file itself, not the GitHub release page

INDEXNOW_KEY = "a3007c2aad3307cf8925b08255b5b513"
def driver_name(mid):
    return "brlaser" if mid.startswith("brlaser-") else "SpliX" if mid.startswith("splix-") else "Gutenprint"

def model_path(m):
    """canon/pixma-ip4300 — mirrored by modelPath() in the home page search script."""
    w = m["name"].split()[0]
    return f"{slug(ALIAS.get(w, w))}/{slug(m['name'][len(w):]) or slug(m['name'])}"
assert len({model_path(m) for m in models}) == len(models), "model page paths collide"

GA_ID = "G-RL7H0KSZYM"
CSS = """
:root{color-scheme:light dark;--bg:#fff;--soft:#f5f6f8;--fg:#14171f;--muted:#5b6472;--line:#e4e7ec;--accent:#1d5fd1;--code:#f1f2f5;--ok:#127a3e;--ok-soft:#e7f6ed;--bad:#c5342b;--bad-soft:#fdeceb;--btn-bg:#1d5fd1;--btn-fg:#fff}
@media(prefers-color-scheme:dark){:root{--bg:#101216;--soft:#191c22;--fg:#eef0f3;--muted:#a3abb8;--line:#2b2f37;--accent:#7db0ff;--code:#1f2229;--ok:#6fd694;--ok-soft:#14291c;--bad:#ff8f87;--bad-soft:#331a18;--btn-bg:#7db0ff;--btn-fg:#0b1a2b}}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased}
header{display:flex;flex-wrap:wrap;align-items:center;gap:6px 22px;max-width:1000px;margin:0 auto;padding:16px 20px}
header>a{color:var(--fg);text-decoration:none;font-weight:700;margin-right:auto}header nav{display:flex;flex-wrap:wrap;gap:4px 20px}header nav a{color:var(--muted);text-decoration:none;font-size:.95rem}header nav a:hover{color:var(--fg)}header nav a.coffee{color:var(--accent);font-weight:600}
main{max-width:1000px;margin:0 auto;padding:12px 20px 48px}
h1{font-size:clamp(2rem,4.6vw,3rem);line-height:1.12;letter-spacing:-.02em;margin:.3em 0 .4em}
h2{font-size:clamp(1.4rem,3vw,1.75rem);line-height:1.25;letter-spacing:-.01em;margin:2.4em 0 .6em}h3{font-size:1.05rem}
a{color:var(--accent)}p.lead{font-size:1.2rem;color:var(--muted);margin-top:0}.note{color:var(--muted);font-size:.93rem}
.hero{display:grid;gap:32px;align-items:center;padding:24px 0 8px}@media(min-width:800px){.hero{grid-template-columns:1.45fr 1fr}}
.mock{background:var(--soft);border-radius:18px;padding:18px;display:grid;gap:8px;justify-items:center}
.mock div{width:100%;background:var(--bg);border-radius:12px;padding:12px 14px;line-height:1.3}.mock small{display:block;font-weight:600}
.mock .bad small{color:var(--bad)}.mock .good small{color:var(--ok)}.mock span{color:var(--muted)}
.dl{background:var(--soft);border-radius:16px;padding:20px 22px;margin:20px 0}.hero .dl{background:none;padding:0;margin:0}
.dl .ok{font-size:1.1rem;font-weight:600;margin:0 0 12px;color:var(--ok)}
a.btn{display:inline-block;background:var(--btn-bg);color:var(--btn-fg);font-size:1.15rem;font-weight:600;text-decoration:none;padding:15px 30px;border-radius:12px}
a.btn:hover{filter:brightness(1.1)}a.btn:focus-visible,summary:focus-visible,button:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.dl .trust{color:var(--muted);font-size:.92rem;margin:12px 0 14px}.hero .trust{margin-bottom:6px}
ol.quick{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;list-style:none;padding:0;margin:0;counter-reset:q}
ol.quick li{counter-increment:q;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:.97rem}
ol.quick li::before{content:counter(q);display:inline-grid;place-items:center;width:1.7em;height:1.7em;margin-right:8px;border-radius:50%;background:var(--btn-bg);color:var(--btn-fg);font-weight:700;font-size:.85rem}
@media(max-width:600px){ol.quick{grid-template-columns:1fr}a.btn{display:block;text-align:center}}
input[type=search]{width:100%;font-size:1.15rem;padding:14px 16px;border:2px solid var(--line);border-radius:12px;background:var(--bg);color:var(--fg)}input[type=search]:focus{outline:none;border-color:var(--accent)}
#results{list-style:none;padding:0;margin:8px 0 0}#results li{padding:10px 14px;border:1px solid var(--line);border-radius:10px;margin-top:8px;cursor:pointer}#results li:hover,#results li.sel{border-color:var(--accent)}
.card{background:var(--soft);border-radius:16px;padding:18px 22px;margin:18px 0}.brands a{display:inline-block;margin:4px 12px 4px 0}
.cards{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}.cards div{border:1px solid var(--line);border-radius:14px;padding:14px 16px}.cards strong{display:block;margin-bottom:4px}
.models{columns:3 220px;list-style:none;padding:0;margin:0}.models li{padding:3px 0;break-inside:avoid}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:.9rem;color:var(--muted)}tbody tr:first-child{background:var(--ok-soft)}
details{border-bottom:1px solid var(--line);padding:12px 0}summary{cursor:pointer;font-weight:600}details p{margin:.6em 0 .2em}
pre,code{font:.92em ui-monospace,SFMono-Regular,Menlo,monospace}pre{background:var(--code);padding:12px 14px;border-radius:10px;overflow:auto;position:relative}code{background:var(--code);padding:1px 5px;border-radius:4px}pre code{background:none;padding:0}
button.copy{position:absolute;top:8px;right:8px;font-size:.8rem;padding:4px 8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:6px;cursor:pointer}
.hidden{display:none}ol.steps li{margin:.4em 0}
footer{color:var(--muted);font-size:.9rem;margin-top:56px;border-top:1px solid var(--line);padding-top:16px}
"""

# Owner's decision (2026-11-05): GA runs for every visitor, no consent bar. Advertising features stay off.
# The automatic page_view ignores custom params, so brand and model pages send their own printer_page event.
TRACK_JS = """(function(){var G='%s',d=document;
window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}
var s=d.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+G;d.head.appendChild(s);
var P=JSON.parse(d.body.dataset.track||'{}');gtag('js',new Date());gtag('config',G,{allow_google_signals:false,allow_ad_personalization_signals:false});if(P.printer_brand)gtag('event','printer_page',P);
window.track=function(n,p){gtag('event',n,Object.assign({},P,p))};
d.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href$=".pkg"]');if(a)track('driver_download',{link_location:a.dataset.loc||'nav'})});
d.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href*="sponsors/theshiver"]');if(a)track('coffee_click',{link_location:a.dataset.loc||'other'})});
d.addEventListener('toggle',function(e){var s=e.target.querySelector&&e.target.querySelector('summary');if(e.target.open&&s)track('faq_open',{question:s.textContent.slice(0,100)})},true);
})();""" % GA_ID

NAV = {"en": ("Check my printer", "Help", "☕ Buy me a coffee"), "de": ("Drucker prüfen", "Hilfe", "☕ Spendier mir einen Kaffee")}
COFFEE = "https://github.com/sponsors/theshiver"
COFFEE_CARD = {"en": ("☕ Printing again?", "This driver is free and always will be. If it saved you a new printer, you can say thanks with a coffee.", "Buy me a coffee"),
               "de": ("☕ Druckt es wieder?", "Dieser Treiber ist kostenlos und bleibt es. Hat er dir einen neuen Drucker erspart, kannst du mit einem Kaffee Danke sagen.", "Spendier mir einen Kaffee")}
def coffee_card(lang="en"):
    t, d, b = COFFEE_CARD[lang]
    return f'<div class="card"><strong>{t}</strong><br>{d} <a href="{COFFEE}" data-loc="card">{b} →</a></div>'
PRIVACY = {"en": "Privacy", "de": "Datenschutz (englisch)"}
LANG_NAME = {"en": "English", "de": "Deutsch"}

def page(title, desc, canonical, body, jsonld=None, keywords="", robots="", lang="en", alts=None, track=None):
    """alts: {lang: url} of every language version including this one; emits hreflang and a language switch."""
    sup, helplink, coffee = NAV[lang]
    privacy = PRIVACY[lang]
    data = html.escape(json.dumps({"page_type": "other", **(track or {})}), quote=True)
    hreflang = "".join(f'<link rel="alternate" hreflang="{l}" href="{u}">' for l, u in (alts or {}).items())
    if alts:
        hreflang += f'<link rel="alternate" hreflang="x-default" href="{alts["en"]}">'
    switch = "".join(f'<a href="{u}" hreflang="{l}" lang="{l}">{LANG_NAME[l]}</a>' for l, u in (alts or {}).items() if l != lang)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, separators=(",",":"))}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{f'<meta name="keywords" content="{html.escape(keywords)}">' if keywords else ''}
{f'<meta name="robots" content="{robots}">' if robots else ''}
<link rel="canonical" href="{canonical}">{hreflang}
<meta property="og:type" content="website"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/not-compatible.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}/not-compatible.png">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%96%A8%3C/text%3E%3C/svg%3E">
{ld}
<style>{CSS}</style>
</head>
<body data-track="{data}">
<header><a href="{BASE}/{'de/' if lang == 'de' else ''}">🖨 Mac Printer Drivers</a>
<nav><a href="{BASE}/#search">{sup}</a><a href="{BASE}/troubleshooting/">{helplink}</a><a class="coffee" href="{COFFEE}" data-loc="header">{coffee}</a>{switch}</nav></header>
<main>
{body}
<footer><a href="{BASE}/brands/">{'Alle Marken' if lang == 'de' else 'All brands'}</a> · <a href="{REPO}">GitHub</a> · <a href="{COFFEE}" data-loc="footer">{coffee}</a> · <a href="{BASE}/privacy/">{privacy}</a><br>{'Kostenlos und Open Source. Keine Verbindung zu Canon, Epson, HP, Brother oder Apple. Produktnamen sind Marken ihrer Inhaber.' if lang == 'de' else 'Free and open source. Not affiliated with Canon, Epson, HP, Brother or Apple. Product names are trademarks of their owners.'}</footer>
</main>
<script>{TRACK_JS}</script>
</body></html>"""

DL_TEXT = {
    "en": ("Download the free driver", f"Free · Signed and notarized by Apple · Any Apple Silicon Mac, macOS 12 or later",
           ("Plug the printer in with USB and switch it on", "Open the downloaded file and click through", "Print. The printer is set up for you"),
           f'Still not printing? Restart the Mac once and re-plug the printer, then see <a href="{BASE}/troubleshooting/">troubleshooting</a>. Wi-Fi printer? See below.'),
    "de": ("Kostenlosen Treiber herunterladen", f"Kostenlos · Von Apple signiert und notarisiert · Jeder Apple-Silicon-Mac ab macOS 12",
           ("Drucker per USB anschließen und einschalten", "Heruntergeladene Datei öffnen und durchklicken", "Drucken. Der Drucker wird automatisch eingerichtet"),
           f'Druckt es nicht? Mac einmal neu starten, Drucker neu einstecken, dann <a href="{BASE}/troubleshooting/">Fehlerbehebung</a> (englisch). WLAN-Drucker? Siehe unten.'),
}
def quick_steps(lang="en"):
    return f'<ol class="quick">{"".join(f"<li>{t}</li>" for t in DL_TEXT[lang][2])}</ol>'
def download_card(ok="", lang="en", steps=True):
    """The answer people came for, above everything else: one button, three steps."""
    btn, trust, _, after = DL_TEXT[lang]
    return (f'<div class="dl">{f"<p class=ok>✅ {ok}</p>" if ok else ""}<a class="btn" href="{PKG_URL}" data-loc="card">⬇ {btn}</a>'
            f'<p class="trust">{trust}</p>{quick_steps(lang) if steps else ""}</div>\n' + (f'<p class="note">{after}</p>' if steps else ""))
def faq_list(qa):
    """Questions stay in the HTML for search engines and find-in-page, but the page reads short."""
    return "\n".join(f"<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>" for q, a in qa)
def cards(rows):
    return '<div class="cards">' + "".join(f"<div><strong>{t}</strong>{d}</div>" for t, d in rows) + "</div>"

MACOS = "macOS 27, macOS 26 Tahoe and macOS 15 Sequoia"
ROSETTA_A = "Sometimes, and only for now. Reinstalling Rosetta makes some old printer drivers work again after you delete and re-add the printer; others stay marked “Software Incompatible”. Apple ends Rosetta for apps in macOS 28, so the maker's old driver will stop again then. This driver doesn't need Rosetta."

WIFI_A = "Install the driver, then open System Settings → Printers & Scanners, click Add, select your printer, choose Use: Select Software… and pick your model ending in “Apple Silicon”."
def brand_faq(b, n):
    return [
     (f"Is there a {b} printer driver for macOS 27 and Apple Silicon?",
      f"{b} never released Apple Silicon versions of the Mac drivers for many of its older printers; they need Rosetta, and macOS 27 marks Intel-only printer drivers as incompatible. Apple ends Rosetta for apps in macOS 28. This free package adds native arm64 drivers for {n} {b} models, so they print on any Apple Silicon Mac without Rosetta."),
     (f"Why does my {b} printer say “The printer software is not compatible with this device”?",
      f"The {b} driver installed on the Mac is Intel-only. Install this package, restart the Mac once, then unplug and re-plug the printer."),
     ("Will reinstalling Rosetta fix it?",
      ROSETTA_A),
     ("Does it work on macOS 26 Tahoe and macOS 15 Sequoia?",
      "Yes. It runs on macOS 12 and later on Apple Silicon Macs, and keeps working after you update to macOS 27."),
     ("My printer is on Wi-Fi, or wasn't set up automatically.", WIFI_A),
    ]

def model_list(ms):
    return '<ul class="models">' + "".join(f'<li><a href="{BASE}/{model_path(m)}/">{html.escape(m["name"])}</a></li>' for m in ms) + "</ul>"

def brand_page(b):
    ms = sorted(by_brand[b], key=lambda m: m["name"].lower())
    rows = model_list(ms)
    title = fit(f"{b} Printer Driver for Mac (macOS 27, Apple Silicon) – Free", f"{b} Printer Driver for Mac (macOS 27, Apple Silicon)")
    desc = f"Free {b} printer driver for Mac: native Apple Silicon driver for {len(ms)} {b} printers on {MACOS}. Fixes “The printer software is not compatible with this device” without Rosetta."
    qa = brand_faq(b, len(ms))
    others = " ".join(f'<a href="{BASE}/{slug(o)}/">{html.escape(o)}</a>' for o in POPULAR if o in BRANDS and o != b)
    body = f"""
<p class="note"><a href="{BASE}/">Home</a> › <a href="{BASE}/brands/">Brands</a> › {html.escape(b)}</p>
<h1>{html.escape(b)} printer driver for Mac (Apple Silicon, macOS 27)</h1>
<p class="lead">{len(ms)} {html.escape(b)} printers work again on Apple Silicon Macs with {MACOS}. One free installer for all of them, no Rosetta.</p>
{download_card(f"{len(ms)} {html.escape(b)} printers supported")}
<h2>Supported {html.escape(b)} printers</h2>
<p>Pick your printer for model-specific help.</p>
{rows}
<h2>Questions</h2>
{faq_list(qa)}
{coffee_card()}
<p>Other brands: <span class="brands">{others} <a href="{BASE}/brands/">all brands →</a></span></p>
"""
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "numberOfItems": len(ms), "itemListElement": [{"@type": "ListItem", "position": i+1, "name": m["name"], "url": f"{BASE}/{model_path(m)}/"} for i, m in enumerate(ms[:200])]},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]},
          {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i+1, "name": n, "item": u} for i, (n, u) in enumerate([("Home", f"{BASE}/"), ("Brands", f"{BASE}/brands/"), (b, f"{BASE}/{slug(b)}/")])]}]
    return page(title, desc, f"{BASE}/{slug(b)}/", body, ld, alts=alts_for(f"{slug(b)}/") if b in DE_BRANDS else None, keywords=f"{b} printer driver mac, {b} driver macos 27, {b} driver mac tahoe, {b} driver macos 26, {b} apple silicon, printer software not compatible with this device", track={"page_type": "brand", "printer_brand": b})

def model_page(m, b, siblings):
    name, mid = m["name"], m["id"]
    esc = html.escape(name)
    brlaser, splix = mid.startswith("brlaser-"), mid.startswith("splix-")
    driver = (f'<a href="https://github.com/Owl-Maintain/brlaser">brlaser {BRLASER}</a>' if brlaser
              else f'<a href="https://github.com/OpenPrinting/splix">SpliX {SPLIX}</a>' if splix
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
    sib = " · ".join(f'<a href="{BASE}/{model_path(s)}/">{html.escape(s["name"])}</a>' for s in siblings)
    title = fit(f"{name} Driver for Mac (macOS 27, Apple Silicon) – Free", f"{name} Driver for Mac (macOS 27, Apple Silicon)",
                f"{name} Driver for Mac (macOS 27)", f"{name} Mac Driver")
    desc = (f"Free native driver for the {name} on Apple Silicon Macs. Fixes “The printer software is not compatible "
            f"with this device” on {MACOS} without Rosetta. USB sets up automatically; Wi-Fi in a few clicks.")
    qa = [
        (f"Does the {name} work on macOS 27, macOS 26 Tahoe and Apple Silicon?",
         f"Yes. This free package adds a native arm64 {driver_name(mid)} driver for the {name}. It runs on every Apple Silicon Mac with macOS 12 or later, including macOS 27, without Rosetta."),
        (f"Do I need to write my own {name} driver?",
         f"No. The {name} is already supported by {driver_name(mid)}, an open source driver with years of tuning for this printer. Install the package; there is nothing to write, compile or patch."),
        (f"Why does my {name} say “The printer software is not compatible with this device”?",
         f"{b}'s Mac driver for the {name} is Intel-only, and macOS 27 marks Intel-only printer drivers as incompatible. Install this package, restart the Mac once, then unplug and re-plug the printer."),
    ]
    body = f"""
<p class="note"><a href="{BASE}/">Home</a> › <a href="{brand_url}">{html.escape(brand_label)}</a> › {esc}</p>
<h1>{esc} driver for Mac</h1>
<p class="lead">Works on Apple Silicon Macs with {MACOS}. One free installer, no Rosetta, nothing to compile.</p>
{download_card(f"The {esc} is supported")}
<h2>Wi-Fi, network, or not detected over USB</h2>
<ol class="steps"><li>Install the driver above.</li><li>Open System Settings → Printers &amp; Scanners and click Add.</li><li>Select your printer, then under Use choose Select Software…</li><li>Pick “{esc}” ending in “Apple Silicon” and click Add.</li></ol>
<h2>Why did my {esc} stop working?</h2>
<p>{html.escape(b)}'s own Mac driver for this printer was built for Intel Macs only. On Apple Silicon it ran through Rosetta, but macOS 27 marks Intel-only printer drivers as incompatible, so System Settings now says <em>“The printer software is not compatible with this device”</em>. This package replaces it with {driver}, compiled natively for Apple Silicon.</p>
{"".join(notes)}
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
<script>document.querySelectorAll('button.copy').forEach(b=>b.onclick=async()=>{{await navigator.clipboard.writeText(b.nextElementSibling.textContent);b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1500)}})</script>
"""
    url = f"{BASE}/{model_path(m)}/"
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
                keywords=f"{name} driver mac, {name} mac driver, {name} macos 27, {name} mac tahoe, {name} apple silicon, {name} m1, {b} printer driver mac",
                track={"page_type": "model", "printer_brand": b, "printer_model": name})

# ---- write model pages
model_urls = []
for b, ms in by_brand.items():
    ms = sorted(ms, key=lambda m: m["name"].lower())
    for i, m in enumerate(ms):
        siblings = ms[max(0, i - 6):i] + ms[i + 1:i + 7]
        url = f"{BASE}/{model_path(m)}/"
        write_page(DOCS / model_path(m), model_page(m, b, siblings), url)
        model_urls.append(url)

# ---- write brand pages
urls = []
for b in BRANDS:
    write_page(DOCS / slug(b), brand_page(b), f"{BASE}/{slug(b)}/")
    urls.append(f"{BASE}/{slug(b)}/")

# ---- brands index
brand_links = "\n".join(f'<a href="{BASE}/{slug(b)}/">{html.escape(b)} ({len(by_brand[b])})</a>' for b in BRANDS)
write_page(DOCS / "brands", page(
    "Supported printer brands — Mac printer drivers for Apple Silicon",
    f"{len(models)} printer models from {len(BRANDS)} brands supported by native arm64 Gutenprint, brlaser and SpliX drivers for macOS.",
    f"{BASE}/brands/",
    f"<h1>Supported brands</h1><p class='lead'>{len(models):,} models. Click a brand for the full model list.</p><p class='brands'>{brand_links}</p>"), f"{BASE}/brands/")
urls.append(f"{BASE}/brands/")

# ---- troubleshooting: the follow-up questions people ask after installing
trouble = [
 ("It still says “The printer software is not compatible with this device” after installing.",
  "That message belongs to the old printer entry, which still uses the maker's Intel-only driver. The installer adds a new entry next to it, named after the model and ending in “Apple Silicon”. "
  "In System Settings → Printers & Scanners, remove the old entry (select it, click −), then print to the “Apple Silicon” one. If there is no such entry, restart the Mac once, unplug and re-plug the printer, and check the next question."),
 ("My printer doesn't show up in the list.",
  "Search your model on the home page first: if it isn't supported, no entry will appear. If it is supported and connected over USB, restart the Mac once and unplug / re-plug the printer, and connect it directly rather than through a hub or dock. "
  "Then add it in System Settings → Printers & Scanners → Add, with Use: Select Software… and the entry for your model ending in “Apple Silicon”."),
 ("“Software for this printer isn't available from Apple”.",
  "macOS shows this when you add a printer it has no driver for. Install this package first, then add the printer again in System Settings → Printers & Scanners → Add, choose Use: Select Software… and pick the entry for your model ending in “Apple Silicon”."),
 ("“No AirPrint printers found”, or AirPrint isn't offered.",
  "Older printers don't support AirPrint, and AirPrint never works over USB. For those printers, add them with Use: Select Software… and the “Apple Silicon” entry, after installing this package."),
 ("My printer is on Wi-Fi or Ethernet.",
  "The installer only sets up USB printers by itself. For a network printer, add it in System Settings → Printers & Scanners → Add with Use: Select Software… and the “Apple Silicon” entry. "
  "If the printer doesn't appear, connect it to the same network as the Mac and switch it off and on."),
 ("Will reinstalling Rosetta fix it?", ROSETTA_A),
 ("The job goes through but nothing prints, or only blank pages.",
  "Check that the queue uses your exact model: a similar model's driver can send data the printer silently ignores. Some printers, such as the HP LaserJet 1018, 1020, P1005 and P1006, can't be supported at all because they need the maker's firmware sent on every power-up."),
 ("Nothing here helped.",
  f"Open an issue on GitHub ({REPO}/issues) with your printer model, how it's connected (USB or network) and your macOS version. Terminal steps for advanced users are in the README on GitHub."),
]
trouble_html = faq_list(trouble)
trouble_title = "Mac Printer Still Not Working After Installing? Troubleshooting"
write_page(DOCS / "troubleshooting", page(
    trouble_title,
    "Printer still “not compatible”, missing from the list, on Wi-Fi, or printing blank pages after installing the Apple Silicon printer drivers? Step-by-step fixes for macOS 27, Tahoe and Sequoia.",
    f"{BASE}/troubleshooting/",
    f"<p class='note'><a href='{BASE}/'>Home</a> › Troubleshooting</p><h1>Printer still not working after installing?</h1>"
    f"<p class='lead'>Fixes for the problems people hit after installing the driver package, in the order they usually happen.</p>{trouble_html}{coffee_card()}",
    [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in trouble]},
     {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"}, {"@type": "ListItem", "position": 2, "name": "Troubleshooting", "item": f"{BASE}/troubleshooting/"}]}],
    keywords="printer software is not compatible with this device after install, printer not showing up mac, software for this printer isn't available from apple, no airprint printers found, mac printer wifi driver, macos 27 printer troubleshooting"), f"{BASE}/troubleshooting/")
urls.append(f"{BASE}/troubleshooting/")

# ---- home
faq = [
 ("Why did my printer stop working?",
  "The printer maker's Mac driver was built for older Intel Macs and never updated. macOS 27 marks those drivers as incompatible, so the printer stops, even though nothing is wrong with it. This free driver replaces the old one."),
 ("Will reinstalling Rosetta fix it?", ROSETTA_A),
 ("I had the printer maker's old driver installed. Anything to do?",
  "Restart the Mac once after installing, then unplug and re-plug the printer. The installer moves Canon's old driver aside, nothing is deleted."),
 ("Still on macOS 26 Tahoe or earlier?",
  "Your printer works now, but it can stop after you update. You can install this before or after updating."),
 ("My printer is on Wi-Fi, not USB.", WIFI_A),
 ("The installer didn't add my printer.", WIFI_A),
 ('Where are print quality and black & white?',
  'In the print dialog, open Printer Features (Printer Options on macOS 27). Quality is under Resolution. For black & white set Color Model to Grayscale.'),
 ("Black doesn't print, or colors look off.",
  "Run a nozzle check from the printer itself first: an empty or clogged cartridge is the usual cause. Then check in Printer Features that no “color-only” mode is selected. Colors can look a little different from the maker's driver."),
 ("Supply Levels says “Information Not Available”.",
  "That's expected: this driver can't read ink or toner levels. Check them on the printer's own screen."),
 ("My printer isn't in the list.",
  "Many newer printers support AirPrint and need no driver: connect the printer to your network, then add it in System Settings → Printers & Scanners → Add, with Use: AirPrint. AirPrint doesn't work over USB."),
 ("My Brother ink tank printer (DCP-T420W, DCP-T426W, DCP-T536DW, MFC-T…) isn't supported.",
  "These printers have no free driver, so this package can't add them. Check your model's Downloads page on support.brother.com. If the printer supports AirPrint, connect it to your network and add it with Use: AirPrint."),
 ("My HP LaserJet 1018, 1020, P1005 or P1006 isn't supported.",
  "These printers need HP's own software loaded every time they switch on, which this driver can't do. Picking a similar model doesn't work either: the job goes through, but nothing prints."),
 ("Does the scanner on my all-in-one work?",
  "No, only printing. For scanning use VueScan (paid) or SANE (free, more technical)."),
 ("Is it safe? Will macOS complain?",
  "Yes, it's safe. The installer is signed and notarized by Apple, so it opens without warnings, and everything it does is listed openly on GitHub."),
 ("Is it free?", "Yes. Free and open source, no account needed. The driver collects nothing."),
 ("Which macOS versions?", "Tested on macOS 27 on Apple Silicon. It should work on macOS 12 and later on Apple Silicon Macs."),
]
faq_html = faq_list(faq)
home_ld = [
 {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Mac Printer Drivers for Apple Silicon (Gutenprint arm64)",
  "operatingSystem": "macOS", "applicationCategory": "DriverApplication", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
  "downloadUrl": PKG_URL, "softwareVersion": VERSION, "license": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
  "image": f"{BASE}/not-compatible.png", "description": f"Native arm64 macOS printer driver package for {len(models)} Canon, Epson, HP, Brother, Samsung and other printers. Auto-detects USB printers."},
 {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
 {"@context": "https://schema.org", "@type": "HowTo", "name": "Install a printer driver on an Apple Silicon Mac",
  "step": [{"@type": "HowToStep", "text": "Connect the printer over USB and switch it on."},
           {"@type": "HowToStep", "text": "Download the .pkg installer and open it (signed and notarized by Apple)."},
           {"@type": "HowToStep", "text": "Print. The installer sets the printer up automatically; otherwise search the model on the site for the one command to add it."}]},
]
def table(head, rows, stack=False):
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f'<td data-l="{h}">{c}</td>' for h, c in zip(head, r)) + "</tr>" for r in rows)
    return f'<table{" class=stack" if stack else ""}><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'
# Home pages only: in CSS it would rewrite all 3,700 pages and move their lastmod. Four columns don't fit a phone, so rows become cards
STACK_CSS = ("<style>@media(max-width:600px){table.stack,.stack tbody,.stack tr,.stack td{display:block}.stack thead{display:none}"
             ".stack tr{border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin:10px 0}.stack td{border:0;padding:4px 0}"
             ".stack td:first-child{font-weight:600}.stack td:not(:first-child)::before{content:attr(data-l);display:block;color:var(--muted);font-size:.85rem}}</style>")
# ponytail: hand-kept floors (.pkg downloads across all releases, GitHub stars), refresh at release time
DOWNLOADS, STARS = 7300, 65
symptoms = cards([
 ("“The printer software is not compatible with this device”", "The old driver no longer runs. Install this driver, then print to the new entry ending in “Apple Silicon”."),
 ("“Software for this printer isn't available”", "macOS has no driver for it. Install this driver, then add the printer with Use: Select Software…"),
 ("“Generic PostScript Printer”, blank pages or missing options", "macOS picked a generic driver. Install this driver, add the printer again and pick the “Apple Silicon” entry."),
 ("The printer disappeared from the list", f'Search your model above, then see <a href="{BASE}/troubleshooting/">Help</a>.'),
])
MOCK = '<div class="mock" aria-hidden="true"><div class="bad">{who}<small>✕ {bad}</small></div><span>↓</span><div class="good">{who}<small>✓ {good}</small></div></div>'
by_name = {m["name"]: m for m in models}
POPULAR_MODELS = [by_name[n] for n in ("Brother HL-2270DW series", "Brother HL-1210W series", "Brother HL-1110 series", "Brother MFC-7460DN", "Brother DCP-7065DN",
    "Canon PIXMA MP250", "Canon PIXMA iP4300", "Canon PIXMA iP110", "Canon PIXMA MX885", "Canon MG2500 series",
    "Epson Stylus Photo R300", "Epson WorkForce 610", "HP LaserJet 1010", "Samsung ML-1865", "Samsung ML-2010")]
options = table(("Option", "Cost", "Works on macOS 28?", "Older inkjets like Canon PIXMA?"), [
 ("<strong>This package</strong>", "<strong>Free</strong>", "<strong>Yes, native on Apple Silicon</strong>", f"<strong>Yes, among {len(models):,} models</strong>"),
 ("Reinstall Rosetta", "Free", "No, Apple ends Rosetta for apps in macOS 28", "Only some printers, and only until then"),
 ("The maker's driver", "Free", "Only if the maker built one for Apple Silicon", "Older models usually have none"),
 ("A paid replacement driver", "Paid, can be per printer", "Check with the vendor", "Often not: many only drive PCL or PostScript printers"),
 ("A new printer", "The price of a printer", "Yes", "Yes, and your old one goes to waste"),
], stack=True)
home = f"""
<section class="hero"><div>
<h1>Printer not working on your Mac after the macOS update?</h1>
<p class="lead">Your printer isn't broken, and you don't need a new one. A free driver gets {len(models):,} Canon, Epson, HP, Brother and Samsung printers working again.</p>
{download_card(steps=False)}
<p class="note">{DOWNLOADS:,}+ downloads · {STARS} stars on <a href="{REPO}">GitHub</a> · No account needed</p>
</div>{MOCK.format(bad="Software not compatible", good="Ready to print", who="Your printer")}</section>

<h2>How it works</h2>
{quick_steps()}
<p class="note">Still not printing? Restart the Mac once and re-plug the printer, then see <a href="{BASE}/troubleshooting/">Help</a>.</p>
<p><a href="{BASE}/print-from-iphone/">Want to print from your iPhone or iPad too? →</a></p>

<h2 id="search">Is my printer supported?</h2>
<form id="qf" onsubmit="return false"><input type="search" id="q" aria-label="Printer model" placeholder="Type your printer model, e.g. Canon MP250" autocomplete="off"></form>
<ul id="results"></ul>
<div id="answer" class="card hidden"></div>
<p class="note">Not listed? Try just the model number. If it still isn't there, this driver doesn't support that printer. And if macOS already sets your printer up by itself (AirPrint), you don't need any of this.</p>
<p class="brands">{" ".join(f'<a href="{BASE}/{slug(b)}/">{html.escape(b)}</a>' for b in POPULAR if b in BRANDS)} <a href="{BASE}/brands/">all brands →</a></p>

<h2 id="symptoms">Does this look familiar?</h2>
<figure style="margin:0 0 16px"><img src="not-compatible.png" width="1270" height="230" style="width:100%;height:auto;border-radius:12px" alt="macOS Printers &amp; Scanners showing a Canon MP250 with the error: The printer software is not compatible with this device" loading="lazy"></figure>
{symptoms}

<h2 id="options">Your options</h2>
{STACK_CSS}{options}
<p class="note">What this driver doesn't do: it can't show ink or toner levels, it doesn't scan, and Wi-Fi printers take one extra step.</p>

<h2>Popular printers</h2>
<p class="brands">{" ".join(f'<a href="{BASE}/{model_path(m)}/">{html.escape(m["name"])}</a>' for m in POPULAR_MODELS)}</p>

<h2 id="faq">Questions</h2>
{faq_html}
<p><a href="{BASE}/troubleshooting/">More help →</a></p>
{coffee_card()}

<script>
const BASE={json.dumps(BASE)},ALIAS={json.dumps(ALIAS)};let MODELS=null,sel=-1,st;
const slug=s=>s.replace(/\\+/g,' plus').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
function modelPath(m){{const w=m.name.split(' ')[0];return slug(ALIAS[w]||w)+'/'+(slug(m.name.slice(w.length))||slug(m.name))}}
const q=document.getElementById('q'),res=document.getElementById('results'),ans=document.getElementById('answer');
const norm=s=>s.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
async function load(){{if(!MODELS){{MODELS=await (await fetch('models.json')).json();MODELS.forEach(m=>m.n=norm(m.name+' '+m.id));}}}}
function score(m,terms){{let s=0;for(const t of terms){{if(!m.n.includes(t))return 0;s+=(m.n.split(' ').includes(t)?3:1)}}return s+Math.max(0,20-m.name.length)/20}}
async function search(){{await load();const terms=norm(q.value).split(' ').filter(Boolean);res.innerHTML='';sel=-1;if(!terms.length)return;
 const hits=MODELS.map(m=>[score(m,terms),m]).filter(x=>x[0]>0).sort((a,b)=>b[0]-a[0]).slice(0,12);
 clearTimeout(st);st=setTimeout(()=>window.track&&track('printer_search',{{search_term:q.value.trim().slice(0,60),result_count:hits.length}}),1500);
 if(!hits.length){{res.innerHTML='<li>No match. Try only the model number (e.g. “MP250”).</li>';return}}
 for(const [,m] of hits){{const li=document.createElement('li');li.innerHTML=`<strong>${{m.name}}</strong>`;li.onclick=()=>show(m);res.appendChild(li)}}}}
function show(m){{res.innerHTML='';q.value=m.name; ans.classList.remove('hidden');window.track&&track('printer_select',{{printer_model:m.name}});
 ans.innerHTML=`<h3 style="margin-top:0">✅ ${{m.name}} is supported</h3>
 <p><a class="btn" href="{PKG_URL}" data-loc="search">⬇ Download the free driver</a></p>
 <p>Plugged in with USB? The installer sets it up by itself. <a href="${{BASE}}/${{modelPath(m)}}/">Wi-Fi and more help for the ${{m.name}} →</a></p>`;
 history.replaceState(null,'','#'+encodeURIComponent(m.id));ans.scrollIntoView({{behavior:'smooth',block:'center'}})}}
q.addEventListener('input',search);q.addEventListener('keydown',e=>{{const items=[...res.children];if(e.key==='ArrowDown'){{sel=Math.min(sel+1,items.length-1)}}else if(e.key==='ArrowUp'){{sel=Math.max(sel-1,0)}}else if(e.key==='Enter'){{if(items[sel]||items[0])(items[sel]||items[0]).click();return}}else return;items.forEach((li,i)=>li.classList.toggle('sel',i===sel));e.preventDefault()}});
function pick(){{const items=[...res.children];const it=items[sel]||items[0];if(it&&it.onclick)it.click()}}
document.getElementById('qf').addEventListener('submit',e=>{{e.preventDefault();pick()}});
q.addEventListener('search',pick);q.addEventListener('keyup',e=>{{if(e.key==='Enter')pick()}});
(async()=>{{const h=decodeURIComponent(location.hash.slice(1));if(h){{await load();const m=MODELS.find(x=>x.id===h);if(m)show(m)}}}})();
</script>
"""
write_page(DOCS, page(
    "“Printer Software Is Not Compatible With This Device” Mac Fix",
    f"Your printer isn't broken. Fix “The printer software is not compatible with this device” on macOS 27 with a free driver for {len(models):,} Canon, Epson, HP, Brother and Samsung printers. No Rosetta.",
    f"{BASE}/", home, home_ld, alts=alts_for(""), track={"page_type": "home"},
    keywords="mac printer drivers, macos printer driver, macos 27 printer driver, macos tahoe printer driver, printer not working after mac update, printer software is not compatible with this device, canon mp250 driver mac, apple silicon printer driver, m1 printer driver, macos 27 printer, rosetta printer driver, gutenprint mac arm64"), f"{BASE}/")
urls.insert(0, f"{BASE}/")

# ---- German pages (home + DE_BRANDS); model pages stay English and are linked from the tables
DE_MACOS = "macOS 27, macOS 26 Tahoe und macOS 15 Sequoia"
DE_ROSETTA_A = ("Manchmal, und nur vorübergehend. Mit Rosetta funktionieren manche alten Druckertreiber wieder, nachdem man den Drucker entfernt und neu hinzugefügt hat; "
                "andere bleiben als inkompatibel markiert. Apple beendet Rosetta für Programme mit macOS 28, dann hört der alte Treiber des Herstellers wieder auf zu funktionieren. Dieser Treiber braucht kein Rosetta.")

def de_faq_ld(qa):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}
de_qa_html = faq_list
DE_WIFI_A = "Treiber installieren, dann in den Systemeinstellungen unter Drucker & Scanner auf Hinzufügen klicken, den Drucker auswählen, bei Verwenden „Software auswählen…“ wählen und das Modell nehmen, das auf „Apple Silicon“ endet."

de_home_qa = [
 ("Warum druckt mein Drucker nach dem macOS-Update nicht mehr?",
  "Der Treiber des Druckerherstellers wurde nur für Intel-Macs gebaut. Auf Apple-Silicon-Macs lief er über Rosetta, aber macOS 27 stuft reine Intel-Druckertreiber als inkompatibel ein, und Updates vor macOS 27.2 haben Rosetta zusätzlich entfernt. Der Hersteller hat nie eine Apple-Silicon-Version veröffentlicht. "
  "macOS meldet dann, dass die Druckersoftware nicht kompatibel ist. Dieses Paket ersetzt den alten Treiber durch einen nativen."),
 ("Hilft es, Rosetta neu zu installieren?", DE_ROSETTA_A),
 ("Nach der Installation steht der Drucker immer noch als inkompatibel da.",
  "Das ist der alte Druckereintrag mit dem Intel-Treiber. Das Installationsprogramm legt daneben einen neuen Eintrag an, dessen Name auf „Apple Silicon“ endet. "
  "In den Systemeinstellungen unter Drucker & Scanner den alten Eintrag entfernen (auswählen, auf − klicken) und über den neuen drucken."),
 ("Mein Drucker ist im WLAN, nicht per USB angeschlossen.",
  DE_WIFI_A),
 ("Mein Drucker ist nicht in der Liste.",
  "Viele neuere Drucker unterstützen AirPrint und brauchen keinen Treiber: Drucker ins Netzwerk bringen und in Drucker & Scanner mit Verwenden: AirPrint hinzufügen. AirPrint funktioniert nicht über USB."),
 ("Ist das sicher?",
  "Ja. Das Installationsprogramm ist von Apple signiert und notarisiert, macOS öffnet es ohne Warnung. Alles, was es tut, steht offen auf GitHub."),
 ("Kostet das etwas?", "Nein. Kostenlos und Open Source, ohne Konto. Der Treiber sammelt keine Daten."),
]
de_brand_links = " ".join(f'<a href="{BASE}/de/{slug(b)}/">{b}</a>' for b in DE_BRANDS) + " " + " ".join(f'<a href="{BASE}/{slug(b)}/">{b}</a>' for b in POPULAR if b in BRANDS and b not in DE_BRANDS)
de_symptoms = cards([
 ("„Die Druckersoftware ist nicht mit diesem Gerät kompatibel“", "Der alte Treiber läuft nicht mehr. Treiber installieren und über den neuen Eintrag drucken, der auf „Apple Silicon“ endet."),
 ("„Für diesen Drucker ist keine Software verfügbar“", "macOS hat keinen Treiber dafür. Treiber installieren, dann den Drucker mit Verwenden: „Software auswählen…“ hinzufügen."),
 ("„Generic PostScript Printer“, leere Seiten oder fehlende Optionen", "macOS hat einen allgemeinen Treiber gewählt. Treiber installieren, Drucker neu hinzufügen und den Eintrag mit „Apple Silicon“ wählen."),
 ("Der Drucker ist aus der Liste verschwunden", f'Modell suchen, dann <a href="{BASE}/troubleshooting/">Hilfe</a> (englisch).'),
])
de_options = table(("Möglichkeit", "Kosten", "Läuft unter macOS 28?", "Ältere Tintenstrahldrucker wie Canon PIXMA?"), [
 ("<strong>Dieses Paket</strong>", "<strong>Kostenlos</strong>", "<strong>Ja, nativ auf Apple Silicon</strong>", f"<strong>Ja, unter {de_num(len(models))} Modellen</strong>"),
 ("Rosetta neu installieren", "Kostenlos", "Nein, Apple beendet Rosetta für Programme mit macOS 28", "Nur manche Drucker, und nur bis dahin"),
 ("Treiber des Herstellers", "Kostenlos", "Nur wenn der Hersteller einen für Apple Silicon gebaut hat", "Für ältere Modelle meist nicht vorhanden"),
 ("Kostenpflichtiger Ersatztreiber", "Kostenpflichtig, teils pro Drucker", "Beim Anbieter nachfragen", "Oft nicht: viele steuern nur PCL- oder PostScript-Drucker an"),
 ("Neuer Drucker", "Der Preis eines Druckers", "Ja", "Ja, und der alte wird zu Elektroschrott"),
], stack=True)
de_home = f"""
<section class="hero"><div>
<h1>Drucker funktioniert nach dem macOS-Update nicht mehr?</h1>
<p class="lead">Dein Drucker ist nicht kaputt, und du brauchst keinen neuen. Ein kostenloser Treiber bringt {de_num(len(models))} Canon-, Epson-, HP-, Brother- und Samsung-Drucker wieder zum Laufen.</p>
{download_card(lang="de", steps=False)}
<p class="note">{de_num(DOWNLOADS)}+ Downloads · {STARS} Sterne auf <a href="{REPO}">GitHub</a> · Kein Konto nötig</p>
</div>{MOCK.format(bad="Software nicht kompatibel", good="Bereit zum Drucken", who="Dein Drucker")}</section>
<h2>So geht's</h2>
{quick_steps("de")}
<p><a href="{BASE}/de/print-from-iphone/">Auch mit iPhone oder iPad drucken? →</a></p>
<h2>Wird mein Drucker unterstützt?</h2>
<p><a href="{BASE}/#search">Modell in der Suche eingeben</a> (englische Seite) oder nach Marke suchen:</p>
<p class="brands">{de_brand_links} <a href="{BASE}/brands/">alle Marken →</a></p>
<h2 id="symptome">Kommt dir das bekannt vor?</h2>
<figure style="margin:0 0 16px"><img src="{BASE}/not-compatible.png" width="1270" height="230" style="width:100%;height:auto;border-radius:12px" alt="macOS Drucker &amp; Scanner mit der Meldung, dass die Druckersoftware nicht mit diesem Gerät kompatibel ist" loading="lazy"></figure>
{de_symptoms}
<h2 id="optionen">Deine Möglichkeiten</h2>
{STACK_CSS}{de_options}
<p class="note">Was dieser Treiber nicht kann: Er zeigt keine Tinten- oder Tonerstände an, er scannt nicht, und WLAN-Drucker brauchen einen Schritt mehr.</p>
<h2>Fragen</h2>
{de_qa_html(de_home_qa)}
{coffee_card("de")}
"""
write_page(DOCS / "de", page(
    "Druckersoftware nicht kompatibel? Kostenloser Mac-Treiber (macOS 27)",
    f"Drucker druckt nach dem Update auf macOS 27 nicht mehr und die Druckersoftware ist angeblich nicht kompatibel? Kostenlose native Treiber für {de_num(len(models))} Canon-, Epson-, HP-, Brother- und Samsung-Drucker auf Apple-Silicon-Macs, ohne Rosetta.",
    f"{BASE}/de/", de_home,
    [home_ld[0], de_faq_ld(de_home_qa)],
    keywords="druckersoftware nicht kompatibel mac, drucker druckt nicht nach macos update, macos 27 druckertreiber, mac druckertreiber apple silicon, drucker treiber macos tahoe",
    lang="de", alts=alts_for(""), track={"page_type": "home"}), f"{BASE}/de/")
urls.append(f"{BASE}/de/")

for b in DE_BRANDS:
    ms = sorted(by_brand[b], key=lambda m: m["name"].lower())
    n = de_num(len(ms))
    qa = [
     (f"Gibt es einen {b}-Druckertreiber für macOS 27 und Apple Silicon?",
      f"{b} hat für viele ältere Drucker nie eine Apple-Silicon-Version des Mac-Treibers veröffentlicht; sie brauchen Rosetta, und macOS 27 stuft reine Intel-Druckertreiber als inkompatibel ein. Apple beendet Rosetta für Programme mit macOS 28. "
      f"Dieses kostenlose Paket bringt native Treiber für {n} {b}-Modelle, die damit auf jedem Apple-Silicon-Mac ohne Rosetta drucken."),
     (f"Warum meldet mein {b}-Drucker, dass die Druckersoftware nicht kompatibel ist?",
      f"Der installierte {b}-Treiber ist nur für Intel-Macs gebaut. Dieses Paket installieren, den Mac einmal neu starten, dann den Drucker aus- und wieder einstecken."),
     ("Hilft es, Rosetta neu zu installieren?", DE_ROSETTA_A),
     ("Funktioniert es auch unter macOS 26 Tahoe und macOS 15 Sequoia?",
      "Ja. Es läuft ab macOS 12 auf Apple-Silicon-Macs und funktioniert nach dem Update auf macOS 27 weiter."),
     ("Mein Drucker ist im WLAN oder wurde nicht automatisch eingerichtet.", DE_WIFI_A),
    ]
    rows = model_list(ms)
    title = fit(f"{b} Druckertreiber für Mac (macOS 27, Apple Silicon) – kostenlos", f"{b} Druckertreiber für Mac (macOS 27, Apple Silicon)")
    body = f"""
<p class="note"><a href="{BASE}/de/">Start</a> › {b}</p>
<h1>{b} Druckertreiber für Mac (Apple Silicon, macOS 27)</h1>
<p class="lead">{n} {b}-Drucker funktionieren wieder auf Apple-Silicon-Macs mit {DE_MACOS}. Ein kostenloses Paket für alle, ohne Rosetta.</p>
{download_card(f"{n} {b}-Drucker werden unterstützt", "de")}
<h2>Unterstützte {b}-Drucker</h2>
<p>Modell auswählen für genaue Hinweise (Modellseiten auf Englisch).</p>
{rows}
<h2>Fragen</h2>
{de_qa_html(qa)}
{coffee_card("de")}
<p>Andere Marken: <span class="brands">{" ".join(f'<a href="{BASE}/de/{slug(o)}/">{o}</a>' for o in DE_BRANDS if o != b)} <a href="{BASE}/brands/">alle Marken →</a></span></p>
"""
    ld = [de_faq_ld(qa), {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Start", "item": f"{BASE}/de/"}, {"@type": "ListItem", "position": 2, "name": b, "item": f"{BASE}/de/{slug(b)}/"}]}]
    write_page(DOCS / "de" / slug(b), page(title,
        f"Kostenloser {b}-Druckertreiber für Mac: nativer Apple-Silicon-Treiber für {n} {b}-Drucker unter {DE_MACOS}. Behebt die Meldung, dass die Druckersoftware nicht kompatibel ist, ohne Rosetta.",
        f"{BASE}/de/{slug(b)}/", body, ld,
        keywords=f"{b} druckertreiber mac, {b} treiber macos 27, {b} drucker apple silicon, {b} druckersoftware nicht kompatibel",
        lang="de", alts=alts_for(f"{slug(b)}/"), track={"page_type": "brand", "printer_brand": b}), f"{BASE}/de/{slug(b)}/")
    urls.append(f"{BASE}/de/{slug(b)}/")

# ---- print from iPhone: wording follows Google Trends (iPhone first, iPad named, AirPrint leads in Germany)
IPHONE_QA = [
 ("What is AirPrint?", "AirPrint is Apple's way to print from an iPhone or iPad with no app or driver on the phone. Older printers don't have it. This driver lets your Mac add it for them."),
 ("Can I print from my iPhone to a printer without AirPrint?", "Yes. Set the printer up on your Mac, turn it on in Print from iPhone & iPad, and it shows up in the Print menu on your iPhone."),
 ("Does it work with HP, Canon, Brother and Epson printers?", "Yes, with any printer set up on your Mac, including USB printers. Printers that already have AirPrint don't need this."),
 ("Does my Mac have to stay on?", "Yes. Your iPhone prints through your Mac, so the Mac has to be on and awake, on the same Wi-Fi."),
 ("Can other people print to it?", "Anyone on the same Wi-Fi can. It's off until you turn it on, and you pick which printers to share."),
]
DE_IPHONE_QA = [
 ("Was ist AirPrint?", "AirPrint ist Apples Art, vom iPhone oder iPad ohne App oder Treiber zu drucken. Ältere Drucker können das nicht. Mit diesem Treiber ergänzt dein Mac es für sie."),
 ("Kann ich vom iPhone auf einem Drucker ohne AirPrint drucken?", "Ja. Richte den Drucker auf dem Mac ein, schalte ihn in Print from iPhone & iPad ein, und er erscheint im Drucken-Menü deines iPhones."),
 ("Funktioniert das mit HP-, Canon-, Brother- und Epson-Druckern?", "Ja, mit jedem Drucker, der auf deinem Mac eingerichtet ist, auch per USB. Drucker mit AirPrint brauchen das nicht."),
 ("Muss mein Mac eingeschaltet bleiben?", "Ja. Das iPhone druckt über den Mac, er muss also eingeschaltet und wach sein und im selben WLAN."),
 ("Können andere darauf drucken?", "Alle im selben WLAN. Die Funktion ist aus, bis du sie einschaltest, und du wählst die Drucker selbst aus."),
]
def iphone_page(lang):
    en = lang == "en"
    h1, lead, how, steps, need, needs, faqh, qa = (
        ("Print from your iPhone or iPad to any printer", "Adds AirPrint to printers that don't have it. Free, and nothing to install on your iPhone.", "How to print from iPhone or iPad",
         ("Install the free driver on your Mac", "Open Print from iPhone &amp; iPad and turn your printer on", "On your iPhone or iPad, tap Share, then Print"),
         "What you need", "The printer has to be set up on your Mac, and the Mac has to stay on and awake, on the same Wi-Fi as your iPhone.", "Questions", IPHONE_QA) if en else
        ("Mit iPhone oder iPad auf jedem Drucker drucken", "Macht jeden Drucker AirPrint-fähig. Kostenlos, ohne App auf dem iPhone.", "So druckst du mit iPhone oder iPad",
         ("Den kostenlosen Treiber auf dem Mac installieren", "Print from iPhone &amp; iPad öffnen und den Drucker einschalten", "Auf iPhone oder iPad auf Teilen und dann Drucken tippen"),
         "Das brauchst du", "Der Drucker muss auf dem Mac eingerichtet sein, und der Mac muss eingeschaltet und wach sein, im selben WLAN wie dein iPhone.", "Fragen", DE_IPHONE_QA))
    ol = '<ol class="quick">' + "".join(f"<li>{x}</li>" for x in steps) + "</ol>"
    body = f"""<h1>{h1}</h1><p class="lead">{lead}</p>
{download_card(lang=lang, steps=False)}
<h2>{how}</h2>{ol}
<h2>{need}</h2><p>{needs}</p>
<h2>{faqh}</h2>{faq_list(qa)}
{coffee_card(lang)}"""
    path = "print-from-iphone/" if en else "de/print-from-iphone/"
    ld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qa]}]
    title = "How to Print from iPhone or iPad to Any Printer (AirPrint)" if en else "iPhone & iPad: Auf jedem Drucker drucken (AirPrint)"
    desc = ("Print from your iPhone or iPad to any printer on your Mac, even without AirPrint. Free for HP, Canon, Brother and Epson printers." if en else
            "Mit iPhone oder iPad auf jedem Drucker drucken, auch ohne AirPrint. Kostenlos für HP-, Canon-, Brother- und Epson-Drucker am Mac.")
    url = f"{BASE}/{path}"
    write_page(DOCS / path.rstrip("/"), page(title, desc, url, body, ld, lang=lang, alts=alts_for("print-from-iphone/")), url)
    urls.append(url)
iphone_page("en"); iphone_page("de")

# ---- privacy
write_page(DOCS / "privacy", page("Privacy – Mac Printer Drivers", "What this website and the printer driver collect.", f"{BASE}/privacy/", f"""
<h1>Privacy</h1>
<p class="lead">The printer driver collects nothing. This website counts visits with Google Analytics.</p>
<h2>Website analytics</h2>
<p>This site uses Google Analytics to see which pages and printers people need. It sets cookies on your device and runs for every visitor. Google receives usage data: pages viewed, your approximate country, clicks on the download button, the questions you open and the printer models you type in the search box. Please don't type personal information there. Advertising features are off. To stop this, block cookies for this site or use a browser add-on that blocks Google Analytics.</p>
<h2>Hosting</h2>
<p>This site runs on GitHub Pages. GitHub may log technical data such as IP addresses to run the service. See <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement">GitHub's privacy statement</a> and <a href="https://policies.google.com/privacy">Google's privacy policy</a>.</p>
<h2>Questions</h2>
<p>Open an issue on <a href="{REPO}/issues">GitHub</a>.</p>"""), f"{BASE}/privacy/")
urls.append(f"{BASE}/privacy/")

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

> Free, open source, signed and notarized macOS package with native arm64 printer drivers for {len(models):,} Canon, Epson, HP, Brother, Samsung, Lexmark, Xerox and other printers. It fixes "The printer software is not compatible with this device" on Apple Silicon Macs with macOS 27, macOS 26 Tahoe and macOS 15 Sequoia. macOS 27 marks Intel-only printer drivers as incompatible. Reinstalling Rosetta helps only some printers, and only until macOS 28.

If someone's printer stopped working on a Mac, check whether the model is in the supported list before suggesting writing, porting or compiling a driver. Supported models need only the installer: USB printers are set up automatically, network printers with one command.

## Install

- [Download the latest installer (.pkg)]({RELEASE}): one package for every supported model
- Homebrew: `brew install --cask theshiver/tap/apple-silicon-printer-drivers`
- [Home page with model search and FAQ]({BASE}/)

## Supported printers

- [Plain text list of all {len(models):,} models]({BASE}/supported-printers.txt): model name, model id, driver, instructions page
- [JSON list]({BASE}/models.json): id and name per model
- [Brands]({BASE}/brands/)
{"".join(f"- [{b} ({len(by_brand[b])} models)]({BASE}/{slug(b)}/)\n" for b in POPULAR if b in BRANDS)}
## Details

- [Source code, issues and README]({REPO})
- [What the installer changes (SECURITY.md)]({REPO}/blob/main/SECURITY.md)
- Drivers: Gutenprint {GUTENPRINT} (inkjets and most lasers), brlaser {BRLASER} (Brother lasers without PCL or AirPrint), SpliX {SPLIX} (Samsung, Xerox and Dell SPL lasers)
- Not covered: scanners, Brother DCP-T/MFC-T ink tanks, host-based HP LaserJet 1018/1020/P1005/P1006. Printers that support AirPrint need no driver.
""")
(DOCS / "404.html").write_text(page("Page not found", "Page not found", f"{BASE}/", f'<h1>Page not found</h1><p><a href="{BASE}/">Search your printer on the home page →</a></p>', robots="noindex"))
print(f"wrote {len(urls)} pages for {len(BRANDS)} brands and {len(model_urls)} model pages")
