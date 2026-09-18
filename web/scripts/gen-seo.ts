/** Generates static, crawlable ballistics chart pages from the bullet library using the app's own solver.
 *  Output: public/ballistics/** and public/sitemap.xml. Run via `npm run gen-seo` (also part of `build`). */
import { mkdirSync, writeFileSync, rmSync } from "node:fs";
import { resolve } from "node:path";
import { calculateSolution, atRange, dropMrad, windageMrad, MRAD_TO_MOA } from "../src/core/solver";
import lib from "../src/data/bullets.json";

type Bullet = { id: string; manufacturer: string; caliber: string; bullet: string; mass_grains: number; diameter_in: number; length_in: number; bc_g7?: number | null; bc_g1?: number | null; default_mv_mps: number; default_twist_in?: number };
const bullets = (lib as { bullets: Bullet[] }).bullets;
const PUB = resolve(process.cwd(), "public");
const OUT = resolve(PUB, "ballistics") + "/";
const SITE = "https://ballistics.ge";
const TODAY = new Date().toISOString().slice(0, 10);
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const esc = (s: string) => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
const calSlug = (c: string) => slug(c);
const M2YD = 1.09361, M2IN = 39.3701, MPS2FPS = 3.28084, J2FTLB = 0.737562;

const head = (title: string, desc: string, path: string, jsonld?: object) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>${esc(title)}</title><meta name="description" content="${esc(desc)}"><link rel="canonical" href="${SITE}${path}"><meta property="og:type" content="article"><meta property="og:title" content="${esc(title)}"><meta property="og:description" content="${esc(desc)}"><meta property="og:url" content="${SITE}${path}"><meta property="og:image" content="${SITE}/brand/ballistics-logo.png"><link rel="stylesheet" href="/blog/blog.css"><link rel="icon" type="image/png" sizes="32x32" href="/icons/ballistics-b-32.png">${jsonld ? `<script type="application/ld+json">${JSON.stringify(jsonld)}</script>` : ""}<style>table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:.92rem}th,td{padding:6px 8px;text-align:right;border-bottom:1px solid var(--border,#333)}th:first-child,td:first-child{text-align:left}thead th{position:sticky;top:0;background:var(--panel,#111)}.wrap{overflow-x:auto}.cta{display:inline-block;padding:12px 20px;border-radius:10px;background:#99d284;color:#000;font-weight:700;text-decoration:none}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}.kv{background:var(--panel2,#161616);border:1px solid var(--border,#333);border-radius:8px;padding:8px}.kv b{display:block;font-size:1.1rem}</style></head><body><a class="skip" href="#content">Skip to content</a><header><a href="/" class="brand" aria-label="ballistics.ge"><img src="/brand/ballistics-logo.png" alt="ballistics.ge" width="1200" height="520"></a><nav aria-label="Main"><a href="/">Calculator</a> · <a href="/ballistics/">Ballistics charts</a> · <a href="/pricing/">Pricing</a> · <a href="/blog/">Blog</a></nav></header><main id="content">`;
const foot = `</main><footer>ballistics.ge — free ballistic calculator that works offline · <a href="/ballistics/">Charts</a> · <a href="/terms/">Terms</a> · <a href="/privacy/">Privacy</a></footer></body></html>`;

function table(b: Bullet, imperial: boolean) {
  const zeroM = imperial ? 100 / M2YD : 100;
  const ranges = imperial ? [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000].map(y => y / M2YD) : [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000];
  const wind = imperial ? 10 / 2.23694 : 4; // 10 mph / 4 m/s full-value
  const sol = calculateSolution({ muzzleVelocityMps: b.default_mv_mps, bcG7: b.bc_g7 ?? null, bcG1: b.bc_g1 ?? null, dragModel: b.bc_g7 ? "G7" : "G1", massGrains: b.mass_grains, diameterIn: b.diameter_in,
    bulletLengthIn: b.length_in, twistRateIn: b.default_twist_in ?? 10, zeroRangeM: zeroM, targetRangeM: 1100, sightHeightMm: 40, windSpeedMps: wind, windDirectionDeg: 90, temperatureC: 15, pressureMbar: 1013.25, humidityPct: 50 });
  const rows = ranges.map(r => { const p = atRange(sol, r); if (!p) return ""; const isZero = Math.abs(r - zeroM) < 0.5; const dm = isZero ? 0 : dropMrad(p), wm = windageMrad(p); if (isZero) p.dropM = 0;
    const drop = imperial ? (p.dropM * M2IN).toFixed(1) : (p.dropM * 100).toFixed(1);
    const wnd = imperial ? Math.abs(p.windageM * M2IN).toFixed(1) : Math.abs(p.windageM * 100).toFixed(1);
    const v = imperial ? Math.round(p.velocityMps * MPS2FPS) : Math.round(p.velocityMps);
    const e = imperial ? Math.round(p.energyJ * J2FTLB) : Math.round(p.energyJ);
    return `<tr><td>${imperial ? Math.round(r * M2YD) + " yd" : r + " m"}</td><td>${drop}</td><td>${(-dm).toFixed(2)}</td><td>${(-dm * MRAD_TO_MOA).toFixed(2)}</td><td>${wnd}</td><td>${Math.abs(wm).toFixed(2)}</td><td>${Math.abs(wm * MRAD_TO_MOA).toFixed(2)}</td><td>${v}</td><td>${e}</td><td>${p.timeS.toFixed(3)}</td></tr>`; }).join("");
  const u = imperial ? { z: "100 yd", d: "in", w: "10 mph", v: "fps", e: "ft·lb" } : { z: "100 m", d: "cm", w: "4 m/s", v: "m/s", e: "J" };
  return `<h3>${imperial ? "Yards" : "Metres"} · ${u.z} zero · ${u.w} full-value wind</h3><div class="wrap"><table><thead><tr><th>Range</th><th>Drop (${u.d})</th><th>Elev MRAD</th><th>Elev MOA</th><th>Wind (${u.d})</th><th>Wind MRAD</th><th>Wind MOA</th><th>Velocity (${u.v})</th><th>Energy (${u.e})</th><th>Time (s)</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

rmSync(OUT, { recursive: true, force: true });
const byCal = new Map<string, Bullet[]>();
for (const b of bullets) (byCal.get(b.caliber) ?? byCal.set(b.caliber, []).get(b.caliber)!).push(b);
const urls: string[] = [];

for (const b of bullets) {
  const name = `${b.manufacturer} ${b.bullet}`;
  const path = `/ballistics/${calSlug(b.caliber)}/${slug(b.id)}/`;
  const title = `${b.caliber} ${name} ballistics chart — drop, wind & energy | ballistics.ge`;
  const desc = `${b.caliber} ${name} (${b.mass_grains} gr, G7 BC ${b.bc_g7 ?? "—"}, G1 BC ${b.bc_g1 ?? "—"}) trajectory table at ${Math.round(b.default_mv_mps * MPS2FPS)} fps / ${b.default_mv_mps} m/s: bullet drop, wind drift, velocity and energy out to 1000 yards and 1000 m. Free, works offline.`;
  const body = `<h1>${esc(b.caliber)} ${esc(name)} ballistics chart</h1>
<p class="intro">Trajectory, wind drift, velocity and energy for the ${esc(b.manufacturer)} ${esc(b.bullet)} in ${esc(b.caliber)}, computed with the same RK4 point-mass solver as the <a href="/">ballistics.ge calculator</a>. Sea level, 15 °C / 59 °F, 40 mm sight height. Your rifle will differ — <a href="/">run it with your muzzle velocity and conditions</a>, or true it on the range.</p>
<div class="grid"><div class="kv">Weight<b>${b.mass_grains} gr</b></div><div class="kv">G7 BC<b>${b.bc_g7 ?? "—"}</b></div><div class="kv">G1 BC<b>${b.bc_g1 ?? "—"}</b></div><div class="kv">Muzzle velocity<b>${Math.round(b.default_mv_mps * MPS2FPS)} fps · ${b.default_mv_mps} m/s</b></div><div class="kv">Diameter<b>${b.diameter_in}"</b></div><div class="kv">Length<b>${b.length_in}"</b></div></div>
${table(b, true)}${table(b, false)}
<p><a class="cta" href="/">Open in the free calculator →</a></p>
<h2>Notes</h2><p>Drop is measured from the line of sight with a ${"100 yd / 100 m"} zero; "Elev" is the correction to dial UP. Wind columns are for a full-value (90°) crosswind — halve them for a 45° wind. Velocity and BC are manufacturer published values for a typical barrel; verify with a chronograph or use the truing tool in the app. Coriolis and spin drift are excluded here but included in the calculator.</p>
<p>More ${esc(b.caliber)} loads: <a href="/ballistics/${calSlug(b.caliber)}/">${esc(b.caliber)} ballistics charts</a>.</p>`;
  mkdirSync(`${OUT}${calSlug(b.caliber)}/${slug(b.id)}`, { recursive: true });
  writeFileSync(`${OUT}${path.slice("/ballistics/".length)}index.html`, head(title, desc, path, { "@context": "https://schema.org", "@type": "Dataset", name: title, description: desc, url: SITE + path, creator: { "@type": "Organization", name: "ballistics.ge" }, license: "https://ballistics.ge/terms/" }) + body + foot);
  urls.push(path);
}

for (const [cal, list] of byCal) {
  const path = `/ballistics/${calSlug(cal)}/`;
  const title = `${cal} ballistics charts — bullet drop & wind drift tables (${list.length} loads) | ballistics.ge`;
  const desc = `${cal} trajectory tables for ${list.length} factory bullets: drop, wind, velocity and energy to 1000 yards. Free ballistic calculator, works offline.`;
  const items = list.sort((a, b) => a.mass_grains - b.mass_grains || a.manufacturer.localeCompare(b.manufacturer)).map(b => `<li><a href="/ballistics/${calSlug(cal)}/${slug(b.id)}/">${esc(b.manufacturer)} ${esc(b.bullet)}</a> — ${b.mass_grains} gr, G7 ${b.bc_g7 ?? "—"}, ${Math.round(b.default_mv_mps * MPS2FPS)} fps</li>`).join("");
  writeFileSync(`${OUT}${calSlug(cal)}/index.html`, head(title, desc, path) + `<h1>${esc(cal)} ballistics charts</h1><p class="intro">Drop and wind tables for ${list.length} ${esc(cal)} bullets, in yards and metres. Pick your bullet, or <a href="/">open the calculator</a> and enter your own velocity.</p><ul>${items}</ul><p><a class="cta" href="/">Open the free calculator →</a></p>` + foot);
  urls.push(path);
}

const calList = [...byCal.entries()].sort((a, b) => b[1].length - a[1].length).map(([c, l]) => `<li><a href="/ballistics/${calSlug(c)}/">${esc(c)}</a> <span class="meta">(${l.length} loads)</span></li>`).join("");
writeFileSync(`${OUT}index.html`, head("Ballistics charts by cartridge — drop & wind tables | ballistics.ge", `Free bullet drop and wind drift charts for ${bullets.length} factory bullets across ${byCal.size} cartridges (.308 Win, 6.5 Creedmoor, .223 Rem, .22 LR and more). Generated by the ballistics.ge calculator.`, "/ballistics/") + `<h1>Ballistics charts by cartridge</h1><p class="intro">${bullets.length} factory bullets, ${byCal.size} cartridges. Every table is computed by the free <a href="/">ballistics.ge calculator</a> — the same solver, so what you see here is what the app will give you before truing.</p><ul>${calList}</ul><p><a class="cta" href="/">Open the free calculator →</a></p>` + foot);
urls.push("/ballistics/");

// sitemap: static pages + generated
const staticUrls = ["/", "/pricing/", "/terms/", "/privacy/", "/refunds/", "/blog/", "/blog/vaznebis-gadatana-300-400/", "/blog/shenaxvis-uflebit-iaraghi-tirshi/", "/blog/iaraghis-shenaxvis-pirobebi/", "/blog/dasakhlebidan-ramden-metrshi-sheidzleba-srola/", "/blog/sad-visrolot-shashkhanit-sakartveloshi/"];
const sm = `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${[...staticUrls, ...urls].map(u => `<url><loc>${SITE}${u}</loc><lastmod>${TODAY}</lastmod>${u === "/" ? "<priority>1.0</priority>" : ""}</url>`).join("")}</urlset>`;
writeFileSync(resolve(PUB, "sitemap.xml"), sm);
console.log(`gen-seo: ${bullets.length} bullet pages, ${byCal.size} cartridge pages, sitemap ${staticUrls.length + urls.length} urls`);
