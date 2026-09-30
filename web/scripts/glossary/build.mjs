// Generates the glossary in English (/glossary/, imperial units) and Georgian (/ka/glossary/, metric units):
// one page per term, a hub per language, hreflang pairs between them, and sitemap entries.
// Run with `npm run glossary` (part of `npm run build`, after gen-seo writes sitemap.xml).
import { mkdir, readFile, writeFile, rm } from "node:fs/promises";
import { computeFacts } from "./facts.mjs";
import termsEn, { CATEGORIES as CAT_EN } from "./terms.mjs";
import termsKa, { CATEGORIES as CAT_KA } from "./terms.ka.mjs";

const SITE = "https://ballistics.ge";
const PUBLIC = new URL("../../public/", import.meta.url).pathname;
const SITEMAP = PUBLIC + "sitemap.xml";
// Bump UPDATED when the content changes; rebuilding alone must not fake freshness.
const PUBLISHED = { en: "2026-09-30", ka: "2026-09-30" };
const UPDATED = { en: "2026-09-30", ka: "2026-09-30" };

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const strip = (h) => h.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
const words = (h) => strip(h).split(" ").filter(Boolean).length;
const n = (x, d = 1) => (Math.abs(x) < 0.5 * 10 ** -d ? 0 : x).toFixed(d);

