#!/usr/bin/env python3
"""Submits live URLs to IndexNow (Bing, Yandex, Seznam, Naver).
Run after the site is deployed, so the key file is live:

  python3 site/indexnow.py
"""
import json, re, pathlib, urllib.request

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
BASE = "https://macprinterdrivers.com"
KEY = re.search(r'INDEXNOW_KEY = "([0-9a-f]+)"', (DOCS.parent / "site" / "build-site.py").read_text()).group(1)


def collect_urls():
    seen = set()
    urls = []

    def add(u):
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    for f in sorted(DOCS.glob("sitemap-*.xml")):
        for u in re.findall(r"<loc>(.*?)</loc>", f.read_text()):
            add(u)
    for line in (DOCS / "supported-printers.txt").read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4 and parts[3].startswith(BASE):
            add(parts[3])
    add(f"{BASE}/llms.txt")
    add(f"{BASE}/supported-printers.txt")
    return urls


def main():
    urls = collect_urls()
    body = json.dumps({
        "host": "macprinterdrivers.com",
        "key": KEY,
        "keyLocation": f"{BASE}/{KEY}.txt",
        "urlList": urls,
    }).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        body,
        {"Content-Type": "application/json; charset=utf-8", "User-Agent": "apple-silicon-printer-drivers-indexnow/1.0"},
    )
    with urllib.request.urlopen(req) as r:
        print(f"submitted {len(urls)} urls: HTTP {r.status}")


if __name__ == "__main__":
    main()
