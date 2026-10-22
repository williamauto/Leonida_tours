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


# ---------------------------------------------------------------- contact form
def contact_form():
    """The contact form. No phone number, mailbox or street address is shown:
    the visitor types a message, it is sent to the team by email, and the
    team answers by email."""
    topics = ["A booking or a question about a tour",
              "A group, private or corporate booking",
              "A change to a booking I already made",
              "A correction to something on the site",
              "Media, press or creator enquiry",
              "Something else"]
    opts = "".join(f"<option>{esc(t)}</option>" for t in topics)
    return (
        '<form class="cform" id="contact-form" novalidate>'
        '<div class="cform-grid">'
        '<label class="cf-label">Your name'
        '<input type="text" name="name" autocomplete="name" placeholder="Alex Rivera" required></label>'
        '<label class="cf-label">Your email'
        '<input type="email" name="email" autocomplete="email" placeholder="alex@example.com" required></label>'
        '</div>'
        '<label class="cf-label">What is this about'
        f'<select name="topic">{opts}</select></label>'
        '<div class="cform-grid">'
        '<label class="cf-label">Preferred date <span class="cf-opt">optional</span>'
        '<input type="date" name="travel_date"></label>'
        '<label class="cf-label">Group size <span class="cf-opt">optional</span>'
        '<input type="number" name="group_size" min="1" max="60" placeholder="2"></label>'
        '</div>'
        '<label class="cf-label">Your message'
        '<textarea name="message" rows="7" required '
        'placeholder="Dates, how many of you there are, where you are staying, anything you need to know."></textarea></label>'
        '<p class="cform-note">We answer by email, usually the same day. Nothing you write here is published, '
        'and we never pass your details to anyone else.</p>'
        '<button class="btn btn-primary" type="submit" id="cf-submit">Send message</button>'
        '<p class="cform-msg" id="cf-msg" role="status"></p>'
        '</form>'
    )


def contact_form_script():
    """Client-side handler for the contact form.

    Posts to the form service when one is configured. With no endpoint the
    details are handed to the visitor's own mail client, so the message still
    reaches the team by email. The team address is assembled at runtime, so
    no page source contains it."""
    return (
        CTX["FORM_JS"] +
        "var cf=document.getElementById('contact-form');\n"
        "if(cf){\n"
        "  var cfmsg=document.getElementById('cf-msg'), cfbtn=document.getElementById('cf-submit');\n"
        "  function cfval(n){var el=cf.querySelector('[name='+n+']'); return el?el.value.trim():'';}\n"
        "  cf.addEventListener('submit',function(ev){\n"
        "    ev.preventDefault();\n"
        "    var name=cfval('name'), email=cfval('email'), topic=cfval('topic'),\n"
        "        date=cfval('travel_date'), size=cfval('group_size'), text=cfval('message');\n"
        "    if(!name||!email||!text){cfmsg.className='cform-msg err';"
        "cfmsg.textContent='Please add your name, your email and a short message.';return;}\n"
        "    if(!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$/.test(email)){cfmsg.className='cform-msg err';"
        "cfmsg.textContent='That email address does not look right. Check it and try again.';return;}\n"
        "    cfbtn.disabled=true; cfmsg.className='cform-msg'; cfmsg.textContent='Sending your message...';\n"
        "    var payload={name:name,email:email,topic:topic,travel_date:date,group_size:size,"
        "message:text,source:'contact page'};\n"
        "    ltSend(payload).then(function(channel){\n"
        "      if(channel==='mail'){\n"
        "        var body=['Name: '+name,'Email: '+email,'Topic: '+topic,"
        "date?('Preferred date: '+date):'',size?('Group size: '+size):'','',text].filter(Boolean).join('\\n');\n"
        "        window.location.href=ltMailto('Leonida Tours enquiry',body);\n"
        "        cf.outerHTML='<div class=\"cform-done\"><span class=\"eyebrow\">Almost done</span>"
        "<h3>Send it from your email app</h3>"
        "<p>We have opened a new message with your details. Press send and we will answer by email, usually the same day.</p></div>';\n"
        "      } else {\n"
        "        cf.outerHTML='<div class=\"cform-done\"><span class=\"eyebrow\">Message sent</span>"
        "<h3>Thank you, we have it</h3>"
        "<p>A person reads these. We will answer by email, usually the same day.</p></div>';\n"
        "      }\n"
        "    }).catch(function(){\n"
        "      cfbtn.disabled=false; cfmsg.className='cform-msg err';"
        "cfmsg.textContent='That did not go through. Please try again in a moment.';\n"
        "    });\n"
        "  });\n"
        "}\n"
    )


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
            elif k == "form":
                out.append(contact_form())
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
    return CTX["site_nav"](p, current)