const L = {
  en: {
    dir: "glossary/", locale: "en_US", terms: termsEn, cats: CAT_EN, metric: false, minWords: 400,
    nav: `<a href="/">Calculator</a> · <a href="/ballistics/">Charts</a> · <a href="/glossary/">Glossary</a> · <a href="/ka/glossary/" hreflang="ka" lang="ka">ქართული</a>`,
    skip: "Skip to content", home: "Home", glossary: "Glossary", faq: "FAQ", related: "Related terms", updated: "Updated",
    cta: "Open the free ballistic calculator", ctaNote: "Works offline in your phone's browser. Add it to your home screen to use at the range.",
    foot: `ballistics.ge · free ballistic calculator that works offline · <a href="/ballistics/">Charts</a> · <a href="/terms/">Terms</a> · <a href="/privacy/">Privacy</a><br>Numbers on this page are calculated with the same solver the calculator uses (RK4 point-mass, G1/G7 drag, validated against py_ballisticcalc).`,
    date: (d) => new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
    hubTitle: "Long Range Shooting Glossary: Ballistics Terms Explained",
    hubDesc: "Plain-English explanations of MOA, MIL, FFP, ballistic coefficient, spin drift, density altitude, zeroing and more, with charts calculated for real loads.",
    hubH1: "Long range shooting glossary",
    hubIntro: "Every term a ballistic calculator asks for, explained in plain English. Each page gives the short answer first, then the details, a worked example calculated for a real load, and the questions shooters usually ask next.",
    setName: "ballistics.ge shooting glossary",
    th: ["Yards", "Drop (in)", "Up (MOA)", "Up (MIL)", "Wind (in)", "Wind (MIL)", "Velocity (fps)", "Energy (ft·lb)"],
    caption: (l, F) => `${esc(l.name)}: ${Math.round(l.muzzleVelocityMps / 0.3048)} fps muzzle velocity, ${l.bcG7 ? `G7 BC ${l.bcG7}` : `G1 BC ${l.bcG1}`}, ${l.zeroYd}-yard zero, ${(l.sightHeightMm / 25.4).toFixed(1)}" sight height, sea-level standard atmosphere (59°F, 29.92 inHg). Wind is a full-value 10 mph crosswind. Calculated with the ballistics.ge solver.`,
  },
  ka: {
    // Georgian is agglutinative: the same content runs ~25% fewer words than English.
    dir: "ka/glossary/", locale: "ka_GE", terms: termsKa, cats: CAT_KA, metric: true, minWords: 240,
    nav: `<a href="/">კალკულატორი</a> · <a href="/ka/glossary/">ლექსიკონი</a> · <a href="/blog/">ბლოგი</a> · <a href="/glossary/" hreflang="en" lang="en">English</a>`,
    skip: "შინაარსზე გადასვლა", home: "მთავარი", glossary: "ლექსიკონი", faq: "ხშირი კითხვები", related: "დაკავშირებული ტერმინები", updated: "განახლდა",
    cta: "გახსენით უფასო ბალისტიკური კალკულატორი", ctaNote: "მუშაობს ოფლაინ, ტელეფონის ბრაუზერში. დაამატეთ მთავარ ეკრანზე და გამოიყენეთ სასროლეთზე.",
    foot: `ballistics.ge · უფასო ბალისტიკური კალკულატორი, რომელიც ოფლაინ მუშაობს · <a href="/blog/">ბლოგი</a> · <a href="/terms/">წესები</a> · <a href="/privacy/">კონფიდენციალურობა</a><br>ამ გვერდის ყველა რიცხვი გამოთვლილია იმავე მოდელით, რასაც კალკულატორი იყენებს (RK4 წერტილოვანი მასა, G1/G7 წინაღობა, შემოწმებულია py_ballisticcalc-ით).`,
    date: (d) => { const [y, m, day] = d.split("-").map(Number); return `${day} ${["იანვარი", "თებერვალი", "მარტი", "აპრილი", "მაისი", "ივნისი", "ივლისი", "აგვისტო", "სექტემბერი", "ოქტომბერი", "ნოემბერი", "დეკემბერი"][m - 1]}, ${y}`; },
    hubTitle: "სროლის ლექსიკონი: ბალისტიკის ტერმინები მარტივად",
    hubDesc: "MOA, MIL, FFP, ბალისტიკური კოეფიციენტი, ნულზე მიყვანა, ქარი, ბრუნვითი გადახრა და სხვა ტერმინები მარტივად ახსნილი, რეალური ვაზნების ცხრილებით.",
    hubH1: "სროლის ლექსიკონი",
    hubIntro: "ყველა ტერმინი, რასაც ბალისტიკური კალკულატორი გეკითხებათ, მარტივ ქართულად. თითო გვერდზე ჯერ მოკლე პასუხია, შემდეგ დეტალები, რეალური ვაზნისთვის გამოთვლილი მაგალითი მეტრულ ერთეულებში და ხშირი კითხვები.",
    setName: "ballistics.ge სროლის ლექსიკონი",
    th: ["მეტრი", "დაცემა (სმ)", "ზემოთ (MOA)", "ზემოთ (MIL)", "ქარი (სმ)", "ქარი (MIL)", "სიჩქარე (მ/წმ)", "ენერგია (J)"],
    caption: (l) => `${esc(l.name)}: საწყისი სიჩქარე ${Math.round(l.muzzleVelocityMps)} მ/წმ, ${l.bcG7 ? `G7 BC ${l.bcG7}` : `G1 BC ${l.bcG1}`}, ნული ${l.zeroYd} მ, ოპტიკის სიმაღლე ${Math.round(l.sightHeightMm / 10 * 10) / 10} სმ, სტანდარტული ატმოსფერო ზღვის დონეზე (15 °C, 1013 მბარი). ქარი: 5 მ/წმ, სრული მნიშვნელობა (90°). გამოთვლილია ballistics.ge-ის მოდელით.`,
  },
};

const helpers = (lang, F) => ({
  F, n, lang,
  /** Drop/wind table for a reference load, in the page language's units. */
  dropTable(key, caption) {
    const l = F.loads[key], t = F.tables[key], metric = F.metric;
    const rows = t.map((r) => `<tr><td>${r.yd}</td><td>${n(r.dropIn, metric ? 0 : 1)}</td><td>${n(-r.moa)}</td><td>${n(-r.mil)}</td><td>${n(Math.abs(r.windIn), metric ? 0 : 1)}</td><td>${n(Math.abs(r.windMil))}</td><td>${Math.round(r.fps)}</td><td>${Math.round(r.ftlb)}</td></tr>`).join("");
    return `<figure class="tbl"><div class="scroll"><table><thead><tr>${L[lang].th.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>
<figcaption>${caption ?? L[lang].caption(l, F)}</figcaption></figure>`;
  },
  table(head, rows, caption) {
    return `<figure class="tbl"><div class="scroll"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>${caption ? `<figcaption>${caption}</figcaption>` : ""}</figure>`;
  },
});

