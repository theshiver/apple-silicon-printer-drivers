#!/usr/bin/env python3
"""Weekly read-only SEO & AI-SEO radar for macprinterdrivers.com."""
import argparse
import collections
import datetime as dt
import json
import os
import pathlib
import re
import sys
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

CFG = os.path.expanduser("~/.config/seo-stats/google-api.json")
SC = "https://www.googleapis.com/webmasters/v3"
GA_DATA = "https://analyticsdata.googleapis.com/v1beta"
NEW_SITE = "https://macprinterdrivers.com/"
OLD_SITE = "https://theshiver.github.io/apple-silicon-printer-drivers/"
GA_PID = "properties/562532170"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def make_session():
    try:
        key_path = os.path.expanduser(json.load(open(CFG))["service_account_path"])
    except (OSError, KeyError, ValueError):
        sys.exit(f"Credentials missing: could not read service_account_path from {CFG}")
    scopes = [
        "https://www.googleapis.com/auth/webmasters.readonly",
        "https://www.googleapis.com/auth/analytics.readonly",
    ]
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return AuthorizedSession(creds)


def gsc_query(sess, site, start, end, dims=None, limit=25000):
    body = {"startDate": str(start), "endDate": str(end), "rowLimit": limit}
    if dims:
        body["dimensions"] = dims
    r = sess.post(f"{SC}/sites/{quote(site, safe='')}/searchAnalytics/query", json=body)
    return r.json().get("rows", []) if r.ok else []


def ga_report(sess, start, end, dims, metrics, filt=None, limit=200):
    body = {
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": d} for d in dims],
        "metrics": [{"name": m} for m in metrics],
        "limit": limit,
    }
    if filt:
        body["dimensionFilter"] = filt
    r = sess.post(f"{GA_DATA}/{GA_PID}:runReport", json=body)
    return r.json() if r.ok else {}


