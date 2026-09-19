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
PKG = "AppleSilicon-Printer-Drivers-1.3.4.pkg"
TODAY = datetime.date.today().isoformat()

models = json.load(open(DOCS / "models.json"))

# brand normalisation: first word of the display name, with a few fixes
ALIAS = {"Dai": "DNP", "PIXMA": "Canon", "imageRunner": "Canon", "Phaser": "Xerox",
         "e-Studio": "Toshiba", "MP": "Ricoh", "Datamax-ONeil": "Datamax"}
def brand_of(m):
    b = m["name"].split()[0]
    return ALIAS.get(b, b)

by_brand = collections.defaultdict(list)
for m in models:
    by_brand[brand_of(m)].append(m)
# only brands with a handful of models get their own page
BRANDS = sorted([b for b, l in by_brand.items() if len(l) >= 4], key=lambda b: -len(by_brand[b]))
slug = lambda s: re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--muted:#666;--line:#e5e5e5;--accent:#0a66c2;--code:#f4f4f6;--ok:#137333}
@media(prefers-color-scheme:dark){:root{--bg:#111;--fg:#eee;--muted:#aaa;--line:#2a2a2a;--accent:#6cb4ff;--code:#1c1c1f;--ok:#7bd88f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 64px}header{padding:12px 16px;border-bottom:1px solid var(--line)}
header a{color:var(--fg);text-decoration:none;font-weight:600}header nav a{margin-left:16px;font-weight:400;color:var(--muted)}
h1{font-size:1.9rem;line-height:1.2;margin:.4em 0}h2{margin-top:2em;border-bottom:1px solid var(--line);padding-bottom:.25em}
a{color:var(--accent)}p.lead{font-size:1.1rem;color:var(--muted)}
input[type=search]{width:100%;font-size:1.15rem;padding:12px 14px;border:2px solid var(--line);border-radius:10px;background:var(--bg);color:var(--fg)}
input[type=search]:focus{outline:none;border-color:var(--accent)}
#results{list-style:none;padding:0;margin:8px 0 0}#results li{padding:10px 12px;border:1px solid var(--line);border-radius:8px;margin-top:8px;cursor:pointer}
#results li:hover,#results li.sel{border-color:var(--accent)}#results small{color:var(--muted)}
pre,code{font:.95em ui-monospace,SFMono-Regular,Menlo,monospace}pre{background:var(--code);padding:12px 14px;border-radius:8px;overflow:auto;position:relative}
code{background:var(--code);padding:1px 5px;border-radius:4px}pre code{background:none;padding:0}
button.copy{position:absolute;top:8px;right:8px;font-size:.8rem;padding:4px 8px;border:1px solid var(--line);background:var(--bg);color:var(--fg);border-radius:6px;cursor:pointer}
ol.steps li{margin:.6em 0}.card{border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:18px 0}
.hidden{display:none}.note{color:var(--muted);font-size:.95rem}.brands a{display:inline-block;margin:4px 8px 4px 0}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
footer{color:var(--muted);font-size:.9rem;margin-top:48px;border-top:1px solid var(--line);padding-top:16px}
"""

def page(title, desc, canonical, body, jsonld=None, keywords=""):
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, separators=(",",":"))}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{f'<meta name="keywords" content="{html.escape(keywords)}">' if keywords else ''}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{BASE}/not-compatible.png"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE}/not-compatible.png">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%96%A8%3C/text%3E%3C/svg%3E">
{ld}
<style>{CSS}</style>
</head>
<body>
<header><a href="{BASE}/">🖨 Apple Silicon Printer Drivers</a>
<nav style="display:inline"><a href="{RELEASE}">Download</a><a href="{BASE}/#search">Is my printer supported?</a><a href="{BASE}/brands/">Brands</a><a href="{REPO}">GitHub</a><a href="https://github.com/sponsors/theshiver">☕ Buy me a coffee</a></nav></header>
<main>
{body}
<footer>Open source (Gutenprint GPL-2.0, scripts MIT) · <a href="https://github.com/sponsors/theshiver">☕ Buy me a coffee</a> · <a href="{REPO}">Source &amp; issues on GitHub</a> · Not affiliated with Canon, Epson, HP or Apple. Product names are trademarks of their owners.</footer>
</main>
</body></html>"""

INSTALL_STEPS = f"""
<ol class="steps">
<li>Plug the printer into the Mac with a USB cable and switch it on.</li>
<li><a href="{RELEASE}"><strong>Download the installer (.pkg)</strong></a> and open it. Click through, enter your Mac password. It is signed and notarized by Apple, so there are no security warnings.</li>
<li>Print something. The installer recognised the printer and set it up as the default.</li>
</ol>
<p class="note"><strong>Had the printer maker's old driver installed</strong> (Canon IJ, etc.)? Restart the Mac once, then unplug and re-plug the printer. The old driver is moved to <code>/Users/Shared/printer-driver-backup</code>, nothing is deleted.</p>"""

def brand_page(b):
    ms = sorted(by_brand[b], key=lambda m: m["name"].lower())
    rows = "\n".join(f'<tr><td>{html.escape(m["name"])}</td><td><code>sudo gutenprint-add {html.escape(m["id"])}</code></td></tr>' for m in ms)
    title = f"{b} printer driver for Apple Silicon Mac (M1/M2/M3/M4) — {len(ms)} models"
    desc = f"Free native arm64 macOS driver for {len(ms)} {b} printers. Fixes 'The printer software is not compatible with this device' on macOS 27 without Rosetta. Step-by-step install."
    body = f"""
<h1>{html.escape(b)} printer drivers for Apple Silicon Macs</h1>
<p class="lead">{len(ms)} {html.escape(b)} models work on M-series Macs with this free, native (arm64) driver — no Rosetta, no {html.escape(b)} software needed.</p>
<div class="card"><strong>Search your exact model instead:</strong> <a href="{BASE}/#search">use the search box on the home page</a> — it shows the one command you need.</div>
<h2>Install (same package for every model)</h2>
{INSTALL_STEPS}
<h2>Printer not set up automatically?</h2>
<p>USB printers are normally detected by the installer. If yours wasn't (or it's on Wi-Fi), find it below, open Terminal (⌘+Space, type <em>Terminal</em>), paste its command and press Enter.</p>
<table><thead><tr><th>Model</th><th>Command</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">Network / Wi-Fi printer? Add the device address: <code>sudo gutenprint-add &lt;id&gt; MyPrinter socket://192.168.1.50</code> (<code>lpinfo -v</code> lists what macOS sees), or add it in System Settings → Printers &amp; Scanners → Use: Select Software… and pick the "Apple Silicon" entry.</p>
<p><a href="{BASE}/brands/">← All brands</a></p>
"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "numberOfItems": len(ms), "itemListElement": [{"@type": "ListItem", "position": i+1, "name": m["name"]} for i, m in enumerate(ms[:200])]}
    return page(title, desc, f"{BASE}/{slug(b)}/", body, ld, keywords=f"{b} driver mac, {b} apple silicon, {b} macos 27, printer software not compatible with this device")

# ---- write brand pages
urls = []
for b in BRANDS:
    d = DOCS / slug(b); d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(brand_page(b))
    urls.append(f"{BASE}/{slug(b)}/")

# ---- brands index
brand_links = "\n".join(f'<a href="{BASE}/{slug(b)}/">{html.escape(b)} ({len(by_brand[b])})</a>' for b in BRANDS)
(DOCS / "brands").mkdir(exist_ok=True)
(DOCS / "brands" / "index.html").write_text(page(
    "Supported printer brands — Apple Silicon Mac drivers",
    f"{len(models)} printer models from {len(BRANDS)} brands supported by the native arm64 Gutenprint driver for macOS.",
    f"{BASE}/brands/",
    f"<h1>Supported brands</h1><p class='lead'>{len(models)} models. Click a brand for the full list with copy-paste commands.</p><p class='brands'>{brand_links}</p>"))
urls.append(f"{BASE}/brands/")

# ---- home
examples = [("Canon PIXMA MP250", "bjc-MULTIPASS-MP250"), ("Canon PIXMA iP4300", "bjc-PIXMA-iP4300"), ("Epson Stylus Photo R300", "escp2-r300"),
            ("HP LaserJet 1010", "hp-lj_1010"), ("Brother HL-5040", "brother-hl-5040"), ("Samsung ML-2150", "samsung-ml-2150")]
ex_rows = "\n".join(f'<tr><td>{n}</td><td><code>sudo gutenprint-add {i}</code></td></tr>' for n, i in examples)
faq = [
 ("Why does my Mac say “The printer software is not compatible with this device”?",
  "Your printer's driver was compiled for Intel Macs only. macOS 27 flags Intel-only printer software on Apple Silicon (M1–M4) Macs, and Rosetta, which used to run it, is being phased out. This site provides a native replacement."),
 ("Which printers get set up automatically?", "Any printer connected over USB during installation whose USB name matches a model in the database — e.g. “Canon MP250 series”, “EPSON Stylus Photo R300”, “Brother HL-5040 series”. Others take one gutenprint-add command, shown when you search your model on this page."),
 ("Is it safe? Will macOS complain?", "The installer is signed with an Apple Developer ID and notarized by Apple, so Gatekeeper opens it without warnings. Everything it does is documented in SECURITY.md on GitHub and the install script is plain shell you can read."),
 ("Is it free?", "Yes. It is the open-source Gutenprint driver (GPL-2.0), compiled natively for Apple Silicon and packaged as a one-click macOS installer."),
 ("Does it remove my old driver?", "Only when it has to: Canon's IJ driver installs a kernel extension that blocks macOS's own USB printer driver, so the installer moves it to /Users/Shared/printer-driver-backup (nothing is deleted). Other vendors' drivers are left in place."),
 ("Does the scanner of my all-in-one work?", "No. Only printing is covered. For scanning use SANE (Homebrew) or VueScan, which have native Apple Silicon support."),
 ("My printer is on Wi-Fi, not USB.", "Install the package, then add the printer in System Settings → Printers & Scanners, choose Use: Select Software… and pick the entry ending in “Apple Silicon”."),
 ("Which macOS versions?", "Built and tested on macOS 27 (Apple Silicon). It should work on macOS 12 and later on M-series Macs."),
]
faq_html = "\n".join(f"<h3>{html.escape(q)}</h3><p>{html.escape(a)}</p>" for q, a in faq)
home_ld = [
 {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Apple Silicon Printer Drivers (Gutenprint arm64)",
  "operatingSystem": "macOS", "applicationCategory": "DriverApplication", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
  "downloadUrl": RELEASE, "softwareVersion": "1.1.0", "license": "https://www.gnu.org/licenses/old-licenses/gpl-2.0.html",
  "image": f"{BASE}/not-compatible.png", "description": f"Native arm64 macOS printer driver package for {len(models)} Canon, Epson, HP, Brother, Samsung and other printers. Auto-detects USB printers."},
 {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
 {"@context": "https://schema.org", "@type": "HowTo", "name": "Install a printer driver on an Apple Silicon Mac",
  "step": [{"@type": "HowToStep", "text": "Connect the printer over USB and switch it on."},
           {"@type": "HowToStep", "text": "Download the .pkg installer and open it (signed and notarized by Apple)."},
           {"@type": "HowToStep", "text": "Print. The installer sets the printer up automatically; otherwise search the model on the site for the one command to add it."}]},
]
home = f"""
<h1>Old printer, new Mac? Get it printing on Apple Silicon.</h1>
<p class="lead">Free native (arm64) macOS driver for <strong>{len(models)} printers</strong> — Canon PIXMA, Epson Stylus, HP DeskJet &amp; LaserJet, Brother, Samsung, Lexmark, Kyocera, Xerox, Ricoh, Oki, Kodak and more. Fixes <em>“The printer software is not compatible with this device”</em> on macOS 27 without Rosetta.</p>

<figure style="margin:20px 0"><img src="not-compatible.png" width="1270" height="230" style="width:100%;height:auto;border:1px solid var(--line);border-radius:10px" alt="macOS Printers &amp; Scanners showing a Canon MP250 with the error: The printer software is not compatible with this device" loading="eager"><figcaption class="note">Seeing this in System Settings → Printers &amp; Scanners? This page fixes it.</figcaption></figure>

<h2>Install</h2>
{INSTALL_STEPS}

<h2 id="search">Is my printer supported? / It wasn't set up automatically</h2>
<p>Type your model to check. If the installer didn't pick it up (Wi-Fi printer, unusual USB name, or it wasn't plugged in), you'll get the one command that adds it.</p>
<form id="qf" onsubmit="return false"><input type="search" id="q" placeholder="Type your printer model, e.g. Canon MP250, Epson R300, LaserJet 1010…" autocomplete="off"></form>
<ul id="results"></ul>
<div id="answer" class="card hidden"></div>
<p class="note">Not listed? Try fewer words (just the model number). If it still isn't there, Gutenprint doesn't support that model. Also: if macOS already sees your printer via AirPrint, you don't need any of this.</p>
<p>Or browse by brand: <span class="brands">{" ".join(f'<a href="{BASE}/{slug(b)}/">{html.escape(b)}</a>' for b in BRANDS[:16])} <a href="{BASE}/brands/">all brands →</a></span></p>

<h2>Questions</h2>
{faq_html}

<div class="card" style="text-align:center"><strong>☕ Did this save your printer?</strong><br>It's free and always will be. If you'd like to say thanks, <a href="https://github.com/sponsors/theshiver">buy me a coffee via GitHub Sponsors</a>.</div>

<h2>How it works</h2>
<p>The package is <a href="https://gimp-print.sourceforge.io/">Gutenprint 5.3.4</a> compiled for arm64 and installed under <code>/Library/Printers/Gutenprint</code>, where Apple's print system can run it, plus a small helper (<code>gutenprint-add</code>) that writes the printer description file and creates the queue. Printing goes through Apple's own USB printer class driver, so nothing Intel-only is involved. Full details, source and build scripts are <a href="{REPO}">on GitHub</a>.</p>

<script>
const BASE={json.dumps(BASE)};let MODELS=null,sel=-1;
const q=document.getElementById('q'),res=document.getElementById('results'),ans=document.getElementById('answer');
const norm=s=>s.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
async function load(){{if(!MODELS){{MODELS=await (await fetch('models.json')).json();MODELS.forEach(m=>m.n=norm(m.name+' '+m.id));}}}}
function score(m,terms){{let s=0;for(const t of terms){{if(!m.n.includes(t))return 0;s+=(m.n.split(' ').includes(t)?3:1)}}return s+Math.max(0,20-m.name.length)/20}}
async function search(){{await load();const terms=norm(q.value).split(' ').filter(Boolean);res.innerHTML='';sel=-1;if(!terms.length)return;
 const hits=MODELS.map(m=>[score(m,terms),m]).filter(x=>x[0]>0).sort((a,b)=>b[0]-a[0]).slice(0,12);
 if(!hits.length){{res.innerHTML='<li>No match. Try only the model number (e.g. “MP250”).</li>';return}}
 for(const [,m] of hits){{const li=document.createElement('li');li.innerHTML=`<strong>${{m.name}}</strong> <small>${{m.id}}</small>`;li.onclick=()=>show(m);res.appendChild(li)}}}}
function show(m){{res.innerHTML='';q.value=m.name; ans.classList.remove('hidden');ans.innerHTML=`<h3 style="margin-top:0">✅ ${{m.name}} is supported</h3>
 <p><strong>Plugged in over USB?</strong> Just <a href="{RELEASE}">install the package</a>, it sets the printer up by itself.</p>
 <p><strong>Not detected, or on Wi-Fi?</strong> After installing, open Terminal (⌘+Space, type <em>Terminal</em>) and paste:</p><pre><button class="copy">Copy</button><code>sudo gutenprint-add ${{m.id}}</code></pre><p class="note">For a network printer add a name and address: <code>sudo gutenprint-add ${{m.id}} MyPrinter socket://192.168.1.50</code></p>`;
 wire();history.replaceState(null,'','#'+encodeURIComponent(m.id));ans.scrollIntoView({{behavior:'smooth',block:'center'}})}}
q.addEventListener('input',search);q.addEventListener('keydown',e=>{{const items=[...res.children];if(e.key==='ArrowDown'){{sel=Math.min(sel+1,items.length-1)}}else if(e.key==='ArrowUp'){{sel=Math.max(sel-1,0)}}else if(e.key==='Enter'){{if(items[sel]||items[0])(items[sel]||items[0]).click();return}}else return;items.forEach((li,i)=>li.classList.toggle('sel',i===sel));e.preventDefault()}});
function wire(){{document.querySelectorAll('button.copy').forEach(b=>b.onclick=async()=>{{await navigator.clipboard.writeText(b.nextElementSibling.textContent);b.textContent='Copied';setTimeout(()=>b.textContent='Copy',1500)}})}}
function pick(){{const items=[...res.children];const it=items[sel]||items[0];if(it&&it.onclick)it.click()}}
document.getElementById('qf').addEventListener('submit',e=>{{e.preventDefault();pick()}});
q.addEventListener('search',pick);q.addEventListener('keyup',e=>{{if(e.key==='Enter')pick()}});
wire();
(async()=>{{const h=decodeURIComponent(location.hash.slice(1));if(h){{await load();const m=MODELS.find(x=>x.id===h);if(m)show(m)}}}})();
</script>
"""
(DOCS / "index.html").write_text(page(
    "Printer not compatible with your Apple Silicon Mac? Free native driver for 3,500+ printers",
    "Fix “The printer software is not compatible with this device” on M1/M2/M3/M4 Macs and macOS 27. Free native arm64 driver for Canon PIXMA, Epson Stylus, HP, Brother, Samsung and 3,500+ printers. Search your model, one command to install.",
    f"{BASE}/", home, home_ld,
    keywords="printer software is not compatible with this device, canon mp250 driver mac, apple silicon printer driver, m1 printer driver, macos 27 printer, rosetta printer driver, gutenprint mac arm64"))
urls.insert(0, f"{BASE}/")

# ---- sitemap / robots / 404
(DOCS / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod><priority>{'1.0' if u.endswith('driver/') else '0.7'}</priority></url>\n" for u in urls) + "</urlset>\n")
(DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
(DOCS / ".nojekyll").write_text("")
(DOCS / "404.html").write_text(page("Page not found", "Page not found", f"{BASE}/", f'<h1>Page not found</h1><p><a href="{BASE}/">Search your printer on the home page →</a></p>'))
print(f"wrote {len(urls)} pages for {len(BRANDS)} brands")