const FACTS = { en: await computeFacts({ metric: false }), ka: await computeFacts({ metric: true }) };
const LISTS = Object.fromEntries(Object.keys(L).map((lang) => [lang, L[lang].terms(helpers(lang, FACTS[lang]))]));
const BY = Object.fromEntries(Object.entries(LISTS).map(([lang, list]) => [lang, Object.fromEntries(list.map((t) => [t.slug, t]))]));
for (const [lang, list] of Object.entries(LISTS))
  for (const t of list) for (const r of t.related) if (!BY[lang][r]) throw new Error(`${lang}/${t.slug}: unknown related term ${r}`);

const url = (lang, slug) => `${SITE}/${L[lang].dir}${slug ? slug + "/" : ""}`;
/** hreflang links for a slug (or the hub when slug is empty) in every language that has it. */
const alternates = (slug) => {
  const langs = Object.keys(L).filter((lang) => !slug || BY[lang][slug]);
  if (langs.length < 2) return "";
  return langs.map((lang) => `<link rel="alternate" hreflang="${lang}" href="${url(lang, slug)}">`).join("") + (langs.includes("en") ? `<link rel="alternate" hreflang="x-default" href="${url("en", slug)}">` : "");
};

const head = (lang, { title, description, href, type, ld, slug }) => `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(description)}"><link rel="canonical" href="${href}">${alternates(slug)}
<meta property="og:type" content="${type}"><meta property="og:site_name" content="ballistics.ge"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${href}"><meta property="og:image" content="${SITE}/brand/og-${lang}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:locale" content="${L[lang].locale}"><meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/blog/blog.css"><link rel="stylesheet" href="/glossary/glossary.css">
<link rel="icon" type="image/png" sizes="32x32" href="/icons/ballistics-b-32.png"><link rel="apple-touch-icon" sizes="180x180" href="/icons/ballistics-b-180.png">
<script type="application/ld+json">${JSON.stringify(ld)}</script></head><body><a class="skip" href="#content">${L[lang].skip}</a>
<header><a href="/" class="brand" aria-label="ballistics.ge"><img src="/brand/ballistics-logo.png" alt="ballistics.ge" width="1200" height="520"></a><nav aria-label="Main">${L[lang].nav}</nav></header>`;
const foot = (lang) => `<footer>${L[lang].foot}</footer></body></html>`;
const org = { "@type": "Organization", name: "ballistics.ge", url: `${SITE}/`, logo: `${SITE}/brand/ballistics-logo.png` };