def load_indexed_models():
    txt = (ROOT / "site" / "build-site.py").read_text()
    m = re.search(r"INDEXED_MODELS\s*=\s*\{(.*?)\}", txt, re.S)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def build_report(days):
    sess = make_session()
    end = dt.date.today() - dt.timedelta(days=2)
    start = end - dt.timedelta(days=days - 1)
    pend = start - dt.timedelta(days=1)
    pstart = pend - dt.timedelta(days=days - 1)

    lines = [f"# Weekly SEO & AI-SEO Radar ({start} .. {end} vs {pstart} .. {pend})", ""]

    lines.append("## 1. Google Search Console Totals & Trend")
    for label, site in [("macprinterdrivers.com", NEW_SITE), ("github.io (old)", OLD_SITE)]:
        cur = gsc_query(sess, site, start, end)
        prev = gsc_query(sess, site, pstart, pend)
        c = cur[0] if cur else {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}
        p = prev[0] if prev else {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}
        lines.append(
            f"- **{label}:** {c['impressions']:.0f} impr (prev {p['impressions']:.0f}), "
            f"{c['clicks']:.0f} clicks (prev {p['clicks']:.0f}), CTR {c['ctr']*100:.1f}%, pos {c['position']:.1f}"
        )

    daily = gsc_query(sess, NEW_SITE, start, end, ["date"])
    if daily:
        lines.append("")
        lines.append("Daily `macprinterdrivers.com`: " + ", ".join(
            f"{r['keys'][0][5:]}={r['impressions']:.0f}/{r['clicks']:.0f}" for r in sorted(daily, key=lambda x: x["keys"][0])
        ))

    q_cur = {r["keys"][0]: r for r in gsc_query(sess, NEW_SITE, start, end, ["query"])}
    q_prev = {r["keys"][0]: r for r in gsc_query(sess, NEW_SITE, pstart, pend, ["query"])}
    p_cur = {r["keys"][0]: r for r in gsc_query(sess, NEW_SITE, start, end, ["page"])}

    ctr_ops = [
        (r["impressions"], r["clicks"], r["position"], r["ctr"] * 100, k)
        for k, r in list(q_cur.items()) + list(p_cur.items())
        if r["impressions"] >= 20 and r["position"] <= 15 and r["ctr"] < 0.03
    ]
    lines.extend(["", "## 2. CTR Opportunities (impr >= 20, pos <= 15, CTR < 3%)"])
    if ctr_ops:
        for impr, clk, pos, ctr, key in sorted(ctr_ops, reverse=True)[:12]:
            lines.append(f"- `{key}` — {impr:.0f} impr, {clk:.0f} clicks, pos {pos:.1f}, CTR {ctr:.1f}%")
    else:
        lines.append("- No queries/pages met the threshold in this window.")

    striking = [
        (r["impressions"], r["clicks"], r["position"], k)
        for k, r in q_cur.items()
        if r["impressions"] >= 10 and 10 < r["position"] <= 25
    ]
    lines.extend(["", "## 3. Striking Distance Queries (pos 10–25, impr >= 10)"])
    if striking:
        for impr, clk, pos, key in sorted(striking, reverse=True)[:12]:
            lines.append(f"- `{key}` — {impr:.0f} impr, {clk:.0f} clicks, pos {pos:.1f}")
    else:
        lines.append("- None in this window.")

    new_q = [
        (r["impressions"], r["clicks"], r["position"], k)
        for k, r in q_cur.items()
        if k not in q_prev
    ]
    lines.extend(["", "## 4. Newly Emerging Queries"])
    for impr, clk, pos, key in sorted(new_q, reverse=True)[:12]:
        lines.append(f"- `{key}` — {impr:.0f} impr, {clk:.0f} clicks, pos {pos:.1f}")

    ga_start = f"{days}daysAgo"
    ch_res = ga_report(sess, ga_start, "yesterday", ["sessionDefaultChannelGroup", "eventName"], ["eventCount"], limit=200)
    by_ch = collections.defaultdict(dict)
    for row in ch_res.get("rows", []):
        ch, ev = row["dimensionValues"][0]["value"], row["dimensionValues"][1]["value"]
        cnt = int(row["metricValues"][0]["value"])
        if ev in ("session_start", "driver_download", "coffee_click"):
            by_ch[ch][ev] = cnt

    lines.extend(["", f"## 5. GA4 Channels & Conversions (last {days} days)"])
    lines.append("| Channel | Starts | Downloads | DL % | Coffee | Coffee % |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for ch, d in sorted(by_ch.items(), key=lambda x: -x[1].get("session_start", 0)):
        st = d.get("session_start", 0)
        dl = d.get("driver_download", 0)
        cf = d.get("coffee_click", 0)
        dl_p = f"{100 * dl / st:.1f}%" if st else "-"
        cf_p = f"{100 * cf / st:.2f}%" if st else "-"
        lines.append(f"| {ch} | {st} | {dl} | {dl_p} | {cf} | {cf_p} |")

    indexed = load_indexed_models()
    dl_pages = ga_report(
        sess, ga_start, "yesterday", ["pagePath"], ["eventCount"],
        filt={"filter": {"fieldName": "eventName", "stringFilter": {"value": "driver_download"}}},
        limit=100,
    )
    candidates = []
    for row in dl_pages.get("rows", []):
        path = row["dimensionValues"][0]["value"].strip("/")
        cnt = int(row["metricValues"][0]["value"])
        parts = path.split("/")
        if len(parts) == 2 and path not in indexed and not path.startswith(("apple-silicon-printer-drivers", "fix")):
            candidates.append((cnt, path))
    lines.extend(["", "## 6. Tier-1 Promotion Candidates (High GA4 Downloads, Not Yet Indexed in Google)"])
    if candidates:
        for cnt, path in sorted(candidates, reverse=True)[:12]:
            lines.append(f"- `{path}` — {cnt} driver downloads")
    else:
        lines.append("- Top downloaded model pages are already in `INDEXED_MODELS`.")

    lines.extend(["", "## 7. Recommended Next Experiment (Review & Approve)"])
    if ctr_ops:
        lines.append(f"- Test title/meta rewrite on `{ctr_ops[0][4]}` ({ctr_ops[0][0]:.0f} impr, {ctr_ops[0][3]:.1f}% CTR).")
    if candidates:
        lines.append(f"- Enrich and promote `{candidates[0][1]}` ({candidates[0][0]} downloads) into `INDEXED_MODELS`.")
    if not ctr_ops and not candidates:
        lines.append("- Monitor index recovery across `/` and `/fix/*` pages before making further structural changes.")

    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--out")
    args = p.parse_args()
    report = build_report(args.days)
    if args.out:
        pathlib.Path(args.out).write_text(report)
        print(f"Wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
