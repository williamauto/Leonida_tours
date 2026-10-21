#!/usr/bin/env python3
"""Build the Leonida Tours static site with full SEO plumbing.

Usage:  SITE_URL=https://leonidatours.com python3 _build/build.py
SITE_URL is the public address the site is served from (custom domain or
https://<user>.github.io/<repo>). Every canonical, sitemap and schema URL uses it.
All internal links are relative, so the site works at a domain root or in a subfolder.
"""
import json, os, re, html, datetime, hashlib
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.environ.get("SITE_URL", "https://leonidatours.com").rstrip("/")
HOST = urlparse(SITE).netloc
IS_ROOT = urlparse(SITE).path in ("", "/")
TODAY = datetime.date.today().isoformat()
LAUNCH = "2026-11-19"
EMAIL = "hello@leonidatours.com"
BRAND = "Leonida Tours"
SOCIAL = ["https://www.instagram.com/leonidatours", "https://www.tiktok.com/@leonidatours"]

D = json.load(open(os.path.join(HERE, "data.json")))
TOURS, ORDER, LAND, WATER = D["TOURS"], D["ORDER"], D["LAND"], D["WATER"]
esc = lambda s: html.escape(str(s), quote=True)
money = lambda n: "${:,}".format(n)

ALT = {
    "hero": "Downtown Miami skyline across Biscayne Bay at a pink sunset",
    "oceannight": "Neon-lit Art Deco hotels on Ocean Drive, Miami Beach, at night",
    "neon": "Ocean Drive neon signs and palm trees at night, Miami Beach",
    "decoday": "Pastel Art Deco hotels on Ocean Drive, Miami Beach",
    "tower": "Red lifeguard tower on Lummus Park Beach, Miami Beach",
    "bridgenight": "Miami skyline and causeway bridge at sunset over Biscayne Bay",
    "causeway": "Causeway bridge and Miami skyline lit up at night",
    "downtown": "Downtown Miami highways, palm trees and towers at night",
    "wynwood": "Bright street mural in the Wynwood arts district, Miami",
    "laperle": "Colorful murals on a wall in Little Haiti, Miami",
    "havana": "Welcome to Little Havana mural with a rooster on Calle Ocho, Miami",
    "brickell": "Neon-lit Brickell towers at night, Miami",
    "boat": "Boat speeding across Biscayne Bay toward the Miami skyline",
    "port": "Aerial view of PortMiami, cruise ships and the islands of Biscayne Bay",
    "skyday": "Brickell skyline reflected in Biscayne Bay at golden hour",
    "airboat": "Airboat gliding through Everglades sawgrass at sunrise",
    "glades": "Everglades wetland reflecting a golden sunset",
    "keys": "Seven Mile Bridge over turquoise water in the Florida Keys",
    "keysaerial": "Aerial view of the Overseas Highway crossing a Florida Keys island",
    "classic": "Vintage yellow convertible parked outside a neon Ocean Drive restaurant",
    "drone": "Small drone hovering above an outstretched hand over the bay",
    "bandana": "Guest wearing a red paisley bandana and floral shirt",
    "beach": "Lifeguard tower on Miami Beach at sunset",
    "pm_bay": "Traveler photographing Biscayne Bay from the waterfront",
    "pm_beach": "Friends laughing on South Beach with the Miami Beach skyline behind",
    "pm_palms": "Visitor snapping a photo of tall palm trees against a blue sky",
    "pm_wynwood": "Two friends posing in front of a graffiti wall in Wynwood",
    "b_fisher": "Aerial view of Fisher Island and the turquoise water off Miami Beach",
    "b_marina": "White superyacht docked at Miami Beach Marina",
    "b_palm": "Palm-lined island estates on Biscayne Bay with the Miami skyline behind",
    "b_star": "Waterfront mansion and palm trees on Star Island, Miami",
    "pm_boat": "Couple relaxing on a boat on Biscayne Bay with Miami towers behind",
    "pm_bridge": "Guest on a boat watching the Brickell skyline at sunset",
    "pm_graffiti": "Woman posing against a colorful graffiti wall in Wynwood",
    "pm_tower": "Friends sitting under a pink lifeguard tower on Miami Beach",
}
SIZE = {f[:-4]: Image.open(os.path.join(ROOT, "img", f)).size
        for f in os.listdir(os.path.join(ROOT, "img")) if f.endswith(".jpg")}

