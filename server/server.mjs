// ballistics.ge server: static PWA + feedback API + admin inbox. Node built-ins only.
// Data lives in DATA_DIR (mount a Railway Volume at /data to keep it across deploys).
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const PORT = +(process.env.PORT || 8080);
const DIST = process.env.DIST_DIR || path.resolve("web/dist");
const DATA = process.env.DATA_DIR || "/data";
const FEED = path.join(DATA, "feedback");
const ADMIN_TOKEN = process.env.ADMIN_TOKEN || "";
const MAX_BODY = 3 * 1024 * 1024;
fs.mkdirSync(FEED, { recursive: true });

const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".webmanifest": "application/manifest+json",
  ".txt": "text/plain; charset=utf-8", ".xml": "application/xml", ".woff2": "font/woff2" };

const lastPost = new Map(); // ip -> ts (rate limit)

function send(res, code, body, type = "application/json", extra = {}) {
  const buf = typeof body === "string" || Buffer.isBuffer(body) ? body : JSON.stringify(body);
  res.writeHead(code, { "content-type": type, "content-length": Buffer.byteLength(buf), ...extra });
  res.end(buf);
}
function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on("data", (c) => { size += c.length; if (size > MAX_BODY) { reject(new Error("too large")); req.destroy(); } else chunks.push(c); });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}
const isAdmin = (url) => ADMIN_TOKEN && url.searchParams.get("token") === ADMIN_TOKEN;
const safeId = (s) => /^[a-z0-9-]{8,40}$/i.test(s) ? s : null;

async function handleFeedback(req, res) {
  const ip = req.headers["x-forwarded-for"]?.split(",")[0]?.trim() || req.socket.remoteAddress || "?";
  const now = Date.now();
  if (now - (lastPost.get(ip) || 0) < 60_000) return send(res, 429, { error: "wait a minute" });
  let body;
  try { body = JSON.parse((await readBody(req)).toString("utf8")); } catch { return send(res, 400, { error: "bad body" }); }
  const message = String(body.message || "").trim().slice(0, 4000);
  if (message.length < 5) return send(res, 400, { error: "message too short" });
  const id = `${new Date(now).toISOString().replace(/[:.]/g, "-")}-${crypto.randomBytes(3).toString("hex")}`;
  let screenshot = null;
  if (typeof body.screenshot === "string" && body.screenshot.startsWith("data:image/")) {
    const m = body.screenshot.match(/^data:image\/(png|jpeg|webp);base64,(.+)$/);
    if (m) { screenshot = `${id}.${m[1] === "jpeg" ? "jpg" : m[1]}`; fs.writeFileSync(path.join(FEED, screenshot), Buffer.from(m[2], "base64")); }
  }
  const rec = { id, created_at: new Date(now).toISOString(), kind: String(body.kind || "").slice(0, 40), message,
    contact: String(body.contact || "").slice(0, 200), meta: body.meta && typeof body.meta === "object" ? body.meta : {},
    ua: String(req.headers["user-agent"] || "").slice(0, 300), screenshot, read: false };
  fs.writeFileSync(path.join(FEED, `${id}.json`), JSON.stringify(rec, null, 1));
  lastPost.set(ip, now);
  send(res, 200, { ok: true, id });
}

function listFeedback() {
  return fs.readdirSync(FEED).filter((f) => f.endsWith(".json")).sort().reverse()
    .map((f) => { try { return JSON.parse(fs.readFileSync(path.join(FEED, f), "utf8")); } catch { return null; } }).filter(Boolean);
}

