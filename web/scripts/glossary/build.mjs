// Generates the English glossary: /glossary/<slug>/index.html for every term, the /glossary/ hub,
// and the sitemap entries. Run with `npm run glossary`; output is committed to web/public.
import { mkdir, readFile, writeFile, rm } from "node:fs/promises";
import { computeFacts } from "./facts.mjs";
import terms, { CATEGORIES } from "./terms.mjs";

const SITE = "https://ballistics.ge";
const OUT = new URL("../../public/glossary/", import.meta.url).pathname;
const SITEMAP = new URL("../../public/sitemap.xml", import.meta.url).pathname;
const TODAY = new Date().toISOString().slice(0, 10);
const PUBLISHED = "2026-09-30";

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const strip = (h) => h.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
const words = (h) => strip(h).split(" ").filter(Boolean).length;

const F = await computeFacts();
const n = (x, d = 1) => (Math.abs(x) < 0.5 * 10 ** -d ? 0 : x).toFixed(d);
const H = {
  F, n,
  /** Drop/wind table for a reference load. */
  dropTable(key, caption) {
    const l = F.loads[key], t = F.tables[key];
    const rows = t.map((r) => `<tr><td>${r.yd}</td><td>${n(r.dropIn)}</td><td>${n(-r.moa)}</td><td>${n(-r.mil)}</td><td>${n(Math.abs(r.windIn))}</td><td>${n(Math.abs(r.windMil))}</td><td>${Math.round(r.fps)}</td><td>${Math.round(r.ftlb)}</td></tr>`).join("");
    return `<figure class="tbl"><div class="scroll"><table><thead><tr><th>Yards</th><th>Drop (in)</th><th>Up (MOA)</th><th>Up (MIL)</th><th>Wind (in)</th><th>Wind (MIL)</th><th>Velocity (fps)</th><th>Energy (ft·lb)</th></tr></thead><tbody>${rows}</tbody></table></div>
<figcaption>${caption ?? `${esc(l.name)}: ${Math.round(l.muzzleVelocityMps / 0.3048)} fps muzzle velocity, ${l.bcG7 ? `G7 BC ${l.bcG7}` : `G1 BC ${l.bcG1}`}, ${l.zeroYd}-yard zero, ${(l.sightHeightMm / 25.4).toFixed(1)}" sight height, sea-level standard atmosphere (59°F, 29.92 inHg). Wind is a full-value 10 mph crosswind. Calculated with the ballistics.ge solver.`}</figcaption></figure>`;
  },
  table(head, rows, caption) {
    return `<figure class="tbl"><div class="scroll"><table><thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table></div>${caption ? `<figcaption>${caption}</figcaption>` : ""}</figure>`;
  },
};

const list = terms(H);
const bySlug = Object.fromEntries(list.map((t) => [t.slug, t]));
for (const t of list) for (const r of t.related) if (!bySlug[r]) throw new Error(`${t.slug}: unknown related term ${r}`);