function page(lang, t) {
  const S = L[lang], href = url(lang, t.slug), by = BY[lang];
  const body = t.sections.map((s) => `<section><h2>${s.h}</h2>${s.html}</section>`).join("\n");
  const faq = `<section><h2>${S.faq}</h2>${t.faq.map((f) => `<h3>${f.q}</h3><p>${f.a}</p>`).join("")}</section>`;
  const cta = `<p class="cta"><a class="btn" href="/">${t.cta ?? S.cta} →</a><br><span class="meta">${S.ctaNote}</span></p>`;
  const related = `<nav aria-label="${S.related}"><h2>${S.related}</h2><ul>${t.related.map((r) => `<li><a href="/${S.dir}${r}/">${by[r].h1}</a>: ${by[r].short}</li>`).join("")}</ul></nav>`;
  const ld = { "@context": "https://schema.org", "@graph": [
    { "@type": "Article", headline: t.h1, description: t.description, inLanguage: lang, datePublished: PUBLISHED[lang], dateModified: UPDATED[lang], mainEntityOfPage: href, image: `${SITE}/brand/og-${lang}.png`, author: org, publisher: org, about: { "@type": "DefinedTerm", name: t.term, description: strip(t.answer), inDefinedTermSet: url(lang) } },
    { "@type": "FAQPage", inLanguage: lang, mainEntity: t.faq.map((f) => ({ "@type": "Question", name: strip(f.q), acceptedAnswer: { "@type": "Answer", text: strip(f.a) } })) },
    { "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: S.home, item: `${SITE}/` }, { "@type": "ListItem", position: 2, name: S.glossary, item: url(lang) }, { "@type": "ListItem", position: 3, name: t.h1, item: href }] },
  ] };
  const html = head(lang, { title: t.title, description: t.description, href, type: "article", ld, slug: t.slug }) +
    `<main id="content"><p class="meta"><a href="/">${S.home}</a> / <a href="/${S.dir}">${S.glossary}</a> / ${esc(t.term)}</p><article><h1>${t.h1}</h1>
<div class="answer"><p>${t.answer}</p></div><p class="meta">${S.updated} <time datetime="${UPDATED[lang]}">${S.date(UPDATED[lang])}</time> · ballistics.ge</p>
${body}\n${cta}\n${faq}</article>${related}</main>` + foot(lang);
  return { html, words: words(t.answer + body + faq) };
}

function hub(lang) {
  const S = L[lang], list = LISTS[lang], href = url(lang);
  const groups = S.cats.map((c) => `<section><h2>${c}</h2><ul>${list.filter((t) => t.cat === c).map((t) => `<li><a href="/${S.dir}${t.slug}/">${t.h1}</a>: ${t.short}</li>`).join("")}</ul></section>`).join("");
  const ld = { "@context": "https://schema.org", "@graph": [
    { "@type": "DefinedTermSet", name: S.setName, inLanguage: lang, url: href, hasDefinedTerm: list.map((t) => ({ "@type": "DefinedTerm", name: t.term, url: url(lang, t.slug) })) },
    { "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: S.home, item: `${SITE}/` }, { "@type": "ListItem", position: 2, name: S.glossary, item: href }] },
  ] };
  return head(lang, { title: S.hubTitle, description: S.hubDesc, href, type: "website", ld, slug: "" }) + `<main id="content"><h1>${S.hubH1}</h1>
<p class="intro">${S.hubIntro}</p>
${groups}<p class="cta"><a class="btn" href="/">${S.cta} →</a></p></main>` + foot(lang);
}

const report = [];
const sitemap = [];
for (const lang of Object.keys(L)) {
  const S = L[lang], OUT = PUBLIC + S.dir;
  await rm(OUT, { recursive: true, force: true });
  await mkdir(OUT, { recursive: true });
  if (lang === "en") await writeFile(OUT + "glossary.css", await readFile(new URL("glossary.css", import.meta.url)));
  for (const t of LISTS[lang]) {
    const { html, words: w } = page(lang, t);
    if (t.title.length > 70) console.warn(`! ${lang} title ${t.title.length} chars: ${t.slug}`);
    if (t.description.length > 160 || t.description.length < 100) console.warn(`! ${lang} description ${t.description.length} chars: ${t.slug}`);
    if (w < S.minWords) console.warn(`! ${lang} only ${w} words: ${t.slug}`);
    await mkdir(OUT + t.slug, { recursive: true });
    await writeFile(OUT + t.slug + "/index.html", html);
    report.push(`${lang} ${String(w).padStart(5)}  ${t.slug}`);
    sitemap.push(`<url><loc>${url(lang, t.slug)}</loc><lastmod>${UPDATED[lang]}</lastmod></url>`);
  }
  await writeFile(OUT + "index.html", hub(lang));
  sitemap.push(`<url><loc>${url(lang)}</loc><lastmod>${UPDATED[lang]}</lastmod><priority>0.8</priority></url>`);
}

let sm = await readFile(SITEMAP, "utf8").catch(() => null);
if (!sm) { console.log(`${report.length} pages written (no sitemap.xml yet; run gen-seo first).`); process.exit(0); }
sm = sm.replace(/<url><loc>https:\/\/ballistics\.ge\/(?:ka\/)?glossary\/[^<]*<\/loc>.*?<\/url>/g, "");
sm = sm.replace("</urlset>", sitemap.join("") + "</urlset>");
await writeFile(SITEMAP, sm);
console.log(report.join("\n") + `\n${report.length} pages written.`);