# ---------------------------------------------------------------- per-tour SEO copy
SEO = {
 "vc-van": dict(slug="miami-small-group-tour", type="Miami city tour",
  title="Miami Vice City Small-Group Tour (3h, $79) | Leonida Tours",
  meta="3-hour small-group tour of the real Miami spots behind the trailers: Ocean Drive, Lummus Park, Wynwood, Little Haiti, Little Havana & Brickell. $79.",
  intro="This is the signature Leonida Tours loop: eight real Miami stops in three hours, ridden in an air-conditioned minibus with a local host who knows which corner matches which scene. It works just as well as a first-time Miami city tour, game fan or not.",
  faq=[("How long is the Miami Vice City tour?","About 3 hours, starting and ending on Ocean Drive in Miami Beach. Day departures leave at 10am and 2pm, and the sunset + night departure leaves at 6:30pm."),
       ("Which neighborhoods does it visit?","Ocean Drive and Lummus Park in Miami Beach, the Venetian Causeway, Downtown and Biscayne Boulevard, Wynwood, Little Haiti, Little Havana and Brickell."),
       ("How big are the groups?","Up to 12 guests per minibus, with one host.")]),
 "vc-car": dict(slug="private-classic-convertible-tour-miami", type="Private Miami tour",
  title="Private Classic Convertible Miami Tour | Leonida Tours",
  meta="Up to 3 guests in a top-down vintage convertible with a driver-guide: Ocean Drive, Wynwood, Little Havana and Brickell at golden hour. $600 per car.",
  intro="The most cinematic way to see Miami: a vintage convertible with the top down, a driver-guide who knows every camera angle, and the full eight-stop route at your own pace. Built for couples, birthdays, proposals and content shoots.",
  faq=[("How many people fit in the classic car?","Up to 3 guests plus your driver-guide. The $600 price is per car, not per person."),
       ("Where does the private tour start?","We pick you up in Miami Beach, Downtown or Brickell at the time you choose."),
       ("Can we film or shoot photos?","Yes. The route includes a golden-hour photo stop on the causeway, and drone shots can be added.")]),
 "vc-jeep": dict(slug="private-jeep-tour-miami", type="Private Miami tour",
  title="Private Open-Top Jeep Tour of Miami ($450) | Leonida Tours",
  meta="Roof off: a private open-top Jeep tour of Miami for up to 3, with a driver-guide, sunset photo stops and the full Ocean Drive to Brickell loop. Hotel pickup.",
  intro="An open-top Jeep, your crew and a driver-guide running the full Miami loop, from the Ocean Drive neon to the Brickell skyline. The best-value private option on the map.",
  faq=[("How is the Jeep tour different from the classic car?","Same private route and guide, in an open-top Jeep instead of a vintage convertible, for $450 per Jeep."),
       ("How long does it take?","About 2.5 hours, starting from your hotel in Miami Beach, Downtown or Brickell.")]),
 "vc-boat": dict(slug="miami-boat-tour-biscayne-bay", type="Miami boat tour",
  title="Millionaire's Row Boat Tour Miami: Star Island | Leonida Tours",
  meta="2-hour Millionaire's Row boat tour from Bayside: PortMiami, Fisher Island, megayachts, Star, Palm & Hibiscus Island mansions and a sunset skyline. $79.",
  intro="Our Millionaire's Row cruise shows Miami the way the trailers frame it, from the water. A licensed captain and host loop out of Bayside Marina past PortMiami, Fisher Island and the Miami Beach Marina megayachts, then the celebrity mansions of Star, Palm and Hibiscus Islands and the Venetian Islands, before cutting the engines for the skyline at golden hour.",
  faq=[("Where does the Miami boat tour leave from?","Bayside Marina in Downtown Miami, with departures at 11am, 4pm and sunset."),
       ("Which mansions and islands do we see?","Star Island and the rest of Millionaire's Row, Palm and Hibiscus Islands, Fisher Island and the Venetian Islands, plus the megayachts at Miami Beach Marina."),
       ("Is the sunset departure worth it?","Yes. The tour ends with a golden-hour hold on the skyline, the shot fans know best.")]),
 "airboat": dict(slug="everglades-airboat-tour-from-miami", type="Everglades airboat tour",
  title="Everglades Airboat Tour from Miami | Leonida Tours",
  meta="Half-day Everglades airboat tour with shuttle from Miami: airboat ride, wildlife guide and gator spotting. Add a gator farm or night ATV ride. $79.",
  intro="Leave the neon behind for the swamp that inspired the game's wetlands, the Grasslands. A shuttle takes you from Miami to the Everglades for an airboat run through the sawgrass with a wildlife guide, then a boardwalk and viewing-tower stop.",
  faq=[("Is transport from Miami included?","Yes. The tour includes a round-trip shuttle from Miami."),
       ("Will we see alligators?","Your wildlife guide takes you to the places gators are most often spotted, though wildlife sightings are never guaranteed."),
       ("Can I add anything to the airboat tour?","Yes: an alligator farm visit (+$29), or a one-hour glow-in-the-dark ATV ride after sunset (+$79)."),
       ("Is it suitable for kids?","Yes, for ages 5 and up.")]),
 "nightsky": dict(slug="everglades-night-sky-stargazing-tour", type="Everglades night tour",
  title="Everglades Sunset Airboat & Stargazing | Leonida Tours",
  meta="Evening trip from Miami: a sunset airboat ride in the Everglades, then stargazing with a sky guide in a dark-sky preserve. $129 per person.",
  intro="An evening in the Grasslands: a sunset airboat ride in the Everglades, then on to a dark-sky preserve for stargazing with a sky guide and an open-air projector screening of real-versus-game scenes.",
  faq=[("What time does the night sky tour leave?","3pm pickup in Miami, for about 6 hours in total."),
       ("Who is it for?","Night owls, nature and photo fans, ages 12 and up.")]),
 "keys": dict(slug="florida-keys-day-trip-from-miami", type="Florida Keys day trip",
  title="Florida Keys Day Trip from Miami | Leonida Tours",
  meta="Full-day small-group road trip from Miami down the Overseas Highway: Key Largo, Islamorada, the Seven Mile Bridge and beach time. $149 per person.",
  intro="The island road that inspired the Leonida Keys. A small-group minibus takes you down the Overseas Highway through Key Largo and Islamorada to the Seven Mile Bridge, with beach time at a state park and a seafood lunch stop.",
  faq=[("How long is the Florida Keys day trip?","A full day, with a 7:30am pickup in Miami."),
       ("Do we go to Key West?","No. The route covers Key Largo, Islamorada and the Seven Mile Bridge, which leaves time for the beach instead of a long day on the road.")]),
 "pass": dict(slug="leonida-city-pass", type="Miami tour pass",
  title="Leonida City Pass: 3 Miami Tours for $199 | Leonida Tours",
  meta="One pass for the Miami Vice City tour, the Biscayne Bay boat tour and the Everglades airboat, each booked on your schedule. $237 value for $199.",
  intro="The whole map in one pass: streets, bay and swamp. The Leonida City Pass covers three of our experiences, each booked on the date that suits your trip.",
  faq=[("What does the City Pass include?","The Miami Vice City small-group tour, Miami Vice City by Boat and the Grasslands Airboat in the Everglades."),
       ("Do I have to do all three on the same day?","No. Book each experience whenever you like during your stay.")]),
}
ITIN = {"vc-van": LAND, "vc-car": LAND, "vc-jeep": LAND, "vc-boat": WATER,
        "airboat": [dict(name="Shuttle from Miami", irl="pickup", img="hero", p="Round-trip transport from Miami to the edge of the Everglades."),
                    dict(name="Everglades airboat ride", irl="the Grasslands", img="airboat", p="A 30-minute airboat run through the sawgrass with a wildlife guide."),
                    dict(name="Boardwalk and viewing tower", irl="gator spotting", img="glades", p="Walk the boardwalk and climb the viewing tower to scan the wetlands.")],
        "nightsky": [dict(name="Sunset airboat ride", irl="the Grasslands", img="airboat", p="An airboat run through the Everglades as the sun goes down."),
                     dict(name="Dark-sky preserve", irl="Big Cypress", img="glades", p="Stargazing with a sky guide, far from city light."),
                     dict(name="Open-air screening", irl="real vs game", img="neon", p="A projector screening that matches real places to their in-game scenes.")],
        "keys": [dict(name="Key Largo", irl="first island stop", img="keysaerial", p="The first of the islands, at the top of the Overseas Highway."),
                 dict(name="Islamorada", irl="seafood lunch stop", img="keys", p="Island stop for lunch and a stretch by the water."),
                 dict(name="Seven Mile Bridge", irl="the bridge shot", img="keys", p="Photo stop at the bridge that runs to the horizon."),
                 dict(name="State park beach", irl="beach time", img="keysaerial", p="Swim and turquoise water before the drive back.")]}
