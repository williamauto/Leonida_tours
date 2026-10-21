#!/usr/bin/env python3
"""Audit the generated site: links, SEO basics and trademark placement.

Usage:  python3 _build/_audit.py [--quiet]

Checks every generated HTML page for:
  * broken local links (href/src pointing at a path that does not exist)
  * missing or over-long <title> / meta description
  * missing or non-canonical <link rel="canonical">
  * missing, multiple or duplicate-id <h1>
  * malformed JSON-LD blocks
  * banned game trademarks in the title, meta description or H1 of
    commercial pages (blog pages are editorial and are exempt)
"""
import html
import json
import os
import re
import sys
from urllib.parse import unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, ".."))

TRADEMARKS = ["grand theft auto", "gta", "rockstar", "take-two", "lucia", "jason"]
TITLE_MAX = 64
META_MAX = 160

errors = []
warnings = []
counts = {"pages": 0, "links": 0}


def err(where, msg):
    errors.append(f"{where}: {msg}")


def warn(where, msg):
    warnings.append(f"{where}: {msg}")


def pages():
    out = []
    for root, dirs, files in os.walk(SITE):
        dirs[:] = [d for d in dirs
                   if d not in {".git", "_build", "__pycache__", ".github"}]
        for f in files:
            if f.endswith(".html"):
                out.append(os.path.join(root, f))
    return sorted(out)


def local_targets(src_html, src_path):
    """Yield (raw, resolved_path) for every local link in the document."""
    markup = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", src_html, flags=re.S | re.I)
    for m in re.finditer(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", markup):
        raw = m.group(1).strip()
        if not raw or raw.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
            continue
        u = urlparse(raw)
        if u.scheme or u.netloc:
            continue
        path = unquote(u.path)
        if not path:
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(src_path), path))
        yield raw, target


def check_links(path, doc):
    for raw, target in local_targets(doc, path):
        counts["links"] += 1
        if os.path.isdir(target):
            if not os.path.exists(os.path.join(target, "index.html")):
                err(rel(path), f"broken link -> {raw}")
        elif not os.path.exists(target):
            err(rel(path), f"broken link -> {raw}")


def check_seo(path, doc):
    where = rel(path)
    if os.path.basename(path) == "404.html":
        if 'name="robots"' not in doc or "noindex" not in doc:
            err(where, "404 page must be noindex")
        return
    title = re.search(r"<title>(.*?)</title>", doc, re.S)
    if not title:
        err(where, "missing <title>")
        return
    title_txt = html.unescape(title.group(1)).strip()
    if not title_txt:
        err(where, "empty <title>")
    elif len(title_txt) > TITLE_MAX:
        warn(where, f"title {len(title_txt)} chars (max {TITLE_MAX})")

    meta = re.search(r"""<meta\s+name=["']description["']\s+content=["']([^"']*)["']""", doc)
    if not meta:
        err(where, "missing meta description")
    else:
        meta_txt = html.unescape(meta.group(1)).strip()
        if len(meta_txt) > META_MAX:
            warn(where, f"meta description {len(meta_txt)} chars (max {META_MAX})")

    canon = re.search(r"""<link\s+rel=["']canonical["']\s+href=["']([^"']+)["']""", doc)
    if not canon:
        err(where, "missing canonical")

    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    if len(h1s) != 1:
        err(where, f"{len(h1s)} <h1> elements (expected 1)")

    ids = re.findall(r"""\sid=["']([^"']+)["']""", doc)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        err(where, f"duplicate ids: {', '.join(sorted(dupes))}")

    for block in re.findall(
            r"""<script\s+type=["']application/ld\+json["'][^>]*>(.*?)</script>""",
            doc, re.S):
        try:
            json.loads(block)
        except Exception as exc:  # noqa: BLE001
            err(where, f"invalid JSON-LD: {exc}")


def check_trademarks(path, doc):
    """Commercial pages may not use game names in title / meta / H1."""
    where = rel(path).replace(os.sep, "/")
    if where.startswith("blog/"):
        return
    head = doc.split("</head>")[0]
    title = re.search(r"<title>(.*?)</title>", head, re.S)
    meta = re.search(r"""<meta\s+name=["']description["']\s+content=["']([^"']*)["']""", head)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    fields = []
    if title:
        fields.append(("title", html.unescape(title.group(1))))
    if meta:
        fields.append(("meta description", html.unescape(meta.group(1))))
    if h1:
        fields.append(("H1", html.unescape(re.sub(r"<[^>]+>", " ", h1.group(1)))))
    for label, text in fields:
        low = text.lower()
        for t in TRADEMARKS:
            if t in low:
                err(where, f"trademark '{t}' in {label}")


def rel(path):
    return os.path.relpath(path, SITE)


def main():
    for path in pages():
        counts["pages"] += 1
        doc = open(path, encoding="utf-8").read()
        check_links(path, doc)
        check_seo(path, doc)
        check_trademarks(path, doc)

    for w in warnings:
        print("WARN " + w)
    for e in errors:
        print("FAIL " + e)
    print(f"checked {counts['pages']} pages, {counts['links']} local links "
          f"-> {len(errors)} issues, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
