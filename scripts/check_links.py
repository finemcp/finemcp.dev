#!/usr/bin/env python3
"""Crawl the local Hugo site and report all non-200 responses."""
import urllib.request
import re
import sys
from collections import deque

BASE = "http://localhost:1313"
visited = set()
queue = deque([BASE + "/"])
results = []   # (status_code, url, referrer)
referrers = {}


def fetch_links(url, html):
    found = re.findall(r'href=["\']([^"\'>\s]+)', html)
    links = []
    for h in found:
        h = h.split("#")[0].strip()
        if not h:
            continue
        if h.startswith("mailto:") or h.startswith("javascript:"):
            continue
        if h.startswith("http://localhost:1313") or h.startswith("/"):
            full = h if h.startswith("http") else BASE + h
            if not full.endswith((".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp", ".woff", ".woff2", ".ttf", ".css", ".js", ".xml")):
                if full not in visited:
                    links.append(full)
    return links


while queue:
    url = queue.popleft()
    if url in visited:
        continue
    visited.add(url)
    if not url.startswith(BASE):
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LinkChecker/1.0"})
        resp = urllib.request.urlopen(req, timeout=8)
        code = resp.status
        html = resp.read().decode("utf-8", errors="ignore")
        results.append((code, url, referrers.get(url, "-")))
        for link in fetch_links(url, html):
            if link not in visited:
                referrers[link] = url
                queue.append(link)
    except urllib.error.HTTPError as e:
        results.append((e.code, url, referrers.get(url, "-")))
    except Exception as e:
        results.append(("ERR:" + str(e)[:50], url, referrers.get(url, "-")))

ok  = [(c, u, r) for c, u, r in results if c == 200]
bad = [(c, u, r) for c, u, r in results if c != 200]

print(f"Total pages crawled : {len(results)}")
print(f"OK (200)            : {len(ok)}")
print(f"Issues              : {len(bad)}")
print()

if bad:
    print("=" * 70)
    print("BROKEN / ERRORS")
    print("=" * 70)
    for code, url, ref in sorted(bad, key=lambda x: str(x[0])):
        print(f"  [{code}]  {url}")
        print(f"          linked from: {ref}")
        print()
else:
    print("All links OK!")

print()
print("=" * 70)
print("ALL PAGES (200 OK)")
print("=" * 70)
for _, url, _ in sorted(ok, key=lambda x: x[1]):
    print(f"  {url}")