FAQ = [
 ("Is this an official game tour?", "No. Leonida Tours is an independent South Florida tour company running unofficial tours. We take you IRL to the real places that inspired the game's world. We are not affiliated with, endorsed or sponsored by Rockstar Games or Take-Two Interactive."),
 ("Why do you use names like Leonida?", "Fans know these places by their in-game nicknames, so we use them to point you to the real spots that inspired them. Every stop is a real, public place in Miami, the Everglades or the Florida Keys."),
 ("Do I need to be a gamer?", "Not at all. Fans get the scene-by-scene details. Everyone else gets Miami Beach, downtown, Wynwood, Little Haiti, Little Havana, the Everglades and the Keys with a great local guide."),
 ("What does reserving mean?", "It's free and there's no payment today. We email you to confirm your date before public booking opens, plus 20% off your first tour."),
 ("When do tours start?", "Mid-November 2026. Miami tours run daily; the Grasslands (Everglades) and Leonida Keys trips run on set days each week."),
 ("What's the difference between small group and private?", "Small-group tours ride in a minibus with up to 12 guests and a host. Private tours are just your crew, up to 3 people, in a classic convertible ($600) or a Jeep convertible ($450) with a driver-guide."),
 ("How does the City Pass work?", "One pass covers the Miami Vice City small-group tour, the boat tour and the Grasslands airboat. Book each date whenever you like during your stay."),
 ("What if it rains?", "Every route has covered stops. If a storm cancels your tour, rebook for free or get a full refund."),
]
DISCLAIMER = ("<strong>Unofficial tours.</strong> Leonida Tours is an independent tour company. Our tours are not affiliated with, endorsed, sponsored, licensed or authorized by Rockstar Games, Inc., Take-Two Interactive Software, Inc. or any of their affiliates. All game titles, characters, place names and trademarks belong to their respective owners and are used here only to describe the real-world locations that inspired them. Every stop on our tours is a real, publicly accessible place. Photography via Unsplash.")

url = lambda path="": SITE + "/" + path
turl = lambda k: url(f"tours/{SEO[k]['slug']}/")

# ---------------------------------------------------------------- schema
ORG_ID, SITE_ID = url("#organization"), url("#website")
def org():
    return {"@type": "TravelAgency", "@id": ORG_ID, "name": BRAND, "url": url(),
            "logo": {"@type": "ImageObject", "url": url("assets/icon-512.png"), "width": 512, "height": 512},
            "image": url("assets/og-home.jpg"), "email": EMAIL,
            "description": "Independent South Florida tour company running unofficial small-group and private tours to the real Miami, Everglades and Florida Keys locations that inspired the game world of Leonida.",
            "slogan": "Leonida is real. Play it IRL.", "priceRange": "$79–$600", "currenciesAccepted": "USD",
            "address": {"@type": "PostalAddress", "streetAddress": "Ocean Drive", "addressLocality": "Miami Beach",
                        "addressRegion": "FL", "addressCountry": "US"},
            "geo": {"@type": "GeoCoordinates", "latitude": 25.7781, "longitude": -80.1310},
            "areaServed": [{"@type": "City", "name": "Miami"}, {"@type": "City", "name": "Miami Beach"},
                           {"@type": "Place", "name": "Everglades National Park"}, {"@type": "Place", "name": "Florida Keys"}],
            "knowsAbout": ["Miami tours", "Ocean Drive", "Wynwood", "Little Havana", "Everglades airboat tours",
                           "Florida Keys day trips", "Biscayne Bay boat tours", "Vice City", "Leonida"],
            "sameAs": SOCIAL}

def offer(k):
    T = TOURS[k]
    return {"@type": "Offer", "price": str(T["price"]), "priceCurrency": "USD", "url": turl(k),
            "availability": "https://schema.org/PreOrder", "validFrom": TODAY, "availabilityStarts": LAUNCH,
            "priceSpecification": {"@type": "UnitPriceSpecification", "price": T["price"], "priceCurrency": "USD",
                                   "unitText": "per " + T["unit"]},
            "seller": {"@id": ORG_ID}}

def trip(k, full=True):
    T, S = TOURS[k], SEO[k]
    d = {"@type": "TouristTrip", "@id": turl(k) + "#trip", "name": T["title"], "url": turl(k),
         "description": T["desc"], "image": [url(f"img/{T['img']}.jpg"), url(f"assets/og/{S['slug']}.jpg")],
         "touristType": T["good"], "provider": {"@id": ORG_ID}, "offers": offer(k)}
    if full:
        d["duration"] = {"3 hours · day or night": "PT3H", "3 hours": "PT3H", "2.5 hours": "PT2H30M", "2 hours": "PT2H", "4 hours": "PT4H",
                         "6 hours": "PT6H", "Full day": "PT10H"}.get(T["dur"])
        if not d["duration"]: d.pop("duration")
        if k == "pass":
            d["subTrip"] = [{"@id": turl(x) + "#trip", "@type": "TouristTrip", "name": TOURS[x]["title"], "url": turl(x)}
                            for x in ("vc-van", "vc-boat", "airboat")]
        else:
            stops = ITIN.get(k, [])
            seen, items = set(), []
            for s in stops:
                if s["name"] in seen or s["name"].startswith("Back to"): continue
                seen.add(s["name"])
                items.append({"@type": "ListItem", "position": len(items) + 1,
                              "item": {"@type": "TouristAttraction", "name": s["name"], "description": s["p"],
                                       "image": url(f"img/{s['img']}.jpg")}})
            if items: d["itinerary"] = {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items}
    return d

def faq_schema(items, page):
    return {"@type": "FAQPage", "@id": page + "#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]}

def ld(graph):
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph},
                                                              ensure_ascii=False, separators=(",", ":")) + "</script>"

