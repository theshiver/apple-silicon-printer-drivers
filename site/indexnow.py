#!/usr/bin/env python3
"""Submits every URL in docs/sitemap.xml to IndexNow (Bing, Yandex, Seznam, Naver).
Run after the site is deployed, so the key file is live:

  python3 site/indexnow.py
"""
import json, re, pathlib, urllib.request

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
BASE = "https://theshiver.github.io/apple-silicon-printer-drivers"
KEY = re.search(r'INDEXNOW_KEY = "([0-9a-f]+)"', (DOCS.parent / "site" / "build-site.py").read_text()).group(1)

urls = re.findall(r"<loc>(.*?)</loc>", (DOCS / "sitemap.xml").read_text())
urls += [f"{BASE}/llms.txt", f"{BASE}/supported-printers.txt"]
body = json.dumps({"host": "theshiver.github.io", "key": KEY, "keyLocation": f"{BASE}/{KEY}.txt", "urlList": urls}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", body, {"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req) as r:
    print(f"submitted {len(urls)} urls: HTTP {r.status}")
