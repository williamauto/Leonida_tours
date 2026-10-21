#!/usr/bin/env python3
"""Render the content pages of the Leonida Tours site.

Builds, from the JSON/Python content modules in _build/content/:
  /blog/                     article index
  /blog/<slug>/              12 articles
  /locations/                field guide index
  /locations/<slug>/         15 location pages
  /map/                      interactive map of every location
  /<slug>/                   8 trust and policy pages
  /feed.xml                  RSS 2.0 of the blog
  /llms-full.txt             full text of everything, for AI crawlers

build.py populates CTX before calling build_all(), so this module never
imports build.py and there is no circular import.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONTENT = os.path.join(HERE, "content")

CTX = {}


# ---------------------------------------------------------------- content loading
def _load(name, path):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_posts():
    posts = []
    for fn in sorted(os.listdir(CONTENT)):
        if re.match(r"^posts_.*\.py$", fn):
            posts += _load(fn[:-3], os.path.join(CONTENT, fn)).POSTS
    posts.sort(key=lambda r: r["date"], reverse=True)
    return posts


def load_statics():
    pages = []
    for fn in sorted(os.listdir(CONTENT)):
        if re.match(r"^static_.*\.py$", fn):
            pages += _load(fn[:-3], os.path.join(CONTENT, fn)).STATIC
    return pages


def load_locations():
    with open(os.path.join(CONTENT, "locations.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- helpers
def esc(s):
    return CTX["esc"](s)


def money(n):
    return CTX["money"](n)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", str(s))


def word_count(blocks):
    n = 0
    for b in blocks:
        for k, v in b.items():
            if k == "id":
                continue
            if isinstance(v, str):
                n += len(v.split())
            elif isinstance(v, list):
                n += sum(len(str(x).split()) for x in v)
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    if isinstance(vv, list):
                        n += sum(len(str(x).split()) for x in vv)
                    else:
                        n += len(str(vv).split())
    return n


def reading_time(blocks):
    return max(2, round(word_count(blocks) / 200))


def map_link(lat, lng):
    return f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")
    return s or "section"


def guard(page, fields, graph=None):
    """Trademark guard: commercial pages may not use protected game marks in
    their title, meta description, H1 or entity name. Body copy may name the
    game nominatively and with attribution; only the promotional framing is
    restricted. Blog articles are exempt (the game is their subject)."""
    CTX["guard"](page, fields, graph)


# ---------------------------------------------------------------- block rendering
def render_blocks(blocks, p):
    out = []
    for b in blocks:
        anchor = b.get("id")
        for k, v in b.items():
            if k == "id":
                continue
            if k in ("h2", "h3"):
                hid = anchor or slugify(v)
                out.append(f'<{k} id="{esc(hid)}">{esc(v)}</{k}>')
            elif k == "p":
                out.append("<p>" + " ".join(v) + "</p>")
            elif k in ("ul", "ol"):
                tag = "ul" if k == "ul" else "ol"
                items = "".join(f"<li>{x}</li>" for x in v)
                out.append(f"<{tag}>{items}</{tag}>")
            elif k == "table":
                head = "".join(f"<th>{esc(c)}</th>" for c in v["head"])
                rows = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                               for r in v["rows"])
                out.append('<div class="tbl"><table><thead><tr>' + head +
                           "</tr></thead><tbody>" + rows + "</tbody></table></div>")
            elif k == "note":
                out.append(f'<div class="note"><h3>{esc(v["title"])}</h3><p>{v["text"]}</p></div>')
            elif k == "quote":
                cite = f"<cite>{esc(v['cite'])}</cite>" if v.get("cite") else ""
                out.append(f'<blockquote class="quote"><p>{v["text"]}</p>{cite}</blockquote>')
            elif k == "image":
                dims = CTX["img_attrs"](v["img"]) if v["img"] in CTX["SIZE"] else ""
                cap = f'<figcaption>{esc(v["caption"])}</figcaption>' if v.get("caption") else ""
                out.append(f'<figure><img src="{p}img/{v["img"]}.jpg" alt="{esc(v.get("alt", ""))}" '
                           f'loading="lazy" decoding="async" {dims}>{cap}</figure>')
    return "\n".join(out)


def toc_html(blocks):
    items = []
    for b in blocks:
        if "h2" not in b or b["h2"] == "Frequently asked questions":
            continue
        items.append((b["h2"], b.get("id") or slugify(b["h2"])))
    if len(items) < 3:
        return ""
    lis = "".join(f'<li><a href="#{esc(anchor)}">{esc(text)}</a></li>' for text, anchor in items)
    return ('<nav class="toc" aria-label="On this page"><h2>On this page</h2><ol>' + lis + "</ol></nav>")


# ---------------------------------------------------------------- shell
def nav(p, current=""):
    def a(href, label):
        cur = ' aria-current="page"' if href == current else ""
        return f'<a href="{p}{href}"{cur}>{label}</a>'
    return (
        '<header class="nav article-nav"><div class="wrap">'
        f'<a class="logo" href="{p}"><i>{CTX["PIN"]}</i>LEONIDA <span class="grad">TOURS</span></a>'
        '<nav class="links" aria-label="Sections">'
        + a("blog/", "Blog") + a("locations/", "Locations") + a("map/", "Map") + a("about/", "About")
        + '</nav>'
        f'<a class="btn btn-primary btn-sm" href="{p}#preregister">Reserve free</a>'
        "</div></header>"
    )


def footer(p):
    links = []
    for href, label in [("blog/", "Blog"), ("locations/", "Locations"), ("map/", "Map"),
                        ("about/", "About us"), ("editorial-policy/", "Editorial policy"),
                        ("contact/", "Contact"), ("meeting-point/", "Meeting point"),
                        ("cancellation-policy/", "Cancellation policy"),
                        ("insurance-and-licensing/", "Insurance & licensing"),
                        ("privacy/", "Privacy"), ("terms/", "Terms")]:
        links.append(f'<li><a href="{p}{href}">{label}</a></li>')
    tours = "".join(f'<li><a href="{p}tours/{CTX["SEO"][k]["slug"]}/">{esc(CTX["TOURS"][k]["title"])}</a></li>'
                    for k in CTX["ORDER"])
    return (
        '<footer><div class="wrap">'
        f'<nav aria-label="Tours"><ul>{tours}</ul></nav>'
        f'<nav aria-label="Site"><ul>{"".join(links)}</ul></nav>'
        f"<p>© 2026 {CTX['BRAND']} · <a href=\"mailto:{CTX['EMAIL']}\">{CTX['EMAIL']}</a> · Ocean Drive, Miami Beach, FL</p>"
        f'<p class="legal">{CTX["DISCLAIMER"]}</p>'
        "</div></footer>"
    )


def page_head(title, desc, page_url, og_img, og_alt, p, extra="", og_type="website", article=None):
    styles = (f'<link rel="stylesheet" href="{p}assets/tour.css">\n'
              f'<link rel="stylesheet" href="{p}assets/content.css">\n')
    return CTX["head_common"](title, desc, page_url, og_img, og_alt, p, styles + extra, og_type, article)


def write_html(path, html):
    d = os.path.join(ROOT, path)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(html)


# ---------------------------------------------------------------- schema helpers
def breadcrumb(page, trail):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": CTX["url"]()}]
    for i, (name, url) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": name, "item": url})
    return {"@type": "BreadcrumbList", "@id": page + "#breadcrumb", "itemListElement": items}


def faq_schema(items, page, speakable=False):
    d = {"@type": "FAQPage", "@id": page + "#faq",
         "mainEntity": [{"@type": "Question", "name": q,
                         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}
    if speakable:
        d["speakable"] = {"@type": "SpeakableSpecification",
                          "cssSelector": [".prose h2", ".prose p", ".faq summary", ".faq p"]}
    return d


def web_page(page, name, desc, extra=None):
    d = {"@type": "WebPage", "@id": page + "#webpage", "url": page, "name": name, "description": desc,
         "isPartOf": {"@id": CTX["SITE_ID"]}, "inLanguage": "en-US",
         "dateModified": CTX["TODAY"], "breadcrumb": {"@id": page + "#breadcrumb"}}
    if extra:
        d.update(extra)
    return d


# ---------------------------------------------------------------- shared CTA
def CTA(p):
    return ('<section><div class="wrap cta"><span class="eyebrow">Free reservation &middot; nothing to pay today</span>'
            '<h2 style="margin:0">Come and see it. <span class="grad">Ride first.</span></h2>'
            '<p class="lede">Tell us your date and group size and we will confirm your spot before public booking opens, plus 20% off your first tour.</p>'
            f'<a class="btn btn-primary" href="{p}#preregister">Reserve free</a></div></section>')


# ---------------------------------------------------------------- blog
def build_blog_index(posts):
    p = "../"
    page = CTX["url"]("blog/")
    cards = []
    for r in posts:
        img = r["img"]
        cards.append(
            f'<a class="card" href="{p}blog/{r["slug"]}/">'
            f'<img src="{p}img/{img}.jpg" alt="{esc(r["img_alt"])}" loading="lazy" decoding="async" {CTX["img_attrs"](img)}>'
            f'<div class="cb"><span class="ct">{esc(r["kicker"])}</span><h3>{esc(r["title"])}</h3>'
            f'<p>{esc(r["excerpt"])}</p>'
            f'<span class="cm">{r["date"]} · {reading_time(r["body"])} min read</span></div></a>'
        )
    cats = sorted({r["cat"] for r in posts})
    tagrow = "".join(f'<span class="tag">{esc(c)}</span>' for c in cats)
    featured = posts[0] if posts else None
    feat_html = ""
    if featured:
        feat_html = (
            '<section><div class="wrap"><span class="eyebrow">Latest</span>'
            f'<h2 style="margin:14px 0 18px">{esc(featured["title"])}</h2>'
            f'<p class="lede" style="margin-bottom:20px">{esc(featured["excerpt"])}</p>'
            f'<a class="btn btn-primary" href="{p}blog/{featured["slug"]}/">Read the guide</a></div></section>'
        )
    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"],
         "inLanguage": "en-US", "publisher": {"@id": CTX["ORG_ID"]}},
        web_page(page, "Blog", "Guides to the real Miami, the Everglades and the Florida Keys: where to go, what it costs and how to do it well.",
                 {"mainEntity": {"@id": page + "#list"}}),
        breadcrumb(page, [("Blog", page)]),
        {"@type": "CollectionPage", "@id": page + "#list", "name": "Leonida Tours blog",
         "url": page, "numberOfItems": len(posts),
         "itemListElement": [{"@type": "ListItem", "position": i + 1,
                              "item": {"@type": "Article", "name": r["title"], "url": CTX["url"](f'blog/{r["slug"]}/'),
                                       "datePublished": r["date"], "image": CTX["url"](f'img/{r["img"]}.jpg')}}
                             for i, r in enumerate(posts)]},
    ]
    extra = CTX["ld"](graph)
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(f"Blog & Guides | {CTX['BRAND']}",
                     "Practical guides to Miami, the Everglades and the Florida Keys: real locations, honest itineraries, current prices and how to get the most from a few days.",
                     page, CTX["url"]("assets/og-home.jpg"), "Leonida Tours blog: guides to Miami, the Everglades and the Florida Keys", p, extra) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "blog/") +
           f'<main><div class="wrap ahead"><div class="kicker">Journal<span class="dot"></span>Guides<span class="dot"></span>Updated {CTX["TODAY"]}</div>'
           "<h1>The Leonida Tours blog</h1>"
           '<p class="lede">Everything we know about seeing South Florida properly, written by the people who run the tours: where to go, what it really costs, when to visit and how to get the most out of a short trip.</p>'
           f'<div class="tag-row">{tagrow}</div></div></main>'
           + feat_html +
           f'<section><div class="wrap"><h2>All {len(posts)} guides</h2><div class="card-grid">{"".join(cards)}</div></div></section>'
           + CTA(p) +
           "</main>" + footer(p) + "</body>\n</html>\n")
    write_html("blog", out)


def build_post(r, posts):
    slug = r["slug"]
    p = "../../"
    page = CTX["url"](f"blog/{slug}/")
    img = r["img"]
    og = CTX["url"](f"assets/og/blog-{slug}.jpg")
    byslug = {x["slug"]: x for x in posts}
    relcards = []
    for rs in r.get("related", []):
        x = byslug.get(rs)
        if not x:
            continue
        relcards.append(
            f'<a class="card" href="{p}blog/{x["slug"]}/">'
            f'<img src="{p}img/{x["img"]}.jpg" alt="{esc(x["img_alt"])}" loading="lazy" decoding="async" {CTX["img_attrs"](x["img"])}>'
            f'<div class="cb"><span class="ct">{esc(x["kicker"])}</span><h3>{esc(x["title"])}</h3>'
            f'<span class="cm">{x["date"]} · {reading_time(x["body"])} min read</span></div></a>'
        )
    idx = posts.index(r)
    newer = posts[idx - 1] if idx > 0 else None
    older = posts[idx + 1] if idx + 1 < len(posts) else None
    pager = ""
    if newer or older:
        left = (f'<a href="{p}blog/{newer["slug"]}/"><span>Newer</span>{esc(newer["title"])}</a>'
                if newer else "<span></span>")
        right = (f'<a href="{p}blog/{older["slug"]}/"><span>Older</span>{esc(older["title"])}</a>'
                 if older else "<span></span>")
        pager = f'<div class="pager">{left}{right}</div>'

    faqs = r["faq"]
    faq_html = "".join(f"<details{' open' if i == 0 else ''}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
                        for i, (q, a) in enumerate(faqs))

    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, r["title"], r["meta"],
                 {"primaryImageOfPage": {"@type": "ImageObject", "url": CTX["url"](f"img/{img}.jpg")},
                  "speakable": {"@type": "SpeakableSpecification",
                                "cssSelector": [".ahead h1", ".ahead .lede", ".prose h2", ".prose p"]},
                  "mainEntity": {"@id": page + "#article"}}),
        breadcrumb(page, [("Blog", CTX["url"]("blog/")), (r["title"], page)]),
        {"@type": "Article", "@id": page + "#article", "headline": r["title"], "name": r["title"],
         "description": r["meta"], "url": page,
         "image": [CTX["url"](f"img/{img}.jpg"), og],
         "datePublished": r["date"], "dateModified": r["date"],
         "author": {"@id": CTX["ORG_ID"]}, "publisher": {"@id": CTX["ORG_ID"]},
         "mainEntityOfPage": {"@type": "WebPage", "@id": page},
         "articleSection": r["cat"], "inLanguage": "en-US", "isAccessibleForFree": True,
         "wordCount": word_count(r["body"]),
         "about": {"@type": "Place", "name": "South Florida, Florida"},
         "isPartOf": {"@id": CTX["url"]("blog/")}},
        faq_schema(faqs, page, speakable=True),
    ]
    extra = CTX["ld"](graph)
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(r["title"], r["meta"], page, og, r["img_alt"], p, extra,
                     og_type="article",
                     article={"published": r["date"], "modified": r["date"], "section": r["cat"]}) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "blog/") +
           '<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><ol>'
           f'<li><a href="{p}">Home</a></li><li><a href="{p}blog/">Blog</a></li>'
           f'<li aria-current="page">{esc(r["cat"])}</li></ol></nav></div>'
           f'<div class="wrap ahead"><div class="kicker"><span>{esc(r["kicker"])}</span><span class="dot"></span>'
           f'<span>{esc(r["cat"])}</span></div><h1>{esc(r["title"])}</h1>'
           f'<p class="lede">{esc(r["excerpt"])}</p>'
           f'<div class="byline"><span>Published <b>{r["date"]}</b></span>'
           f'<span>Reading time <b>{reading_time(r["body"])} min</b></span>'
           f'<span>Written by <b>{CTX["BRAND"]}</b></span></div>'
           f'<div class="ph"><img src="{p}img/{img}.jpg" alt="{esc(r["img_alt"])}" fetchpriority="high" {CTX["img_attrs"](img)}></div>'
           f'</div>'
           f'<div class="wrap">{toc_html(r["body"])}</div>'
           f'<section><div class="wrap prose">{render_blocks(r["body"], p)}</div></section>'
           f'<section class="faq"><div class="wrap"><h2>Frequently asked questions</h2>{faq_html}</div></section>'
           + CTA(p) +
           f'<section><div class="wrap"><h2>More guides</h2><div class="card-grid">{"".join(relcards)}</div></div></section>'
           f'<div class="wrap">{pager}</div>'
           f'<div class="wrap"><div class="disc"><strong>Editorial note</strong><p>{CTX["DISCLAIMER"]}</p></div></div>'
           "</main>" + footer(p) + "</body>\n</html>\n")
    write_html(f"blog/{slug}", out)


# ---------------------------------------------------------------- locations
def confidence_class(c):
    c = (c or "").lower()
    if "official" in c:
        return "official"
    if "strong" in c:
        return "strong"
    return ""


def build_locations_index(locs):
    p = "../"
    page = CTX["url"]("locations/")
    rows = []
    cards = []
    for l in locs["locations"]:
        badge = confidence_class(l["confidence"])
        rows.append(
            f'<tr><td><a href="{p}locations/{l["slug"]}/">{esc(l["name"])}</a></td>'
            f'<td>{esc(l["game_name"])}</td><td>{esc(l["area"])}</td>'
            f'<td>{esc(l["addr"])}</td>'
            f'<td><span class="badge {badge}">{esc(l["confidence"])}</span></td></tr>'
        )
        cards.append(
            f'<a class="card" href="{p}locations/{l["slug"]}/">'
            f'<img src="{p}img/{l["img"]}.jpg" alt="{esc(l["img_alt"])}" loading="lazy" decoding="async" {CTX["img_attrs"](l["img"])}>'
            f'<div class="cb"><span class="ct">{esc(l["area"])}</span><h3>{esc(l["name"])}</h3>'
            f'<p>{esc(l["addr"])}</p>'
            f'<span class="badge {badge}">{esc(l["confidence"])}</span></div></a>'
        )
    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, "Real locations field guide",
                 "Fifteen real places in Miami, the Everglades and the Florida Keys matched to their in-game counterparts, with addresses, coordinates and a confidence rating for each.",
                 {"mainEntity": {"@id": page + "#list"}}),
        breadcrumb(page, [("Locations", page)]),
        {"@type": "CollectionPage", "@id": page + "#list", "name": "Leonida Tours real locations field guide",
         "url": page, "numberOfItems": len(locs["locations"]),
         "itemListElement": [{"@type": "ListItem", "position": i + 1,
                              "item": {"@type": "TouristAttraction", "name": l["name"],
                                       "url": CTX["url"](f'locations/{l["slug"]}/'),
                                       "address": l["addr"],
                                       "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lng"]}}}
                             for i, l in enumerate(locs["locations"])]},
    ]
    guard("locations index", [("title", f"Real Locations Field Guide | {CTX['BRAND']}"),
                              ("h1", "The real places behind the game"),
                              ("meta", "Fifteen real Miami, Everglades and Florida Keys places matched to their in-game counterparts, with addresses, coordinates and a confidence rating.")],
          graph)
    extra = CTX["ld"](graph)
    stat = (f'<div class="stat"><b>{len(locs["locations"])}</b><span>real places mapped and verified</span></div>'
            '<div class="stat"><b>4</b><span>confidence ratings, from official to community</span></div>'
            '<div class="stat"><b>15</b><span>coordinates published</span></div>'
            '<div class="stat"><b>0</b><span>game assets used</span></div>')
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(f"Real Locations Field Guide | {CTX['BRAND']}",
                     "Fifteen real Miami, Everglades and Florida Keys places matched to their in-game counterparts, with addresses, coordinates and a confidence rating.",
                     page, CTX["url"]("assets/og-home.jpg"),
                     "Leonida Tours real locations field guide: Miami, Everglades and Florida Keys", p, extra) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "locations/") +
           '<main><div class="wrap ahead"><div class="kicker">Field guide<span class="dot"></span>15 places</div>'
           "<h1>The real places behind the game</h1>"
           f'<p class="lede">{esc(locs["intro"])}</p>'
           f'<div class="stat-row">{stat}</div>'
           '<div class="tag-row"><span class="tag"><a href="../map/" style="color:inherit;text-decoration:none">Open the map</a></span>'
           '<span class="tag"><a href="../blog/gta-6-locations-in-real-life/" style="color:inherit;text-decoration:none">Read the full guide</a></span></div>'
           '</div>'
           '<section><div class="wrap"><h2>Every location</h2>'
           '<div class="table-scroll"><table><thead><tr><th>Real place</th><th>In the game</th><th>District</th><th>Address</th><th>Confidence</th></tr></thead>'
           f'<tbody>{"".join(rows)}</tbody></table></div></div></section>'
           f'<section><div class="wrap"><h2>Browse by place</h2><div class="card-grid">{"".join(cards)}</div></div></section>'
           + CTA(p) +
           "</main>" + footer(p) + "</body>\n</html>\n")
    write_html("locations", out)


def build_location(l, all_locs):
    slug = l["slug"]
    p = "../../"
    page = CTX["url"](f"locations/{slug}/")
    img = l["img"]
    og = CTX["url"](f"assets/og/loc-{slug}.jpg")
    faqs = l["faq"]
    faq_html = "".join(f"<details{' open' if i == 0 else ''}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
                        for i, (q, a) in enumerate(faqs))
    tour = CTX["TOURS"].get(l.get("tour"))
    tour_link = ""
    if tour:
        tslug = CTX["SEO"][l["tour"]]["slug"]
        tour_link = f'<a class="btn btn-primary" href="{p}tours/{tslug}/">See this on the tour</a>'
    same = [x for x in all_locs["locations"] if x["area"] == l["area"] and x["slug"] != slug][:3]
    relcards = "".join(
        f'<a class="card" href="{p}locations/{x["slug"]}/">'
        f'<img src="{p}img/{x["img"]}.jpg" alt="{esc(x["img_alt"])}" loading="lazy" decoding="async" {CTX["img_attrs"](x["img"])}>'
        f'<div class="cb"><span class="ct">{esc(x["area"])}</span><h3>{esc(x["name"])}</h3>'
        f'<p>{esc(x["addr"])}</p></div></a>' for x in same)

    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, l["name"], l["meta"],
                 {"primaryImageOfPage": {"@type": "ImageObject", "url": CTX["url"](f"img/{img}.jpg")},
                  "speakable": {"@type": "SpeakableSpecification",
                                "cssSelector": [".ahead h1", ".ahead .lede", ".facts dd", ".prose h2", ".prose p"]},
                  "mainEntity": {"@id": page + "#place"}}),
        breadcrumb(page, [("Locations", CTX["url"]("locations/")), (l["name"], page)]),
        {"@type": "TouristAttraction", "@id": page + "#place", "name": l["name"], "description": l["lede"],
         "url": page, "image": [CTX["url"](f"img/{img}.jpg"), og],
         "address": {"@type": "PostalAddress", "streetAddress": l["addr"], "addressLocality": "Miami Beach",
                     "addressRegion": "FL", "addressCountry": "US"},
         "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lng"]},
         "hasMap": map_link(l["lat"], l["lng"]),
         "publicAccess": True, "isAccessibleForFree": True,
         "touristType": "Landmark or natural feature",
         "provider": {"@id": CTX["ORG_ID"]},
         "isPartOf": {"@id": CTX["url"]("locations/")}},
        faq_schema(faqs, page, speakable=True),
    ]
    guard(f"location {slug}", [("title", l["title"]), ("h1", l["name"]), ("meta", l["meta"])], graph)
    extra = CTX["ld"](graph)
    facts = (
        '<div class="facts"><h2>At a glance</h2><dl>'
        f'<div><dt>Address</dt><dd>{esc(l["addr"])}</dd></div>'
        f'<div><dt>Coordinates</dt><dd class="coord">{l["lat"]}, {l["lng"]}</dd></div>'
        f'<div><dt>District</dt><dd>{esc(l["area"])}</dd></div>'
        f'<div><dt>Confidence</dt><dd>{esc(l["confidence"])}</dd></div>'
        f'<div><dt>Where it is seen</dt><dd>{esc(l["seen"])}</dd></div>'
        f'<div><dt>Map</dt><dd><a href="{map_link(l["lat"], l["lng"])}" rel="nofollow noopener">Open in Google Maps</a></dd></div>'
        "</dl></div>"
    )
    note = f'<div class="note"><h3>How confident are we?</h3><p>{esc(l["confidence_note"])}</p></div>'
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(l["title"], l["meta"], page, og, l["img_alt"], p, extra) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "locations/") +
           '<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><ol>'
           f'<li><a href="{p}">Home</a></li><li><a href="{p}locations/">Locations</a></li>'
           f'<li aria-current="page">{esc(l["name"])}</li></ol></nav></div>'
           f'<div class="wrap ahead"><div class="kicker"><span>Real location</span><span class="dot"></span>'
           f'<span>{esc(l["area"])}</span></div><h1>{esc(l["name"])}</h1>'
           f'<p class="lede">{esc(l["lede"])}</p>'
           f'<div class="byline"><span>In the game as <b>{esc(l["game_name"])}</b></span>'
           f'<span>Confidence <b>{esc(l["confidence"])}</b></span></div>'
           f'<div class="ph"><img src="{p}img/{img}.jpg" alt="{esc(l["img_alt"])}" fetchpriority="high" {CTX["img_attrs"](img)}></div>'
           f'</div>'
           f'<div class="wrap">{facts}</div>'
           f'<section><div class="wrap prose">{note}{render_blocks(l["body"], p)}</div></section>'
           f'<section class="faq"><div class="wrap"><h2>Frequently asked questions</h2>{faq_html}</div></section>'
           '<section><div class="wrap cta"><span class="eyebrow">Stand here for real</span>'
           '<h2 style="margin:0">See it on a Leonida Tours route.</h2>'
           f'<p class="lede">{esc(l["name"])} is one of the stops we drive past every day. Join a small group and see it in person, with a local guide who knows what to look for.</p>'
           f'{tour_link}</div></section>'
           + (f'<section><div class="wrap"><h2>Nearby on the map</h2><div class="card-grid">{relcards}</div></div></section>'
              if relcards else "") +
           '<div class="wrap"><div class="disc"><strong>Editorial note</strong><p>' + CTX["DISCLAIMER"] + "</p></div></div>"
           "</main>" + footer(p) + "</body>\n</html>\n")
    write_html(f"locations/{slug}", out)


# ---------------------------------------------------------------- trust pages
STATIC_SCHEMA = {
    "about": "AboutPage",
    "editorial-policy": "WebPage",
    "contact": "ContactPage",
    "meeting-point": "WebPage",
    "cancellation-policy": "WebPage",
    "insurance-and-licensing": "WebPage",
    "privacy": "WebPage",
    "terms": "WebPage",
}


def build_static(s, statics):
    slug = s["slug"]
    p = "../"
    page = CTX["url"](f"{slug}/")
    img = s["img"]
    og = CTX["url"](f"assets/og/page-{slug}.jpg")
    faqs = s.get("faq", [])
    faq_html = "".join(f"<details{' open' if i == 0 else ''}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>"
                        for i, (q, a) in enumerate(faqs))
    byslug = {x["slug"]: x for x in statics}
    relcards = "".join(
        f'<a class="card" href="{p}{rs}/">'
        f'<div class="cb"><span class="ct">{esc(byslug[rs]["kicker"])}</span>'
        f'<h3>{esc(byslug[rs]["title"])}</h3><p>{esc(byslug[rs]["excerpt"])}</p></div></a>'
        for rs in s.get("related", []) if rs in byslug)

    extra_schema = {}
    if slug == "contact":
        extra_schema = {"mainEntity": {
            "@type": "Organization", "name": CTX["BRAND"], "email": CTX["EMAIL"],
            "telephone": "+1-305-555-0148",
            "address": {"@type": "PostalAddress", "streetAddress": "1200 Ocean Drive",
                        "addressLocality": "Miami Beach", "addressRegion": "FL", "addressCountry": "US"},
            "contactPoint": {"@type": "ContactPoint", "contactType": "customer service",
                             "telephone": "+1-305-555-0148", "email": CTX["EMAIL"],
                             "availableLanguage": ["en", "es"]}}}
    if slug == "about":
        extra_schema = {"mainEntity": {"@id": CTX["ORG_ID"]}}

    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, s["title"], s["meta"],
                 {"primaryImageOfPage": {"@type": "ImageObject", "url": CTX["url"](f"img/{img}.jpg")},
                  "speakable": {"@type": "SpeakableSpecification",
                                "cssSelector": [".ahead h1", ".ahead .lede", ".prose h2", ".prose p"]},
                  **extra_schema}),
        breadcrumb(page, [(s["title"], page)]),
        {"@type": STATIC_SCHEMA.get(slug, "WebPage"), "@id": page + "#page", "name": s["title"],
         "description": s["meta"], "url": page, "image": CTX["url"](f"img/{img}.jpg"),
         "datePublished": s["date"], "dateModified": CTX["TODAY"],
         "publisher": {"@id": CTX["ORG_ID"]}, "inLanguage": "en-US",
         "isPartOf": {"@id": CTX["SITE_ID"]}},
    ]
    if faqs:
        graph.append(faq_schema(faqs, page, speakable=True))
    guard(f"page {slug}", [("title", s["title"]), ("h1", s["title"]), ("meta", s["meta"])], graph)
    extra = CTX["ld"](graph)
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(s["title"], s["meta"], page, og, s["img_alt"], p, extra) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p) +
           '<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><ol>'
           f'<li><a href="{p}">Home</a></li><li aria-current="page">{esc(s["kicker"])}</li></ol></nav></div>'
           f'<div class="wrap ahead"><div class="kicker"><span>{esc(s["kicker"])}</span>'
           f'<span class="dot"></span><span>Last updated {s["date"]}</span></div><h1>{esc(s["title"])}</h1>'
           f'<p class="lede">{esc(s["excerpt"])}</p></div>'
           f'<section><div class="wrap prose">{render_blocks(s["body"], p)}</div></section>'
           + (f'<section class="faq"><div class="wrap"><h2>Frequently asked questions</h2>{faq_html}</div></section>'
              if faqs else "") +
           (f'<section><div class="wrap"><h2>Related pages</h2><div class="card-grid">{relcards}</div></div></section>'
              if relcards else "") +
           "</main>" + footer(p) + "</body>\n</html>\n")
    write_html(slug, out)


# ---------------------------------------------------------------- map
def build_map(locs):
    p = "../"
    page = CTX["url"]("map/")
    items = locs["locations"]
    markers = [{
        "n": l["name"], "g": l["game_name"], "a": l["area"], "addr": l["addr"],
        "lat": l["lat"], "lng": l["lng"], "c": l["confidence"],
        "slug": l["slug"], "url": CTX["url"](f'locations/{l["slug"]}/'),
        "gm": map_link(l["lat"], l["lng"]),
    } for l in items]
    lst = "".join(
        f'<a href="{p}locations/{l["slug"]}/"><em>{esc(l["area"])}</em><strong>{esc(l["name"])}</strong>'
        f'<span>{esc(l["addr"])}</span></a>' for l in items)
    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, "Map of the real locations",
                 "An interactive map of every real South Florida place we have matched to its in-game counterpart, with addresses, coordinates and a link to each location page.",
                 {"mainEntity": {"@id": page + "#list"}}),
        breadcrumb(page, [("Map", page)]),
        {"@type": "ItemList", "@id": page + "#list", "name": "Real locations map",
         "numberOfItems": len(items),
         "itemListElement": [{"@type": "ListItem", "position": i + 1,
                              "item": {"@type": "TouristAttraction", "name": l["name"],
                                       "url": CTX["url"](f'locations/{l["slug"]}/'),
                                       "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lng"]}}}
                             for i, l in enumerate(items)]},
    ]
    guard("map", [("title", f"Map of Real Locations | {CTX['BRAND']}"),
                  ("h1", "The real places, on a map"),
                  ("meta", "An interactive map of every real South Florida place matched to its in-game counterpart, with addresses, coordinates and a page for each one.")],
          graph)
    extra = CTX["ld"](graph)
    script = ('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" defer></script>\n'
              '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">\n')
    data = json.dumps(markers, ensure_ascii=False).replace("</", "<\\/")
    js = """
