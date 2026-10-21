# Leonida Tours website

Static site for Leonida Tours: unofficial small-group and private tours to the real Miami, Everglades and Florida Keys places that inspired the game world of Leonida. Hosted on GitHub Pages.

## What's in here

| Path | What it is |
| --- | --- |
| `index.html` | Home page (one-page site with map, garage, itinerary, City Pass, reservation form, FAQ) |
| `tours/<slug>/` | One landing page per tour, each targeting its own search (e.g. "Everglades airboat tour from Miami") |
| `img/`, `assets/` | Photos, social share cards (`assets/og/`), icons, tour-page CSS |
| `sitemap.xml` | All pages plus image entries, for Google and Bing |
| `robots.txt` | Allows all search engines and AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended…) |
| `llms.txt` | Plain-text summary of the business, tours, prices and FAQ for ChatGPT, Claude, Perplexity and other AI assistants |
| `site.webmanifest`, `favicon.svg` | App icon and theme |
| `404.html` | Not-found page (noindex) |
| `<key>.txt` + `.github/workflows/indexnow.yml` | IndexNow: pings Bing/Yandex automatically after every push |
| `_build/` | The generator. Not published. |

### SEO built in

- Unique `<title>`, meta description, canonical URL, Open Graph and Twitter cards on every page, with a custom 1200×630 share image per tour.
- JSON-LD structured data: `TravelAgency` (business), `WebSite`, `WebPage`, `TouristTrip` with `Offer` prices for every tour, itinerary stops as `TouristAttraction`, `BreadcrumbList`, `FAQPage`.
- Tour cards, itinerary stops and footer links are real HTML links, so crawlers and AI bots that don't run JavaScript still see every tour.
- Image `width`/`height`, descriptive alt text, lazy loading and hero preload for Core Web Vitals.
- Geo meta tags for Miami Beach.

## Editing

Edit `_build/index.src.html` (the design) or the tour copy in `_build/build.py` / `_build/data.json`, then rebuild:

```bash
SITE_URL=https://leonidatours.com python3 _build/build.py
```

`SITE_URL` must be the address the site is live at. If it's your own domain, the build writes `CNAME`; for a `github.io` address it doesn't.

## Go-live checklist

1. **GitHub Pages:** repo Settings → Pages → Source: *Deploy from a branch*, branch `main`, folder `/ (root)`.
2. **Custom domain (recommended):** at your domain registrar, add four `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`, and a `CNAME` for `www` → `<your-username>.github.io`. Then tick *Enforce HTTPS* in Pages settings. `robots.txt` and the sitemap only count at a domain root, so a custom domain matters for SEO.
3. **Enquiry form:** the site publishes no phone number, no mailbox and no street address. Both the home reservation form and `/contact/` send the visitor's details to the team by email. To have the site post the message for you, create a free form at formspree.io (or similar) and build with `CONTACT_ENDPOINT=https://formspree.io/f/yourid python3 _build/build.py`; the recipient then lives in that service and never reaches the browser. With no endpoint set, the form hands the message to the visitor's own mail client, with the team address assembled at runtime so it is not published in the page source. The exact pickup point is sent with the booking, never printed on the site.
4. **Google Search Console:** add the domain property, verify by DNS, then submit `sitemap.xml`.
5. **Bing Webmaster Tools:** import from Search Console (one click) and submit `sitemap.xml`. Bing powers ChatGPT search and Copilot results.
6. **Google Business Profile:** create one as a tour operator in Miami Beach once you have an address you can verify. It's the biggest lever for "tours near me" searches.
7. **Social links:** the schema lists instagram.com/leonidatours and tiktok.com/@leonidatours; update `SOCIAL` in `build.py` if the handles differ.