def footer(p):
    return CTX["site_footer"](p)


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
    return ('<section><div class="wrap cta"><span class="eyebrow">Early access &middot; no prepayment needed</span>'
            '<h2 style="margin:0">Come and see it. <span class="grad">Ride first.</span></h2>'
            '<p class="lede">Tell us your date and group size and we will confirm your spot before public booking opens, plus 20% off your first tour.</p>'
            f'<a class="btn btn-primary" href="{p}#preregister">Reserve Now</a></div></section>')


# ---------------------------------------------------------------- blog topics
TOPICS = [
    {"slug": "gta-6-locations", "name": "GTA 6 locations in real life", "kicker": "Topic",
     "title": "GTA 6 Locations in Real Life: Miami Guides | Leonida Tours",
     "h1": "GTA 6 locations in real life",
     "meta": "Guides to the real Miami, Everglades and Florida Keys places behind Vice City and Leonida: maps, regions, trailer timestamps and addresses.",
     "intro": "Where the game map meets the real one. These guides match Vice City and the regions of Leonida to real Miami, Everglades and Florida Keys places, with addresses, coordinates and the trailer moments where they appear.",
     "posts": ["gta-6-locations-in-real-life", "is-gta-6-set-in-miami", "gta-6-map-and-regions", "gta-6-trailers-timestamped",
               "gta-6-everglades-grassrivers", "gta-6-florida-keys-leonida-keys"]},
    {"slug": "miami-travel-guides", "name": "Miami travel guides", "kicker": "Topic",
     "title": "Miami Travel Guides & Itineraries | Leonida Tours",
     "h1": "Miami travel guides",
     "meta": "Plan your days in Miami: one-day and three-day itineraries, sunset cruises on Biscayne Bay and Everglades airboat tips from local tour guides.",
     "intro": "Practical guides for a short trip to South Florida: how to order your days, when the light is best on the water and what an Everglades airboat ride really involves.",
     "posts": ["best-things-to-do-in-miami-beach", "miami-in-3-days-itinerary", "miami-sunset-cruise-guide", "everglades-airboat-tour-guide"]},
    {"slug": "gta-6-launch-week", "name": "GTA 6 release & launch week", "kicker": "Topic",
     "title": "GTA 6 Release & Miami Launch Week Guides | Leonida Tours",
     "h1": "GTA 6 release and launch week in Miami",
     "meta": "The GTA 6 release date and how to plan a South Florida trip around launch week from November 19, 2026: what fills up and when to book.",
     "intro": "Everything about the release date and the week around it: the confirmed timeline, what changes in Miami that week and which experiences to book first.",
     "posts": ["gta-6-release-date", "miami-launch-week-guide"]},
]


def topic_of(slug):
    for t in TOPICS:
        if slug in t["posts"]:
            return t
    return None


def post_card(r, p):
    return (f'<a class="card" href="{p}blog/{r["slug"]}/">'
            f'<img src="{p}img/{r["img"]}.jpg" alt="{esc(r["img_alt"])}" loading="lazy" decoding="async" {CTX["img_attrs"](r["img"])}>'
            f'<div class="cb"><span class="ct">{esc(r["kicker"])}</span><h3>{esc(r["title"])}</h3>'
            f'<p>{esc(r["excerpt"])}</p>'
            f'<span class="cm">{r["date"]} · {reading_time(r["body"])} min read</span></div></a>')