<script>window.__LOCS=__DATA__;</script>
<script>
document.addEventListener('DOMContentLoaded', function(){
  if (!window.L || !document.getElementById('map')) return;
  var m = L.map('map', {scrollWheelZoom:false}).setView([25.79,-80.20], 10);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    {attribution:'&copy; OpenStreetMap &copy; CARTO', maxZoom:19}).addTo(m);
  var icon = L.divIcon({className:'lm', html:'<span></span>', iconSize:[26,26], iconAnchor:[13,26], popupAnchor:[0,-24]});
  window.__LOCS.forEach(function(o){
    var mk = L.marker([o.lat, o.lng], {icon:icon}).addTo(m);
    mk.bindPopup('<strong>'+o.n+'</strong><br>'+o.addr+'<br><em>'+o.c+'</em><br>'
      + '<a href="'+o.url+'">Read the page</a> &middot; <a href="'+o.gm+'" rel="nofollow noopener">Google Maps</a>');
  });
  setTimeout(function(){ m.invalidateSize(); }, 300);
});
</script>
"""
    js = js.replace("__DATA__", data)
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(f"Map of Real Locations | {CTX['BRAND']}",
                     "An interactive map of every real South Florida place matched to its in-game counterpart, with addresses, coordinates and a page for each one.",
                     page, CTX["url"]("assets/og-home.jpg"),
                     "Interactive map of real Miami, Everglades and Florida Keys locations", p, extra) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "map/") +
           '<main><div class="wrap ahead"><div class="kicker">Field guide<span class="dot"></span>'
           f'{len(items)} mapped places</div><h1>The real places, on a map</h1>'
           '<p class="lede">Every location on this map is a real, publicly accessible place in South Florida, with coordinates you can check. Click a pin, or pick a place from the list.</p></div>'
           f'<section><div class="wrap map-grid"><div id="map" role="img" aria-label="Map of {len(items)} real South Florida locations"></div>'
           f'<div class="map-list">{lst}</div></div></section>'
           '<section><div class="wrap"><h2>How to read this map</h2>'
           '<div class="prose"><p>The map covers Miami Beach and Downtown, the causeway, Little Havana and Wynwood, the Everglades and the Florida Keys. '
           'Each pin links to a page with the full address, the coordinates, how confident we are about the match and which tour stops there.</p>'
           '<p>Some locations are close together because the real city is compact: Ocean Drive to Brickell is about four miles. The Everglades and the Keys are the two outliers, and both are worth a full day.</p></div></div></section>'
           + CTA(p) +
           "</main>" + footer(p) + script + js + "</body>\n</html>\n")
    write_html("map", out)


# ---------------------------------------------------------------- feed + llms-full
def build_feed(posts):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    def rfc(d):
        y, m, dd = d.split("-")
        return f"{dd} {months[int(m) - 1]} {y}"
    items = []
    for r in posts:
        url = CTX["url"](f'blog/{r["slug"]}/')
        img = r["img"]
        items.append(
            "<item><title>" + esc(r["title"]) + "</title>"
            "<link>" + url + "</link>"
            f'<guid isPermaLink="true">{url}</guid>'
            f"<pubDate>{rfc(r['date'])}</pubDate>"
            "<description>" + esc(r["excerpt"]) + "</description>"
            "<category>" + esc(r["cat"]) + "</category>"
            f'<enclosure url="{CTX["url"]("img/" + img + ".jpg")}" type="image/jpeg" length="0">'
            "</item>")
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            "<channel>"
            f"<title>{esc(CTX['BRAND'])} blog</title>"
            f"<link>{CTX['url']('blog/')}</link>"
            f'<atom:link href="{CTX["url"]("feed.xml")}" rel="self" type="application/rss+xml"/>'
            "<description>Guides to the real Miami, the Everglades and the Florida Keys from the people who run the tours.</description>"
            "<language>en-us</language>"
            f"<lastBuildDate>{rfc(CTX['TODAY'])}</lastBuildDate>"
            "<generator>Leonida Tours static site generator</generator>"
            + "".join(items) + "</channel></rss>\n")
    with open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as fh:
        fh.write(feed)


def _flat(blocks, out):
    for b in blocks:
        for k, v in b.items():
            if k in ("p", "ul", "ol"):
                for item in v:
                    out.append(strip_tags(item))
            elif k == "h2":
                out.append("")
                out.append("## " + v)
            elif k == "h3":
                out.append("### " + v)
            elif k == "table":
                out.append("| " + " | ".join(v["head"]) + " |")
                out.append("|" + "|".join(["---"] * len(v["head"])) + "|")
                for row in v["rows"]:
                    out.append("| " + " | ".join(strip_tags(c) for c in row) + " |")
            elif k == "note":
                out.append(f"> {v['title']}: {strip_tags(v['text'])}")
            elif k == "quote":
                out.append(f"> {strip_tags(v['text'])}" + (f" - {v['cite']}" if v.get("cite") else ""))


def build_llms_full(posts, locs, statics):
    L = []
    L.append(f"# {CTX['BRAND']}: full site text for AI assistants")
    L.append("")
    L.append("> Independent South Florida tour company running small-group and private tours to the real Miami, "
             "Everglades and Florida Keys places. Reservations are free with nothing to pay upfront. "
             "Not affiliated with, endorsed by or sponsored by Rockstar Games or Take-Two Interactive. "
             "All game names are used only to identify real-world locations.")
    L.append("")
    L.append(f"Site: {CTX['url']()}  |  Email: {CTX['EMAIL']}  |  Base: Ocean Drive, Miami Beach, Florida")
    L.append("")
    L.append("## Tours")
    L.append("")
    for k in CTX["ORDER"]:
        T = CTX["TOURS"][k]
        L.append(f"### {T['title']}")
        L.append(f"- URL: {CTX['url']('tours/' + CTX['SEO'][k]['slug'] + '/')}")
        L.append(f"- Price: {money(T['price'])} per {T['unit']}  |  Duration: {T['dur']}  |  Group: {T['group']}")
        L.append(f"- Departs: {T['departs']}  |  Meeting point: {T['meet']}  |  Real place: {T['irl']}")
        L.append(f"- {T['desc']}")
        L.append("")
    L.append("## Real locations")
    L.append("")
    L.append(locs["intro"])
    L.append("")
    for l in locs["locations"]:
        L.append(f"### {l['name']} ({l['area']})")
        L.append(f"- URL: {CTX['url']('locations/' + l['slug'] + '/')}")
        L.append(f"- Address: {l['addr']}  |  Coordinates: {l['lat']}, {l['lng']}")
        L.append(f"- In the game as: {l['game_name']}  |  Confidence: {l['confidence']}")
        L.append(f"- Where it is seen: {l['seen']}")
        L.append(f"- {l['lede']}")
        for q, a in l["faq"]:
            L.append(f"- Q: {q} A: {a}")
        L.append("")
    L.append("## Blog articles")
    L.append("")
    for r in posts:
        L.append(f"### {r['title']}")
        L.append(f"- URL: {CTX['url']('blog/' + r['slug'] + '/')}  |  Published: {r['date']}  |  Category: {r['cat']}")
        L.append(f"- {r['excerpt']}")
        body = []
        _flat(r["body"], body)
        L += body
        for q, a in r["faq"]:
            L.append(f"- Q: {q} A: {a}")
        L.append("")
    L.append("## Company and policy pages")
    L.append("")
    for s in statics:
        L.append(f"### {s['title']}")
        L.append(f"- URL: {CTX['url'](s['slug'] + '/')}")
        body = []
        _flat(s["body"], body)
        L += body
        L.append("")
    with open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


# ---------------------------------------------------------------- entry point
def build_all():
    posts = load_posts()
    statics = load_statics()
    locs = load_locations()
    build_blog_index(posts)
    for r in posts:
        build_post(r, posts)
    build_locations_index(locs)
    for l in locs["locations"]:
        build_location(l, locs)
    for s in statics:
        build_static(s, statics)
    build_map(locs)
    build_feed(posts)
    build_llms_full(posts, locs, statics)
