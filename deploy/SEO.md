# ballistics.ge — SEO & Google Search Console checklist

## What the app already does
- `<title>`: "ballistics.ge — Ballistic Calculator | MRAD, MOA, .308, .22 LR"
- Injected into `<head>` on load (`core/seo.py`): meta description & keywords (KA+EN),
  canonical `https://ballistics.ge/`, Open Graph + Twitter cards, `lang="ka"`,
  JSON-LD `WebApplication` schema.
- Visible H1 + tagline and a bilingual "About" section with the keywords Google needs.

## One-time setup (≈15 min)
1. **Cloudflare Worker** for `robots.txt` / `sitemap.xml`: paste `deploy/cloudflare-worker-seo.js`,
   add routes `ballistics.ge/robots.txt` and `ballistics.ge/sitemap.xml` (only those two).
   Check: https://ballistics.ge/robots.txt and https://ballistics.ge/sitemap.xml open.
2. **Search Console** → Add property → *Domain* `ballistics.ge` → verify via **DNS TXT**
   (Cloudflare DNS → add the TXT record Google shows, name `@`). Domain property covers
   http/https and www in one go.
3. Search Console → **Sitemaps** → submit `https://ballistics.ge/sitemap.xml`.
4. Search Console → **URL inspection** → `https://ballistics.ge/` → **Request indexing**.
   Use "Test live URL" and look at the rendered HTML: the H1, About text and the injected
   meta description must be present (Googlebot renders JavaScript).
5. Cloudflare → SSL/TLS → **Always Use HTTPS** on; Rules → redirect `www.ballistics.ge/*`
   → `https://ballistics.ge/$1` (301) so there is one canonical host.
6. The old strelokai.streamlit.app mirror: delete it once ballistics.ge is stable so
   Google doesn't see duplicate content.

## Getting ahead in results
- Single-page apps are thin for crawlers: the About text is the main ranking content. Add a
  few paragraphs over time (how to zero, MRAD vs MOA, .22 LR subsonic drop table) — each
  one is a keyword set.
- Get 3–5 real links: Georgian shooting clubs / Facebook groups / forums (snipershide,
  accurateshooter "free tools" threads), and the GitHub README.
- Target Georgian queries first (low competition): "ბალისტიკური კალკულატორი",
  "სნაიპერული სროლა კალკულატორი", ".308 ვარდნის ცხრილი". English "ballistic calculator"
  is dominated by Hornady/JBM/Applied Ballistics; aim for long-tail
  ("free online ballistic calculator MRAD dope card", "22lr subsonic ballistic calculator").
- Re-check Search Console → Performance after 2–4 weeks; indexing of a new .ge domain
  usually takes days, ranking movement weeks.