def build_topic(t, posts):
    p = "../../"
    page = CTX["url"](f'blog/{t["slug"]}/')
    by = {r["slug"]: r for r in posts}
    items = [by[x] for x in t["posts"] if x in by]
    others = "".join(f'<a class="tag" href="{p}blog/{o["slug"]}/">{esc(o["name"])}</a>' for o in TOPICS if o is not t)
    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, t["h1"], t["meta"], {"mainEntity": {"@id": page + "#list"}}),
        breadcrumb(page, [("Blog", CTX["url"]("blog/")), (t["name"], page)]),
        {"@type": "CollectionPage", "@id": page + "#list", "name": t["name"], "url": page, "numberOfItems": len(items),
         "itemListElement": [{"@type": "ListItem", "position": i + 1,
                              "item": {"@type": "Article", "name": r["title"], "url": CTX["url"](f'blog/{r["slug"]}/')}}
                             for i, r in enumerate(items)]},
    ]
    # editorial page: like blog articles, exempt from the trademark guard
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(t["title"], t["meta"], page, CTX["url"]("assets/og-home.jpg"), t["name"] + " - Leonida Tours blog", p, CTX["ld"](graph)) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "blog/") +
           '<main><div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><ol>'
           f'<li><a href="{p}">Home</a></li><li><a href="{p}blog/">Blog</a></li><li aria-current="page">{esc(t["name"])}</li></ol></nav></div>'
           f'<div class="wrap ahead"><div class="kicker">Guides<span class="dot"></span>{len(items)} articles</div>'
           f'<h1>{esc(t["h1"])}</h1><p class="lede">{esc(t["intro"])}</p>'
           f'<div class="tag-row"><a class="tag" href="{p}blog/">All guides</a>{others}</div></div>'
           f'<section><div class="wrap"><div class="card-grid">{"".join(post_card(r, p) for r in items)}</div></div></section>'
           + CTA(p) + "</main>" + footer(p) + "</body>\n</html>\n")
    write_html(f'blog/{t["slug"]}', out)


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
    tagrow = "".join(f'<a class="tag" href="{p}blog/{t["slug"]}/">{esc(t["name"])}</a>' for t in TOPICS)
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
           + (f'<li><a href="{p}blog/{topic_of(slug)["slug"]}/">{esc(topic_of(slug)["name"])}</a></li>' if topic_of(slug) else "")
           + f'<li aria-current="page">{esc(r["cat"])}</li></ol></nav></div>'
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
    items = locs["locations"]
    counts = {}
    for l in items:
        counts[l["area"]] = counts.get(l["area"], 0) + 1
    areas = sorted(counts, key=lambda a: (-counts[a], a))
    rows = []
    cards = []
    for l in items:
        badge = confidence_class(l["confidence"])
        rows.append(
            f'<tr><td><a href="{p}locations/{l["slug"]}/">{esc(l["name"])}</a></td>'
            f'<td>{esc(l["game_name"])}</td><td>{esc(l["area"])}</td>'
            f'<td>{esc(l["addr"])}</td>'
            f'<td><span class="badge {badge}">{esc(l["confidence"])}</span></td></tr>'
        )
        cards.append(
            f'<a class="card loc-card" href="{p}locations/{l["slug"]}/" data-area="{esc(l["area"])}">'
            f'<img src="{p}img/{l["img"]}.jpg" alt="{esc(l["img_alt"])}" loading="lazy" decoding="async" {CTX["img_attrs"](l["img"])}>'
            f'<div class="cb"><span class="ct">{esc(l["area"])}</span><h3>{esc(l["name"])}</h3>'
            f'<p>{esc(l["addr"])}</p>'
            f'<span class="badge {badge}">{esc(l["confidence"])}</span></div></a>'
        )
    chips = [f'<button type="button" data-area="all" aria-pressed="true">All places <small>{len(items)}</small></button>']
    for a in areas:
        chips.append(f'<button type="button" data-area="{esc(a)}" aria-pressed="false">{esc(a)} <small>{counts[a]}</small></button>')
    graph = [
        CTX["org"](),
        {"@type": "WebSite", "@id": CTX["SITE_ID"], "url": CTX["url"](), "name": CTX["BRAND"]},
        web_page(page, "Real locations field guide",
                 "Fifteen real places in Miami, the Everglades and the Florida Keys matched to their in-game counterparts, with addresses, coordinates and a confidence rating for each.",
                 {"mainEntity": {"@id": page + "#list"}}),
        breadcrumb(page, [("Locations", page)]),
        {"@type": "CollectionPage", "@id": page + "#list", "name": "Leonida Tours real locations field guide",
         "url": page, "numberOfItems": len(items),
         "itemListElement": [{"@type": "ListItem", "position": i + 1,
                              "item": {"@type": "TouristAttraction", "name": l["name"],
                                       "url": CTX["url"](f'locations/{l["slug"]}/'),
                                       "address": l["addr"],
                                       "geo": {"@type": "GeoCoordinates", "latitude": l["lat"], "longitude": l["lng"]}}}
                             for i, l in enumerate(items)]},
    ]
    guard("locations index", [("title", f"Real Locations Field Guide | {CTX['BRAND']}"),
                              ("h1", "The real places behind the game"),
                              ("meta", "Fifteen real Miami, Everglades and Florida Keys places matched to their in-game counterparts, with addresses, coordinates and a confidence rating.")],
          graph)
    extra = CTX["ld"](graph)
    js = """
<script>
(function(){
  var chips=document.querySelectorAll('#locFilter button[data-area]');
  var cards=document.querySelectorAll('#locGrid .loc-card');
  var count=document.getElementById('locCount');
  var empty=document.getElementById('locEmpty');
  if(!chips.length||!cards.length) return;
  function apply(a){
    chips.forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.area===a)); });
    var n=0;
    cards.forEach(function(c){ var ok=(a==='all'||c.dataset.area===a); c.hidden=!ok; if(ok)n++; });
    if(count) count.textContent = a==='all' ? 'Showing all '+n+' places' : 'Showing '+n+' place'+(n===1?'':'s')+' in '+a;
    if(empty) empty.hidden = n>0;
  }
  chips.forEach(function(b){ b.addEventListener('click', function(){ apply(b.dataset.area); }); });
  try{
    var q=new URLSearchParams(window.location.search).get('area');
    if(q){
      chips.forEach(function(b){ if(b.dataset.area===q) apply(q); });
    }
  }catch(e){}
})();
</script>
"""
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           page_head(f"Real Locations Field Guide | {CTX['BRAND']}",
                     "Fifteen real Miami, Everglades and Florida Keys places matched to their in-game counterparts, with addresses, coordinates and a confidence rating.",
                     page, CTX["url"]("assets/og-home.jpg"),
                     "Leonida Tours real locations field guide: Miami, Everglades and Florida Keys", p, extra) +
           "</head>\n<body>\n" + CTX["GTM_BODY"] + nav(p, "locations/") +
           '<main><div class="wrap ahead"><div class="kicker">Field guide<span class="dot"></span>15 places</div>'
           "<h1>The real places behind the game</h1>"
           f'<p class="lede">{esc(locs["intro"])}</p>'
           '<div class="tag-row"><span class="tag"><a href="../map/" style="color:inherit;text-decoration:none">Open the map</a></span>'
           '<span class="tag"><a href="../blog/gta-6-locations-in-real-life/" style="color:inherit;text-decoration:none">Read the full guide</a></span></div>'
           '</div>'
           '<section><div class="wrap">'
           '<h2>Every place</h2>'
           '<div class="loc-bar">'
           f'<div class="ride-toggle" role="group" aria-label="Filter places by area" id="locFilter">{"".join(chips)}</div>'
           f'<p class="loc-count" id="locCount" role="status">Showing all {len(items)} places</p>'
           '</div>'
           f'<div class="card-grid" id="locGrid">{"".join(cards)}</div>'
           '<p class="loc-empty" id="locEmpty" hidden>No places in this area yet. Pick another area.</p>'
           '</div></section>'
           '<section><div class="wrap">'
           f'<details class="table-details"><summary>Full index table &middot; all {len(items)} places with addresses</summary>'
           '<div class="table-scroll"><table><thead><tr><th>Real place</th><th>In the game</th><th>District</th><th>Address</th><th>Confidence</th></tr></thead>'
           f'<tbody>{"".join(rows)}</tbody></table></div></details>'
           '</div></section>'
           + CTA(p) +
           "</main>" + footer(p) + js + "</body>\n</html>\n")
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
        extra_schema = {"mainEntity": {"@id": CTX["ORG_ID"]}}
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
            ("<script>" + contact_form_script() + "</script>" if slug == "contact" else "") +
            "</main>" + footer(p) + "</body>\n</html>\n")
    write_html(slug, out)