const head = ({ title, description, url, type, ld }) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title><meta name="description" content="${esc(description)}"><link rel="canonical" href="${url}">
<meta property="og:type" content="${type}"><meta property="og:site_name" content="ballistics.ge"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${url}"><meta property="og:image" content="${SITE}/brand/ballistics-logo.png"><meta property="og:locale" content="en_US"><meta name="twitter:card" content="summary">
<link rel="stylesheet" href="/blog/blog.css"><link rel="stylesheet" href="/glossary/glossary.css">
<link rel="icon" type="image/png" sizes="32x32" href="/icons/ballistics-b-32.png"><link rel="apple-touch-icon" sizes="180x180" href="/icons/ballistics-b-180.png">
<script type="application/ld+json">${JSON.stringify(ld)}</script></head><body><a class="skip" href="#content">Skip to content</a>
<header><a href="/" class="brand" aria-label="ballistics.ge"><img src="/brand/ballistics-logo.png" alt="ballistics.ge" width="1200" height="520"></a><nav aria-label="Main"><a href="/">Calculator</a> · <a href="/glossary/">Glossary</a> · <a href="/blog/" hreflang="ka">Blog (KA)</a></nav></header>`;
const foot = `<footer>ballistics.ge · free ballistic calculator that works offline<br>Numbers on this page are calculated with the same solver the calculator uses (RK4 point-mass, G1/G7 drag, validated against py_ballisticcalc).</footer></body></html>`;
const org = { "@type": "Organization", name: "ballistics.ge", url: `${SITE}/`, logo: `${SITE}/brand/ballistics-logo.png` };

function page(t) {
  const url = `${SITE}/glossary/${t.slug}/`;
  const body = t.sections.map((s) => `<section><h2>${s.h}</h2>${s.html}</section>`).join("\n");
  const faq = `<section><h2>FAQ</h2>${t.faq.map((f) => `<h3>${f.q}</h3><p>${f.a}</p>`).join("")}</section>`;
  const cta = `<p class="cta"><a class="btn" href="/">${t.cta ?? "Open the free ballistic calculator"} →</a><br><span class="meta">Works offline in your phone's browser. Add it to your home screen to use at the range.</span></p>`;
  const related = `<nav aria-label="Related terms"><h2>Related terms</h2><ul>${t.related.map((r) => `<li><a href="/glossary/${r}/">${bySlug[r].h1}</a>: ${bySlug[r].short}</li>`).join("")}</ul></nav>`;
  const ld = { "@context": "https://schema.org", "@graph": [
    { "@type": "Article", headline: t.h1, description: t.description, inLanguage: "en", datePublished: PUBLISHED, dateModified: TODAY, mainEntityOfPage: url, image: `${SITE}/brand/ballistics-logo.png`, author: org, publisher: org, about: { "@type": "DefinedTerm", name: t.term, description: strip(t.answer), inDefinedTermSet: `${SITE}/glossary/` } },
    { "@type": "FAQPage", mainEntity: t.faq.map((f) => ({ "@type": "Question", name: strip(f.q), acceptedAnswer: { "@type": "Answer", text: strip(f.a) } })) },
    { "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "Home", item: `${SITE}/` }, { "@type": "ListItem", position: 2, name: "Glossary", item: `${SITE}/glossary/` }, { "@type": "ListItem", position: 3, name: t.h1, item: url }] },
  ] };
  const html = head({ title: t.title, description: t.description, url, type: "article", ld }) +
    `<main id="content"><p class="meta"><a href="/">Home</a> / <a href="/glossary/">Glossary</a> / ${esc(t.term)}</p><article><h1>${t.h1}</h1>
<div class="answer"><p>${t.answer}</p></div><p class="meta">Updated <time datetime="${TODAY}">${new Date(TODAY).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</time> · ballistics.ge</p>
${body}\n${cta}\n${faq}</article>${related}</main>` + foot;
  return { html, words: words(t.answer + body + faq) };
}

function hub() {
  const url = `${SITE}/glossary/`;
  const title = "Long Range Shooting Glossary: Ballistics Terms Explained";
  const description = "Plain-English explanations of MOA, MIL, FFP, ballistic coefficient, spin drift, density altitude, zeroing and more, with charts calculated for real loads.";
  const groups = CATEGORIES.map((c) => `<section><h2>${c}</h2><ul>${list.filter((t) => t.cat === c).map((t) => `<li><a href="/glossary/${t.slug}/">${t.h1}</a>: ${t.short}</li>`).join("")}</ul></section>`).join("");
  const ld = { "@context": "https://schema.org", "@graph": [
    { "@type": "DefinedTermSet", name: "ballistics.ge shooting glossary", url, hasDefinedTerm: list.map((t) => ({ "@type": "DefinedTerm", name: t.term, url: `${url}${t.slug}/` })) },
    { "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "Home", item: `${SITE}/` }, { "@type": "ListItem", position: 2, name: "Glossary", item: url }] },
  ] };
  return head({ title, description, url, type: "website", ld }) + `<main id="content"><h1>Long range shooting glossary</h1>
<p class="intro">Every term a ballistic calculator asks for, explained in plain English. Each page gives the short answer first, then the details, a worked example calculated for a real load, and the questions shooters usually ask next.</p>
${groups}<p class="cta"><a class="btn" href="/">Open the free ballistic calculator →</a></p></main>` + foot;
}

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });
await writeFile(OUT + "glossary.css", await readFile(new URL("glossary.css", import.meta.url)));
const report = [];
for (const t of list) {
  const { html, words: w } = page(t);
  if (t.title.length > 65) console.warn(`! title ${t.title.length} chars: ${t.slug}`);
  if (t.description.length > 160 || t.description.length < 110) console.warn(`! description ${t.description.length} chars: ${t.slug}`);
  if (w < 400) console.warn(`! only ${w} words: ${t.slug}`);
  await mkdir(OUT + t.slug, { recursive: true });
  await writeFile(OUT + t.slug + "/index.html", html);
  report.push(`${String(w).padStart(5)}  ${t.slug}`);
}
await writeFile(OUT + "index.html", hub());

let sm = await readFile(SITEMAP, "utf8");
sm = sm.replace(/<url><loc>https:\/\/ballistics\.ge\/glossary\/[^<]*<\/loc>.*?<\/url>/g, "");
const entries = [`<url><loc>${SITE}/glossary/</loc><lastmod>${TODAY}</lastmod><priority>0.8</priority></url>`, ...list.map((t) => `<url><loc>${SITE}/glossary/${t.slug}/</loc><lastmod>${TODAY}</lastmod></url>`)];
sm = sm.replace("</urlset>", entries.join("") + "</urlset>");
await writeFile(SITEMAP, sm);
console.log(report.join("\n") + `\n${list.length} pages written.`);
