"""
ballistics.ge - SEO helpers.

Streamlit renders a single-page app and only lets us set <title> and the
favicon. Google's crawler executes JavaScript, so we inject the remaining
head tags (description, canonical, Open Graph, language) into the parent
document from a zero-height component, and render a visible, crawlable
heading + about text in the page itself (see render_about()).
Version: 1.0.0
"""
import html
import json

import streamlit as st
import streamlit.components.v1 as components

from config import APP_NAME, SITE_URL, TAGLINE

DESCRIPTION = (
    "Free online ballistic calculator: elevation and windage in MRAD or MOA for .308, "
    ".223, 6.5 Creedmoor and .22 LR, with live weather, dope card, reticle holdover and "
    "phone compass. ბალისტიკური კალკულატორი ზუსტი სროლისთვის."
)
KEYWORDS = (
    "ballistic calculator, ballistics, MRAD, MOA, dope card, .308 Win, .22 LR, 6.5 Creedmoor, "
    "long range shooting, holdover, windage, Strelok alternative, ბალისტიკური კალკულატორი, "
    "ბალისტიკა, სროლა, ტყვიის ვარდნა, ქარის შესწორება, საქართველო"
)


def inject_head_tags() -> None:
    """Add SEO meta tags to the parent document head (idempotent)."""
    tags = [
        ("name", "description", DESCRIPTION),
        ("name", "keywords", KEYWORDS),
        ("name", "robots", "index,follow"),
        ("property", "og:type", "website"),
        ("property", "og:site_name", APP_NAME),
        ("property", "og:title", f"{APP_NAME} — {TAGLINE}"),
        ("property", "og:description", DESCRIPTION),
        ("property", "og:url", SITE_URL + "/"),
        ("property", "og:locale", "ka_GE"),
        ("property", "og:locale:alternate", "en_US"),
        ("name", "twitter:card", "summary"),
        ("name", "twitter:title", f"{APP_NAME} — {TAGLINE}"),
        ("name", "twitter:description", DESCRIPTION),
    ]
    ld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": APP_NAME,
        "url": SITE_URL + "/",
        "description": DESCRIPTION,
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Any (web)",
        "inLanguage": ["ka", "en"],
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "keywords": KEYWORDS,
    }
    js = f"""
    <script>
    (function () {{
      try {{
        var d = window.parent.document;
        if (d.getElementById('bge-seo')) return;
        var tags = {json.dumps(tags)};
        tags.forEach(function (t) {{
          var m = d.createElement('meta'); m.setAttribute(t[0], t[1]); m.setAttribute('content', t[2]);
          m.setAttribute('data-bge', '1'); d.head.appendChild(m);
        }});
        var link = d.createElement('link'); link.rel = 'canonical'; link.href = {json.dumps(SITE_URL + '/')};
        d.head.appendChild(link);
        var ld = d.createElement('script'); ld.type = 'application/ld+json'; ld.id = 'bge-seo';
        ld.text = {json.dumps(json.dumps(ld))};
        d.head.appendChild(ld);
        d.documentElement.setAttribute('lang', 'ka');
      }} catch (e) {{}}
    }})();
    </script>
    """
    components.html(js, height=0)


def render_header() -> None:
    """Visible H1 + tagline: crawlable text at the top of the page."""
    st.markdown(
        f'<h1 style="margin:0 0 2px 0;font-size:1.6rem;">🎯 {html.escape(APP_NAME)}</h1>'
        f'<p style="margin:0 0 10px 0;color:#9a9a9a;font-size:0.95rem;">{html.escape(TAGLINE)}</p>',
        unsafe_allow_html=True,
    )


def render_about() -> None:
    """Indexable description of the app, Georgian first, then English."""
    with st.expander("ℹ️ ballistics.ge — რა არის ეს / About", expanded=False):
        st.markdown(
            """
**ballistics.ge** — უფასო ონლაინ ბალისტიკური კალკულატორი ზუსტი და შორ მანძილზე სროლისთვის.
ითვლის ვერტიკალურ (elevation) და ჰორიზონტალურ (windage) შესწორებას MRAD-სა და MOA-ში,
ოპტიკის click-ებში, ნებისმიერი ვაზნისთვის: .308 Win, .223 Rem / 5.56, 6.5 Creedmoor, .22 LR
(მათ შორის სუბსონიკური), .300 Win Mag, .338 Lapua და სხვა.

- **Calculator** — მანძილი, ქარი, ტემპერატურა, წნევა, სიმაღლე, დახრის კუთხე, cant; ამინდის
  ავტომატური სინქრონიზაცია შენი ლოკაციისთვის; ტელეფონის კომპასი სროლის მიმართულებისთვის.
- **Dope Card** — დაბეჭდვადი ცხრილი ყველა მანძილზე, CSV ექსპორტით.
- **Reticle** — holdover-ის წერტილი MIL-Dot / TMR ბადეზე. **Turret** — ბარაბნის პოზიცია.
- **Range Est.** — მანძილის შეფასება რეტიკლით (mil-relation).
- **True MV** — რეალური დაცემით ლულის სიჩქარის დაზუსტება (truing).
- 190+ ვაზნისა და ტყვიის ბიბლიოთეკა (Lapua, Sierra, Hornady, Berger, PPU, S&B, GECO, Norma, CCI, Eley…).

ფიზიკა: RK4 point-mass solver, G1/G7 და custom drag ცხრილები (BRL/JBM), spin drift, aero jump,
Coriolis, Miller სტაბილურობა, ფხვნილის ტემპერატურული მგრძნობელობა. შემოწმებულია
py_ballisticcalc-სა და JBM-ის ცხრილებთან.

---

**ballistics.ge** is a free online ballistic calculator for precision and long-range shooting.
It gives elevation and windage in MRAD or MOA and in scope clicks for any cartridge — .308 Win,
.223 / 5.56, 6.5 Creedmoor, .22 LR (subsonic included), .300 Win Mag, .338 Lapua and more — with
live weather for your location, phone-compass heading, a printable dope card, reticle holdover,
turret view, mil-relation rangefinder, muzzle-velocity truing and a 190+ bullet library.
Physics: RK4 point-mass solver, G1/G7/custom drag, spin drift, aerodynamic jump, Coriolis,
Miller stability, powder temperature sensitivity, validated against py_ballisticcalc and JBM.
            """
        )