AREA_COLORS = {
    "Vice City": "#FF5FA2",
    "Vice Beach": "#FF8A65",
    "Greater Leonida": "#7CC4FF",
    "Leonida Keys": "#FFA66B",
    "Grassrivers": "#3EE6D6",
}


def build_map(locs):
    p = "../"
    page = CTX["url"]("map/")
    items = locs["locations"]
    counts = {}
    for l in items:
        counts[l["area"]] = counts.get(l["area"], 0) + 1
    areas = sorted(counts, key=lambda a: (-counts[a], a))
    markers = [{
        "n": l["name"], "g": l["game_name"], "a": l["area"], "addr": l["addr"],
        "lat": l["lat"], "lng": l["lng"], "c": l["confidence"],
        "col": AREA_COLORS.get(l["area"], "#FF5FA2"),
        "slug": l["slug"], "url": CTX["url"](f'locations/{l["slug"]}/'),
        "gm": map_link(l["lat"], l["lng"]),
    } for l in items]
    chips = [f'<button type="button" data-area="all" aria-pressed="true">All places <small>{len(items)}</small></button>']
    for a in areas:
        chips.append(f'<button type="button" data-area="{esc(a)}" aria-pressed="false">{esc(a)} <small>{counts[a]}</small></button>')
    legend = "".join(
        f'<span><i style="background:{AREA_COLORS.get(a, "#FF5FA2")}"></i>{esc(a)} <b>{counts[a]}</b></span>'
        for a in areas)
    lst = ""
    for i, l in enumerate(items):
        lst += (f'<div class="map-item" data-area="{esc(l["area"])}" data-i="{i}">'
                f'<em>{esc(l["area"])}</em>'
                f'<a href="{p}locations/{l["slug"]}/"><strong>{esc(l["name"])}</strong></a>'
                f'<span>{esc(l["addr"])}</span>'
                f'<button type="button" class="map-focus" data-i="{i}" aria-label="Show {esc(l["name"])} on the map">Show on map</button>'
                f'</div>')
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
    script = ('<link rel="preconnect" href="https://a.basemaps.cartocdn.com" crossorigin>\n'
              '<link rel="preconnect" href="https://tile.openstreetmap.org" crossorigin>\n'
              f'<link rel="stylesheet" href="{p}assets/vendor/leaflet/leaflet.css">\n'
              f'<script src="{p}assets/vendor/leaflet/leaflet.js" defer></script>\n')
    data = json.dumps(markers, ensure_ascii=False).replace("</", "<\\/")
    js = """
<script>window.__LOCS=__DATA__;</script>
<script>
function initMap(){
  if(window.__LEONIDA_MAP_READY) return;
  window.__LEONIDA_MAP_READY = true;
  var ITEMS = window.__LOCS || [];
  var mapEl = document.getElementById('map');
  if(!mapEl) return;
  var fallback = document.getElementById('mapFallback');
  var chips = Array.prototype.slice.call(document.querySelectorAll('#mapFilter button[data-area]'));
  var listItems = Array.prototype.slice.call(document.querySelectorAll('#mapList .map-item'));
  var countEl = document.getElementById('mapCount');
  var state = 'all';
  var map = null;
  var markers = [];

  function label(a,n){ return a==='all' ? 'Showing all '+n+' places' : 'Showing '+n+' place'+(n===1?'':'s')+' in '+a; }
  function setCount(n){ if(countEl) countEl.textContent = label(state,n); }

  function highlight(i){
    listItems.forEach(function(el){ el.classList.remove('on'); });
    var el = listItems[i];
    if(el){ el.classList.add('on'); try{ el.scrollIntoView({block:'nearest',behavior:'smooth'}); }catch(e){} }
  }
  function focus(i){
    var o = ITEMS[i];
    if(!o) return;
    highlight(i);
    try{ mapEl.scrollIntoView({block:'center', behavior:'smooth'}); }catch(e){}
    if(!map) return;
    try{ map.flyTo([o.lat,o.lng], Math.max(map.getZoom(),13), {duration:.6}); }catch(e){}
    var mk = markers[i];
    if(mk){ try{ mk.openPopup(); }catch(e){} }
  }
  function apply(a){
    state = a;
    chips.forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.area===a)); });
    var shown = 0;
    ITEMS.forEach(function(o,i){
      var ok = (a==='all' || o.a===a);
      var mk = markers[i];
      if(mk && map){
        try{
          if(ok){ if(!map.hasLayer(mk)) mk.addTo(map); }
          else if(map.hasLayer(mk)) map.removeLayer(mk);
        }catch(e){}
      }
      if(listItems[i]) listItems[i].hidden = !ok;
      if(ok) shown++;
    });
    setCount(shown);
    if(map){
      try{
        if(a==='all'){ map.setView([25.79,-80.20], 10); }
        else{
          var b = L.latLngBounds([]);
          ITEMS.forEach(function(o,i){ if(o.a===a && markers[i]) b.extend(markers[i].getLatLng()); });
          if(b.isValid()) map.fitBounds(b.pad(0.3));
        }
      }catch(e){}
      setTimeout(function(){ try{ map.invalidateSize(); }catch(e){} }, 250);
    }
  }

  chips.forEach(function(b){ b.addEventListener('click', function(){ apply(b.dataset.area); }); });
  Array.prototype.forEach.call(document.querySelectorAll('#mapList .map-focus'), function(btn){
    btn.addEventListener('click', function(){ focus(parseInt(btn.dataset.i,10)); });
  });

  if(!window.L){
    mapEl.style.display='none';
    if(fallback) fallback.hidden=false;
    setCount(ITEMS.length);
    return;
  }
  try{
    map = L.map(mapEl, {scrollWheelZoom:false, zoomControl:true, attributionControl:true}).setView([25.79,-80.20],10);
    var dark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      {attribution:'&copy; OpenStreetMap &copy; CARTO', maxZoom:19, subdomains:'abcd', crossOrigin:true});
    var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
      {attribution:'&copy; OpenStreetMap contributors', maxZoom:19, crossOrigin:true});
    var swapped = false;
    dark.on('tileerror', function(){
      if(swapped) return;
      swapped = true;
      try{ map.removeLayer(dark); osm.addTo(map); }catch(e){}
    });
    dark.addTo(map);
    ITEMS.forEach(function(o,i){
      var mk = L.marker([o.lat,o.lng], {icon: L.divIcon({
        className:'lm-num',
        html:'<span style="background:'+o.col+'">'+(i+1)+'</span>',
        iconSize:[30,30], iconAnchor:[15,15], popupAnchor:[0,-16]})});
      mk.bindPopup('<strong>'+o.n+'</strong><br>'+o.addr+'<br><em>'+o.a+' &middot; '+o.c+'</em><br>'
        + '<a href="'+o.url+'">Read the page</a> &middot; <a href="'+o.gm+'" rel="nofollow noopener">Google Maps</a>');
      mk.on('click', function(){ highlight(i); });
      mk.addTo(map);
      markers[i]=mk;
    });
    setTimeout(function(){ try{ map.invalidateSize(); }catch(e){} }, 350);
    window.addEventListener('load', function(){ setTimeout(function(){ try{ map.invalidateSize(); }catch(e){} }, 200); });
  }catch(e){
    mapEl.style.display='none';
    if(fallback) fallback.hidden=false;
  }
}
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded', initMap);
  window.addEventListener('load', function(){ setTimeout(initMap, 0); });
}else{
  initMap();
}
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
           '<p class="lede">Every location on this map is a real, publicly accessible place in South Florida, with coordinates you can check. '
           'Pick an area to narrow the map, click a numbered pin for details, or pick a place from the list.</p>'
           '<div class="tag-row"><span class="tag"><a href="../locations/" style="color:inherit;text-decoration:none">Browse the list</a></span>'
           '<span class="tag"><a href="../blog/gta-6-locations-in-real-life/" style="color:inherit;text-decoration:none">Read the full guide</a></span></div>'
           '</div>'
           '<section><div class="wrap">'
           '<div class="loc-bar">'
           f'<div class="ride-toggle" role="group" aria-label="Filter map places by area" id="mapFilter">{"".join(chips)}</div>'
           f'<p class="loc-count" id="mapCount" role="status">Showing all {len(items)} places</p>'
           '</div>'
           '<div class="map-legend">' + legend + '</div>'
           '</div></section>'
           f'<section><div class="wrap map-grid"><div class="map-panel"><div id="map" role="img" aria-label="Map of {len(items)} real South Florida locations"></div>'
           '<div class="map-fallback" id="mapFallback" hidden><strong>The interactive map did not load.</strong>'
           '<span>Every place is still listed next to this panel with its address, coordinates and a link to the full page.</span></div></div>'
           f'<div class="map-list" id="mapList">{lst}</div></div></section>'
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
             "Everglades and Florida Keys places. Reservations need no prepayment. "
             "Not affiliated with, endorsed by or sponsored by any game publisher. "
             "All game names are used only to identify real-world locations.")
    L.append("")
    L.append(f"Site: {CTX['url']()}  |  Contact: {CTX['url']('contact/')}  |  "
             "One form for enquiries, and we answer by email. "
             "No street address, phone number or mailbox is published: pickup points are sent with each booking, and we collect guests "
             "across the greater Miami area.")
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
    for t in TOPICS:
        build_topic(t, posts)
    build_locations_index(locs)
    for l in locs["locations"]:
        build_location(l, locs)
    for s in statics:
        build_static(s, statics)
    build_map(locs)
    build_feed(posts)
    build_llms_full(posts, locs, statics)