def head_common(title, desc, canonical, og_img, og_alt, prefix, extra=""):
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canonical}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="author" content="{BRAND}">
<meta name="theme-color" content="#0A0910">
<meta name="color-scheme" content="dark">
<meta name="format-detection" content="telephone=no">
<meta name="geo.region" content="US-FL"><meta name="geo.placename" content="Miami Beach">
<meta name="geo.position" content="25.7781;-80.1310"><meta name="ICBM" content="25.7781, -80.1310">
<link rel="alternate" hreflang="en-us" href="{canonical}"><link rel="alternate" hreflang="x-default" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonidatours">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{og_img}">
<link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{prefix}favicon.ico" sizes="48x48">
<link rel="icon" href="{prefix}assets/icon-96.png" sizes="96x96" type="image/png">
<link rel="icon" href="{prefix}assets/icon-48.png" sizes="48x48" type="image/png">
<link rel="apple-touch-icon" href="{prefix}assets/apple-touch-icon.png">
<link rel="manifest" href="{prefix}site.webmanifest">
<link rel="sitemap" type="application/xml" href="{prefix}sitemap.xml">
<link rel="alternate" type="text/plain" title="LLM summary" href="{prefix}llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap">
{extra}"""

def img_attrs(name):
    w, h = SIZE[name]
    return f'width="{w}" height="{h}"'

# ---------------------------------------------------------------- index.html
def build_index():
    src = open(os.path.join(HERE, "index.src.html"), encoding="utf-8").read()
    css = re.search(r'display=swap">\s*<style>(.*?)</style>', src, re.S).group(1)
    body = src[src.index('<nav class="nav"'):]
    body = body[:body.rindex("</body>")]

    # static, crawlable mission cards (identical markup to the JS render, but real links)
    cards = []
    for k in ORDER:
        T = TOURS[k]
        chip = "" if k == "pass" else f'<span class="mode-chip{" self" if T.get("priv") else ""}">{"Private" if T.get("priv") else "Small group"}</span>'
        cards.append(f'<a class="mcard{" pass" if k=="pass" else ""}" href="tours/{SEO[k]["slug"]}/" data-open="{k}">'
                     f'<div class="ph"><img src="img/{T["img"]}.jpg" alt="{esc(ALT[T["img"]])}" loading="lazy" decoding="async" {img_attrs(T["img"])}>'
                     f'<span class="loc">{esc(T["loc"])}</span>{chip}</div><div class="bd"><span class="irl">IRL · <b>{esc(T["irl"])}</b></span>'
                     f'<h3>{esc(T["title"])}</h3><div class="meta"><span>{esc(T["dur"])}</span><strong>{money(T["price"])}<small> /{esc(T["unit"])}</small></strong></div></div></a>')
    body = body.replace('<div class="missions" id="missions"></div>', '<div class="missions" id="missions">' + "".join(cards) + "</div>")
    body = re.sub(r"\n\$\('#missions'\)\.innerHTML=ORDER\.map\(.*?\.join\(''\);", "\n/* missions are pre-rendered in HTML */", body, flags=re.S)

    # static itinerary for crawlers (JS re-renders the same list)
    stops = "".join(f'<li class="stop" data-i="{i}"><div class="ph"><img src="img/{s["img"]}.jpg" alt="{esc(ALT[s["img"]])}" loading="lazy" decoding="async" {img_attrs(s["img"])}><span class="n">{i+1}</span></div>'
                    f'<div><span class="time">+{s["t"]}</span><h3>{esc(s["name"])}</h3><span class="irl">Inspired · <b>{esc(s["irl"])}</b></span><p>{esc(s["p"])}</p>'
                    f'{"<span class=quest>★ "+esc(s["q"])+"</span>" if s.get("q") else ""}</div></li>' for i, s in enumerate(LAND))
    body = body.replace('<ol class="stops" id="stops"></ol>', f'<ol class="stops" id="stops">{stops}</ol>')

    # modal: link to the full tour page
    body = body.replace("const modal=$('#tourModal');",
        "const TOUR_URL=" + json.dumps({k: f"tours/{SEO[k]['slug']}/" for k in ORDER}) + ";\nconst modal=$('#tourModal');")
    body = body.replace('<a class="btn btn-primary btn-sm" href="#preregister" data-pick="${k}" data-close="1">Reserve</a>',
        '<a class="btn btn-glass btn-sm" href="${TOUR_URL[k]}">Tour page</a><a class="btn btn-primary btn-sm" href="#preregister" data-pick="${k}" data-close="1">Reserve</a>')

    # ?tour=key preselects the form (used by tour-page Reserve buttons)
    body = body.replace("gs.addEventListener('change',syncSize); syncSize();",
        "gs.addEventListener('change',syncSize); syncSize();\n"
        "setTimeout(()=>{try{const q=new URLSearchParams(location.search).get('tour'); if(q&&TOURS[q]) pick(q);}catch(e){}},0);", 1)

    # form: Netlify only when hosted there; otherwise open a pre-filled email until FORM_ENDPOINT is set
    old = "  const bodyStr=new URLSearchParams({'form-name':'waitlist',...entry,consent:'yes'}).toString();"
    assert old in body
    body = body.replace(old,
        "  if(!/netlify\\.app$/.test(location.hostname)){\n"
        f"    const sub=encodeURIComponent('Leonida Tours reservation: '+entry.tour+' on '+entry.travel_date);\n"
        "    const msgBody=encodeURIComponent(Object.entries(entry).map(([a,b])=>a+': '+b).join('\\n'));\n"
        f"    window.location.href='mailto:{EMAIL}?subject='+sub+'&body='+msgBody; return true;\n  }}\n" + old)

    # image dimensions + async decoding for CLS / LCP
    def add_dims(m):
        tag, name = m.group(0), m.group(1)
        if "width=" in tag or name not in SIZE: return tag
        extra = f' {img_attrs(name)}' + ('' if 'decoding=' in tag or 'fetchpriority' in tag else ' decoding="async"')
        return tag[:-1] + extra + ">"
    body = re.sub(r'<img src="img/([a-z]+)\.jpg"[^>]*>', add_dims, body)
    body = re.sub(r'(<img src="img/([a-z]+)\.jpg") alt=""', lambda m: f'{m.group(1)} alt="{esc(ALT.get(m.group(2), ""))}"', body)

    body = body.replace('<img src="img/${T.img}.jpg" alt="">', '<img src="img/${T.img}.jpg" alt="${T.title}">')
    # crawlable footer links
    links = "".join(f'<li><a href="tours/{SEO[k]["slug"]}/">{esc(TOURS[k]["title"])}</a></li>' for k in ORDER)
    body = body.replace('<p class="legal">', f'<nav class="foot-links" aria-label="All tours"><h2>Tours</h2><ul>{links}</ul></nav>\n    <p class="legal">', 1)
    css += ("\n.foot-links{margin:28px 0 8px}.foot-links h2{font:700 12px/1 var(--body);letter-spacing:.16em;text-transform:uppercase;color:var(--teal);margin-bottom:14px}"
            ".foot-links ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px 24px}"
            ".foot-links a{color:var(--muted);text-decoration:none;font-size:14px}.foot-links a:hover{color:var(--text)}"
            "\na.mcard{text-decoration:none}")

    title = "Leonida Tours | Miami Vice City IRL Tours, Everglades & Keys"
    desc = ("Unofficial small-group & private tours to the real South Florida spots that inspired the game: "
            "Ocean Drive, Wynwood, the Everglades & the Keys. From $79.")
    graph = [org(),
             {"@type": "WebSite", "@id": SITE_ID, "url": url(), "name": BRAND, "inLanguage": "en-US", "publisher": {"@id": ORG_ID}},
             {"@type": "WebPage", "@id": url("#webpage"), "url": url(), "name": title, "description": desc, "isPartOf": {"@id": SITE_ID},
              "about": {"@id": ORG_ID}, "inLanguage": "en-US", "dateModified": TODAY,
              "primaryImageOfPage": {"@type": "ImageObject", "url": url("img/hero.jpg"), "width": 1900, "height": 1200},
              "mainEntity": {"@id": url("#tours")}},
             {"@type": "ItemList", "@id": url("#tours"), "name": "Leonida Tours experiences", "numberOfItems": len(ORDER),
              "itemListElement": [{"@type": "ListItem", "position": i + 1, "item": trip(k, full=False)} for i, k in enumerate(ORDER)]},
             faq_schema(FAQ, url())]
    extra = ('<link rel="preload" as="image" href="img/hero.jpg" fetchpriority="high">\n' + ld(graph) +
             "\n<style>[hidden]:not([hidden=until-found i]){display:none!important}\n" + css + "</style>")
    out = ("<!doctype html>\n<html lang=\"en-US\">\n<head>\n" +
           head_common(title, desc, url(), url("assets/og-home.jpg"), "Leonida Tours: Miami skyline at sunset, unofficial IRL tours", "", extra) +
           "</head>\n<body>\n" + body + "</body>\n</html>\n")
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(out)

# ---------------------------------------------------------------- tour pages
TOUR_CSS = """:root{color-scheme:dark;--bg:#0A0910;--surface:#13111B;--surface-2:#1A1724;--line:rgba(255,255,255,.09);--line-2:rgba(255,255,255,.16);--pink:#FF5FA2;--coral:#FF8A65;--teal:#3EE6D6;--text:#F6F3FA;--muted:#A7A1B6;--sunset:linear-gradient(100deg,#FF5FA2 0%,#FF7A85 45%,#FFA66B 100%);--display:"Unbounded","Avenir Next","Helvetica Neue",Arial,sans-serif;--body:"Manrope",system-ui,-apple-system,"Segoe UI",sans-serif;--gutter:clamp(16px,4vw,48px)}
*{box-sizing:border-box}html{background:var(--bg);scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:400 16px/1.65 var(--body);-webkit-font-smoothing:antialiased;overflow-x:hidden}
img{display:block;max-width:100%;height:auto}a{color:inherit}:focus-visible{outline:2px solid var(--teal);outline-offset:3px;border-radius:8px}
.wrap{max-width:1100px;margin-inline:auto;padding-inline:var(--gutter)}
h1,h2,h3{font-family:var(--display);font-weight:700;letter-spacing:-.02em;line-height:1.08;margin:0;text-wrap:balance}
h1{font-size:clamp(32px,5.4vw,60px);font-weight:800}h2{font-size:clamp(24px,3.2vw,36px);margin-bottom:18px}h3{font-size:18px}p{margin:0}
.grad{background:var(--sunset);-webkit-background-clip:text;background-clip:text;color:transparent}
.nav{position:sticky;top:0;z-index:10;background:rgba(10,9,16,.78);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--line)}
.nav .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;height:64px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;font:800 15px/1 var(--display);letter-spacing:.02em;white-space:nowrap}
.logo i{width:32px;height:32px;border-radius:10px;background:var(--sunset);display:grid;place-items:center}.logo i svg{width:18px;height:18px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;font:700 15px/1 var(--body);text-decoration:none;padding:15px 24px;border-radius:999px;white-space:nowrap;transition:transform .2s}
.btn:hover{transform:translateY(-2px)}.btn-primary{background:var(--sunset);color:#1A0712}.btn-glass{background:rgba(255,255,255,.08);box-shadow:inset 0 0 0 1px var(--line-2)}.btn-sm{padding:11px 16px;font-size:14px}
.crumbs{font-size:13px;color:var(--muted);padding-top:20px}.crumbs ol{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:6px}.crumbs li+li::before{content:"›";margin-right:6px}.crumbs a{text-decoration:none}.crumbs a:hover{color:var(--text)}
.hero{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:clamp(24px,4vw,48px);align-items:center;padding-block:24px clamp(48px,7vw,80px)}
@media(max-width:860px){.hero{grid-template-columns:1fr}}
.hero .ph{border-radius:24px;overflow:hidden;aspect-ratio:4/3;border:1px solid var(--line)}.hero .ph img{width:100%;height:100%;object-fit:cover}
.copy{display:grid;gap:18px}.eyebrow{font:700 12px/1.3 var(--body);letter-spacing:.16em;text-transform:uppercase;color:var(--teal)}
.lede{color:#D8D1E2;font-size:17px;max-width:60ch}
.price{display:flex;align-items:baseline;gap:8px;font:700 30px/1 var(--display)}.price small{font:600 14px/1 var(--body);color:var(--muted)}
.row{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.specs{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0}@media(max-width:700px){.specs{grid-template-columns:1fr 1fr}}
.specs div{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:14px}.specs dt{font:700 11px/1 var(--body);letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}.specs dd{margin:0;font-weight:700}
section{padding-block:clamp(40px,6vw,64px);border-top:1px solid var(--line)}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:700px){.cols{grid-template-columns:1fr}}
.ticks{list-style:none;margin:0;padding:0;display:grid;gap:10px}.ticks li{padding-left:28px;position:relative;color:#D8D1E2}.ticks li::before{content:"";position:absolute;left:0;top:.45em;width:14px;height:14px;border-radius:50%;background:var(--sunset)}
.stops{list-style:none;margin:0;padding:0;display:grid;gap:12px;counter-reset:s}
.stop{display:grid;grid-template-columns:110px 1fr;gap:16px;align-items:start;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:12px}
.stop img{width:110px;height:110px;object-fit:cover;border-radius:12px}.stop .t{font:700 12px/1 var(--body);letter-spacing:.1em;color:var(--coral)}.stop p{color:var(--muted);font-size:15px;margin-top:6px}.stop .irl{font:700 11px/1.3 var(--body);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);display:block;margin-top:6px}
@media(max-width:480px){.stop{grid-template-columns:76px 1fr}.stop img{width:76px;height:76px}}
.faq details{border-bottom:1px solid var(--line);padding:16px 0}.faq summary{cursor:pointer;font:600 17px/1.4 var(--display)}.faq p{color:var(--muted);margin-top:10px}
.related{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}@media(max-width:800px){.related{grid-template-columns:1fr}}
.related a{display:block;text-decoration:none;background:var(--surface);border:1px solid var(--line);border-radius:18px;overflow:hidden}.related a:hover{border-color:var(--line-2)}.related img{aspect-ratio:16/10;object-fit:cover;width:100%}.related div{padding:14px 16px;display:grid;gap:6px}.related span{color:var(--muted);font-size:14px}
.cta{background:radial-gradient(120% 120% at 100% 0%,rgba(255,95,162,.25),transparent 55%),var(--surface);border:1px solid var(--line);border-radius:24px;padding:clamp(24px,4vw,40px);display:grid;gap:16px;justify-items:start}
footer{border-top:1px solid var(--line);padding-block:32px 48px;color:var(--muted);font-size:13px}footer .legal{margin-top:14px;max-width:90ch}footer ul{list-style:none;margin:0 0 8px;padding:0;display:flex;flex-wrap:wrap;gap:8px 20px}footer a{text-decoration:none}footer a:hover{color:var(--text)}
"""
PIN = '<svg viewBox="0 0 24 24" fill="none" stroke="#1A0712" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="10" r="3"/><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/></svg>'

def related_for(k):
    if k == "pass": return ["vc-van", "vc-boat", "airboat"]
    if k.startswith("vc-"): pool = ["pass", "vc-boat", "airboat", "vc-van", "keys"]
    else: pool = ["pass", "vc-van", "keys", "airboat", "vc-boat"]
    return [x for x in pool if x != k and x in TOURS][:3]

def build_tour(k):
    T, S, p = TOURS[k], SEO[k], "../../"
    page = turl(k)
    stops = ITIN.get(k)
    itin = ""
    if stops:
        lis = "".join(f'<li class="stop"><img src="{p}img/{s["img"]}.jpg" alt="{esc(ALT[s["img"]])}" loading="lazy" decoding="async" {img_attrs(s["img"])}>'
                      f'<div>{"<span class=t>+"+s["t"]+"</span>" if s.get("t") else ""}<h3>{i+1}. {esc(s["name"])}</h3>'
                      f'<span class="irl">Inspired · {esc(s["irl"])}</span><p>{esc(s["p"])}</p></div></li>' for i, s in enumerate(stops))
        itin = f'<section id="itinerary"><div class="wrap"><h2>Itinerary</h2><ol class="stops">{lis}</ol></div></section>'
    faqs = S["faq"] + [FAQ[0], FAQ[3], FAQ[7]]
    faq_html = "".join(f"<details{' open' if i==0 else ''}><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for i, (q, a) in enumerate(faqs))
    rel = "".join(f'<a href="{p}tours/{SEO[x]["slug"]}/"><img src="{p}img/{TOURS[x]["img"]}.jpg" alt="{esc(ALT[TOURS[x]["img"]])}" loading="lazy" decoding="async" {img_attrs(TOURS[x]["img"])}>'
                  f'<div><h3>{esc(TOURS[x]["title"])}</h3><span>{esc(TOURS[x]["dur"])} · from {money(TOURS[x]["price"])} / {esc(TOURS[x]["unit"])}</span></div></a>' for x in related_for(k))
    foot = "".join(f'<li><a href="{p}tours/{SEO[x]["slug"]}/">{esc(TOURS[x]["title"])}</a></li>' for x in ORDER)
    graph = [org(), {"@type": "WebSite", "@id": SITE_ID, "url": url(), "name": BRAND},
             {"@type": "WebPage", "@id": page + "#webpage", "url": page, "name": S["title"], "description": S["meta"],
              "isPartOf": {"@id": SITE_ID}, "inLanguage": "en-US", "dateModified": TODAY, "mainEntity": {"@id": page + "#trip"},
              "breadcrumb": {"@id": page + "#breadcrumb"},
              "primaryImageOfPage": {"@type": "ImageObject", "url": url(f"img/{T['img']}.jpg")}},
             {"@type": "BreadcrumbList", "@id": page + "#breadcrumb", "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "Home", "item": url()},
                 {"@type": "ListItem", "position": 2, "name": "Tours", "item": url("#map")},
                 {"@type": "ListItem", "position": 3, "name": T["title"], "item": page}]},
             trip(k), faq_schema(faqs, page)]
    reserve = f'{p}?tour={k}#preregister'
    out = f"""<!doctype html>
<html lang="en-US">
<head>
{head_common(S["title"], S["meta"], page, url(f"assets/og/{S['slug']}.jpg"), T["title"] + " – Leonida Tours", p,
             f'<link rel="preload" as="image" href="{p}img/{T["img"]}.jpg">' + chr(10) + ld(graph) + chr(10) + f'<link rel="stylesheet" href="{p}assets/tour.css">')}
</head>
<body>
<header class="nav"><div class="wrap"><a class="logo" href="{p}"><i>{PIN}</i>LEONIDA <span class="grad">TOURS</span></a>
<a class="btn btn-primary btn-sm" href="{reserve}">Reserve free</a></div></header>
<main>
<div class="wrap"><nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="{p}">Home</a></li><li><a href="{p}#map">Tours</a></li><li aria-current="page">{esc(T["title"])}</li></ol></nav></div>
<div class="wrap hero">
  <div class="copy">
    <span class="eyebrow">{esc(T["loc"])} · Real place: {esc(T["irl"])}</span>
    <h1>{esc(T["title"])}</h1>
    <p class="lede">{esc(S["intro"])}</p>
    <div class="price">{money(T["price"])}<small>per {esc(T["unit"])} · launch price, tours from mid-November 2026</small></div>
    <div class="row"><a class="btn btn-primary" href="{reserve}">Reserve free, pay later</a><a class="btn btn-glass" href="{p}#map">See all tours</a></div>
  </div>
  <div class="ph"><img src="{p}img/{T["img"]}.jpg" alt="{esc(ALT[T["img"]])}" fetchpriority="high" {img_attrs(T["img"])}></div>
</div>
<section><div class="wrap">
  <h2>At a glance</h2>
  <dl class="specs"><div><dt>Duration</dt><dd>{esc(T["dur"])}</dd></div><div><dt>Group</dt><dd>{esc(T["group"])}</dd></div><div><dt>Departs</dt><dd>{esc(T["departs"])}</dd></div><div><dt>Meeting point</dt><dd>{esc(T["meet"])}</dd></div></dl>
  <p class="lede" style="margin-top:22px">{esc(T["desc"])}</p>
</div></section>
<section><div class="wrap cols">
  <div><h2>What's included</h2><ul class="ticks">{"".join(f"<li>{esc(i)}</li>" for i in T["incl"])}</ul></div>
  <div><h2>Best for</h2><ul class="ticks">{"".join(f"<li>{esc(i)}</li>" for i in T["good"])}</ul></div>
</div></section>
{"" if not T.get("opts") else '<section><div class="wrap"><h2>Optional add-ons</h2><ul class="ticks">' + "".join(f"<li>{esc(o[0])} <strong>{esc(o[1])}</strong></li>" for o in T["opts"]) + "</ul></div></section>"}
{itin}
<section class="faq"><div class="wrap"><h2>Questions about this tour</h2>{faq_html}</div></section>
<section><div class="wrap cta"><span class="eyebrow">Free reservation · nothing to pay today</span><h2 style="margin:0">Reserve now. <span class="grad">Ride first.</span></h2><p class="lede">Tell us your date and group size and we'll confirm your spot before public booking opens, plus 20% off your first tour.</p><a class="btn btn-primary" href="{reserve}">Reserve {esc(T["title"])}</a></div></section>
<section><div class="wrap"><h2>You might also like</h2><div class="related">{rel}</div></div></section>
</main>
<footer><div class="wrap"><ul>{foot}</ul><p>© 2026 {BRAND} · <a href="mailto:{EMAIL}">{EMAIL}</a> · Ocean Drive, Miami Beach, FL</p><p class="legal">{DISCLAIMER}</p></div></footer>
</body>
</html>
"""
    d = os.path.join(ROOT, "tours", S["slug"]); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(out)

# ---------------------------------------------------------------- images: OG cards + icons
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def sunset(w, h):
    g = Image.new("RGB", (w, h)); px = g.load()
    stops = [(0, (255, 95, 162)), (.45, (255, 122, 133)), (1, (255, 166, 107))]
    for x in range(w):
        t = x / max(w - 1, 1)
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                u = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0]); a, b = stops[i][1], stops[i + 1][1]
                c = tuple(int(a[j] + (b[j] - a[j]) * u) for j in range(3)); break
        for y in range(h): px[x, y] = c
    return g

def pin_icon(size):
    s = size * 4
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * .24), fill=255)
    im = sunset(s, s).convert("RGBA"); im.putalpha(m)
    d = ImageDraw.Draw(im); col = (26, 7, 18, 255); lw = int(s * .075)
    cx, cy, r = s / 2, s * .43, s * .23
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=lw)
    d.line([(cx - r * .93, cy + r * .38), (cx, s * .84), (cx + r * .93, cy + r * .38)], fill=col, width=lw, joint="curve")
    d.ellipse([cx - r * .36, cy - r * .36, cx + r * .36, cy + r * .36], outline=col, width=int(lw * .85))
    return im.resize((size, size), Image.LANCZOS)

def wrap_text(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def og_card(img_name, kicker, title, sub, out):
    W, H = 1200, 630
    im = Image.open(os.path.join(ROOT, "img", img_name + ".jpg")).convert("RGB")
    sc = max(W / im.width, H / im.height); im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    im = im.crop(((im.width - W) // 2, (im.height - H) // 2, (im.width - W) // 2 + W, (im.height - H) // 2 + H))
    shade = Image.new("L", (W, H)); sp = shade.load()
    for x in range(W):
        v = int(235 * max(0, 1 - x / (W * .78)) ** .9)
        for y in range(H): sp[x, y] = v
    im = Image.composite(Image.new("RGB", (W, H), (10, 9, 16)), im, shade)
    d = ImageDraw.Draw(im)
    icon = pin_icon(64); im.paste(icon, (64, 56), icon)
    d.text((146, 74), "LEONIDA TOURS", font=ImageFont.truetype(FONT_B, 30), fill=(246, 243, 250))
    d.text((64, 176), kicker.upper(), font=ImageFont.truetype(FONT_B, 22), fill=(62, 230, 214))
    f = ImageFont.truetype(FONT_B, 62 if len(title) < 34 else 52)
    y = 216
    for line in wrap_text(d, title, f, 700)[:3]:
        d.text((64, y), line, font=f, fill=(246, 243, 250)); y += int(f.size * 1.18)
    d.rounded_rectangle([64, y + 18, 64 + 200, y + 24], radius=3, fill=(255, 95, 162))
    fs = ImageFont.truetype(FONT_R, 26)
    for line in wrap_text(d, sub, fs, 700)[:2]:
        d.text((64, y + 46), line, font=fs, fill=(226, 220, 234)); y += 36
    d.text((64, H - 64), "Unofficial IRL tours · Miami · Everglades · Florida Keys", font=ImageFont.truetype(FONT_R, 20), fill=(167, 161, 182))
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)

def build_images():
    a = os.path.join(ROOT, "assets"); os.makedirs(os.path.join(a, "og"), exist_ok=True)
    og_card("hero", "Miami · Everglades · Florida Keys", "Leonida is real. Play it IRL.",
            "Small-group & private tours to the real places that inspired the game. From $79.", os.path.join(a, "og-home.jpg"))
    for k in ORDER:
        T = TOURS[k]
        og_card(T["img"], f'{T["loc"]} · {T["irl"]}', T["title"], f'{T["dur"]} · {money(T["price"])} per {T["unit"]} · tours from mid-Nov 2026',
                os.path.join(a, "og", SEO[k]["slug"] + ".jpg"))
    for s, n in [(32, "icon-32.png"), (48, "icon-48.png"), (96, "icon-96.png"), (144, "icon-144.png"), (180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")]:
        pin_icon(s).save(os.path.join(a, n))
    pin_icon(256).save(os.path.join(ROOT, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    open(os.path.join(ROOT, "favicon.svg"), "w").write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#FF5FA2"/><stop offset=".45" stop-color="#FF7A85"/><stop offset="1" stop-color="#FFA66B"/></linearGradient></defs>'
        '<rect width="32" height="32" rx="8" fill="url(#g)"/><g transform="translate(4 4)" fill="none" stroke="#1A0712" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="10" r="3"/><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/></g></svg>\n')

# ---------------------------------------------------------------- crawl files
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot",
           "Perplexity-User", "Google-Extended", "Applebot", "Applebot-Extended", "Bingbot", "DuckAssistBot", "meta-externalagent", "CCBot"]
INDEXNOW_KEY = hashlib.sha256(("leonida-tours-indexnow" + HOST).encode()).hexdigest()[:32]

def build_crawl_files():
    pages = [(url(), "1.0", "hero")] + [(turl(k), "0.8", TOURS[k]["img"]) for k in ORDER]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for loc, pr, img in pages:
        imgs = [img] + ([s["img"] for s in LAND] if loc == url() else [])
        seen = []
        [seen.append(i) for i in imgs if i not in seen]
        im = "".join(f"<image:image><image:loc>{url('img/'+i+'.jpg')}</image:loc></image:image>" for i in seen)
        sm.append(f"  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{pr}</priority>{im}</url>")
    sm.append("</urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write("\n".join(sm) + "\n")

    rb = ["# Leonida Tours: all search engines and AI assistants are welcome.", "User-agent: *", "Allow: /", "Disallow: /_build/", ""]
    for b in AI_BOTS: rb += [f"User-agent: {b}", "Allow: /", ""]
    rb.append(f"Sitemap: {url('sitemap.xml')}")
    open(os.path.join(ROOT, "robots.txt"), "w").write("\n".join(rb) + "\n")

    lines = [f"# {BRAND}", "",
             "> Independent South Florida tour company running unofficial small-group and private tours to the real Miami, "
             "Everglades and Florida Keys places that inspired the game world of Leonida (Vice City). Tours start mid-November 2026 "
             f"(launch day {LAUNCH}). Reservations are free with nothing to pay upfront. Not affiliated with Rockstar Games or Take-Two Interactive.", "",
             f"- Home base: Ocean Drive, Miami Beach, Florida, USA", f"- Email: {EMAIL}", "- Instagram / TikTok: @leonidatours",
             f"- Reserve: {url('#preregister')}", "", "## Tours", ""]
    for k in ORDER:
        T = TOURS[k]
        lines.append(f"- [{T['title']}]({turl(k)}): {money(T['price'])} per {T['unit']}, {T['dur']}, group {T['group']}, departs {T['departs']}, "
                     f"meets {T['meet']}. Real place: {T['irl']}. {T['desc']}")
    lines += ["", "## Miami Vice City tour stops (in order)", ""]
    lines += [f"{i+1}. {s['name']} ({s['irl']}): {s['p']}" for i, s in enumerate(LAND)]
    lines += ["", "## FAQ", ""] + [f"**{q}** {a}" for q, a in FAQ]
    open(os.path.join(ROOT, "llms.txt"), "w").write("\n".join(lines) + "\n")

    open(os.path.join(ROOT, "site.webmanifest"), "w").write(json.dumps({
        "name": BRAND, "short_name": "Leonida", "description": "Unofficial IRL tours of Miami, the Everglades and the Florida Keys.",
        "start_url": "./", "scope": "./", "display": "standalone", "background_color": "#0A0910", "theme_color": "#0A0910",
        "icons": [{"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}]}, indent=2) + "\n")

    open(os.path.join(ROOT, "404.html"), "w").write(f"""<!doctype html><html lang="en-US"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Page not found | {BRAND}</title><meta name="robots" content="noindex"><link rel="icon" href="{url('favicon.svg')}" type="image/svg+xml">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;background:#0A0910;color:#F6F3FA;font:16px/1.6 system-ui,sans-serif;text-align:center;padding:24px}}
h1{{font-size:clamp(32px,6vw,56px);margin:0 0 12px}}a{{display:inline-block;margin-top:20px;padding:14px 22px;border-radius:999px;background:linear-gradient(100deg,#FF5FA2,#FFA66B);color:#1A0712;font-weight:700;text-decoration:none}}p{{color:#A7A1B6}}</style></head>
<body><main><h1>Wasted. Page not found.</h1><p>This spot isn't on the map. Respawn on the home page and pick a tour.</p><a href="{url()}">Back to Leonida Tours</a></main></body></html>
""")
    open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w").write(INDEXNOW_KEY + "\n")
    open(os.path.join(ROOT, "_config.yml"), "w").write("# GitHub Pages: publish files as-is; _build/ holds the generator.\nexclude: [_build, README.md]\ninclude: [.well-known]\n")
    cname = os.path.join(ROOT, "CNAME")
    if IS_ROOT and not HOST.endswith("github.io"): open(cname, "w").write(HOST + "\n")
    elif os.path.exists(cname): os.remove(cname)
    json.dump({"site_url": SITE, "host": HOST, "indexnow_key": INDEXNOW_KEY, "urls": [p[0] for p in pages]},
              open(os.path.join(HERE, "urls.json"), "w"), indent=2)
    os.makedirs(os.path.join(ROOT, "assets"), exist_ok=True)
    open(os.path.join(ROOT, "assets", "tour.css"), "w").write(TOUR_CSS)

if __name__ == "__main__":
    import shutil
    live = {SEO[k]["slug"] for k in ORDER}
    for d in os.listdir(os.path.join(ROOT, "tours")) if os.path.isdir(os.path.join(ROOT, "tours")) else []:
        if d not in live: shutil.rmtree(os.path.join(ROOT, "tours", d))
    for f in os.listdir(os.path.join(ROOT, "assets", "og")) if os.path.isdir(os.path.join(ROOT, "assets", "og")) else []:
        if f[:-4] not in live: os.remove(os.path.join(ROOT, "assets", "og", f))
    build_images(); build_crawl_files(); build_index()
    for k in ORDER: build_tour(k)
    print("built for", SITE)