const ADMIN_HTML = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ballistics.ge — feedback inbox</title>
<style>body{margin:0;background:#121212;color:#e6e6e6;font:15px/1.4 system-ui,sans-serif}main{max-width:720px;margin:0 auto;padding:12px}
.c{background:#1c1c1c;border:1px solid #333;border-radius:12px;padding:12px;margin-bottom:10px}.c.read{opacity:.55}.m{color:#9a9a9a;font-size:.85rem}
input,button{background:#242424;color:#e6e6e6;border:1px solid #333;border-radius:8px;padding:10px;font-size:1rem}button{cursor:pointer}
img{max-width:100%;border-radius:8px;margin-top:8px}pre{white-space:pre-wrap;font:inherit;margin:6px 0}</style>
<main><h2>📥 Feedback inbox</h2><div id="login"><input id="tok" type="password" placeholder="admin token" style="width:70%"> <button onclick="go()">Open</button></div>
<div id="bar" hidden><label><input type="checkbox" id="showread" onchange="load()"> show read</label> <button onclick="load()">↻</button></div><div id="list"></div></main>
<script>
const $=s=>document.querySelector(s);let tok=localStorage.getItem('bge_admin')||'';if(tok){$('#tok').value=tok;go()}
async function go(){tok=$('#tok').value.trim();localStorage.setItem('bge_admin',tok);await load()}
async function load(){const r=await fetch('/api/admin/feedback?token='+encodeURIComponent(tok));if(!r.ok){$('#list').textContent='wrong token';return}
$('#login').hidden=true;$('#bar').hidden=false;const items=await r.json();const sr=$('#showread').checked;$('#list').innerHTML='';
if(!items.length){$('#list').textContent='No feedback yet.';return}
for(const f of items){if(f.read&&!sr)continue;const d=document.createElement('div');d.className='c'+(f.read?' read':'');
const meta=f.meta||{};d.innerHTML='<div class="m"><b>'+esc(f.kind)+'</b> · '+f.created_at.slice(0,16).replace('T',' ')+' · '+esc(f.contact||'no contact')+'</div><pre>'+esc(f.message)+'</pre>'
+'<div class="m">'+esc(meta.version||'')+' · '+esc(meta.units||'')+' · '+esc(meta.rifle||'')+' / '+esc(meta.ammo||'')+' · '+esc((f.ua||'').slice(0,80))+'</div>'
+(f.screenshot?'<img loading="lazy" src="/api/admin/feedback/'+f.id+'/image?token='+encodeURIComponent(tok)+'">':'')
+(f.read?'':'<div style="margin-top:8px"><button onclick="mark(\\''+f.id+'\\')">Mark read</button></div>');$('#list').appendChild(d)}}
async function mark(id){await fetch('/api/admin/feedback/'+id+'/read?token='+encodeURIComponent(tok),{method:'POST'});load()}
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
</script></html>`;

function serveStatic(req, res, url) {
  let p = decodeURIComponent(url.pathname);
  if (p.includes("..")) return send(res, 400, "bad path", "text/plain");
  let file = path.join(DIST, p);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(DIST, "index.html");
  const ext = path.extname(file);
  const noCache = ext === ".html" || path.basename(file) === "sw.js" || ext === ".webmanifest";
  const headers = { "cache-control": noCache ? "no-cache" : "public, max-age=31536000, immutable" };
  send(res, 200, fs.readFileSync(file), MIME[ext] || "application/octet-stream", headers);
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, "http://x");
  try {
    if (req.method === "POST" && url.pathname === "/api/feedback") return await handleFeedback(req, res);
    if (url.pathname === "/admin") return ADMIN_TOKEN ? send(res, 200, ADMIN_HTML, "text/html; charset=utf-8") : send(res, 404, "admin disabled (set ADMIN_TOKEN)", "text/plain");
    if (url.pathname.startsWith("/api/admin/")) {
      if (!isAdmin(url)) return send(res, 401, { error: "unauthorized" });
      if (url.pathname === "/api/admin/feedback") return send(res, 200, listFeedback());
      const m = url.pathname.match(/^\/api\/admin\/feedback\/([^/]+)\/(image|read)$/);
      const id = m && safeId(m[1]);
      if (!id) return send(res, 404, { error: "not found" });
      const jsonPath = path.join(FEED, `${id}.json`);
      if (!fs.existsSync(jsonPath)) return send(res, 404, { error: "not found" });
      const rec = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
      if (m[2] === "image") {
        if (!rec.screenshot) return send(res, 404, { error: "no image" });
        const f = path.join(FEED, rec.screenshot);
        return send(res, 200, fs.readFileSync(f), MIME[path.extname(f)] || "image/jpeg");
      }
      rec.read = true; fs.writeFileSync(jsonPath, JSON.stringify(rec, null, 1));
      return send(res, 200, { ok: true });
    }
    if (req.method !== "GET" && req.method !== "HEAD") return send(res, 405, "method not allowed", "text/plain");
    return serveStatic(req, res, url);
  } catch (e) {
    console.error(e);
    send(res, 500, { error: "server error" });
  }
}).listen(PORT, () => console.log(`ballistics.ge listening on :${PORT}, data in ${DATA}, admin ${ADMIN_TOKEN ? "enabled" : "disabled"}`));
