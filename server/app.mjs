import { createServer } from 'node:http';
import { randomBytes, createHash, createHmac, timingSafeEqual } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { readFile, stat } from 'node:fs/promises';
import { resolve, extname, sep } from 'node:path';
import { OAuth2Client } from 'google-auth-library';

const token = () => randomBytes(32).toString('base64url');
export const hash = value => createHash('sha256').update(value).digest('hex');
const ttl = 30 * 86400;
const empty = () => ({ rifles: [], ammo: [] });
export function validProfiles(value) {
  if (!value || Object.keys(value).sort().join() !== 'ammo,rifles') return false;
  return ['rifles', 'ammo'].every(kind => Array.isArray(value[kind]) && value[kind].length <= 500 &&
    new Set(value[kind].map(p => p?.id)).size === value[kind].length && value[kind].every(p =>
      p && typeof p === 'object' && !Array.isArray(p) && typeof p.id === 'string' && p.id.length > 0 && p.id.length <= 128 &&
      typeof p.name === 'string' && p.name.length <= 300 && JSON.stringify(p).length <= 16000));
}
export function database(path) {
  const db = new DatabaseSync(path);
  db.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000;
    CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, account TEXT NOT NULL REFERENCES accounts(id), expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS oauth (id TEXT PRIMARY KEY, state TEXT NOT NULL, nonce TEXT NOT NULL, verifier TEXT NOT NULL, expires INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS profiles (account TEXT PRIMARY KEY REFERENCES accounts(id), revision INTEGER NOT NULL, data TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS feedback (id TEXT PRIMARY KEY, created INTEGER NOT NULL, kind TEXT NOT NULL, message TEXT NOT NULL, contact TEXT NOT NULL,
      meta TEXT NOT NULL, ua TEXT NOT NULL, account TEXT, image BLOB, image_type TEXT, read INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS activity (id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT NOT NULL REFERENCES accounts(id), created INTEGER NOT NULL,
      kind TEXT NOT NULL, lat REAL, lon REAL);
    CREATE INDEX IF NOT EXISTS activity_account ON activity(account, created);
    CREATE TABLE IF NOT EXISTS purchases (id TEXT PRIMARY KEY, account TEXT NOT NULL REFERENCES accounts(id), created INTEGER NOT NULL,
      amount TEXT NOT NULL, currency TEXT NOT NULL, raw TEXT NOT NULL);`);
  // Plans: 'founder' = signed in while everything was free (keeps Pro forever), 'free', 'pro' (paid).
  for (const col of ['plan TEXT NOT NULL DEFAULT \'founder\'', 'plan_since INTEGER', 'created INTEGER']) {
    try { db.exec(`ALTER TABLE accounts ADD COLUMN ${col}`); } catch { /* exists */ }
  }
  return db;
}
const feedbackLast = new Map(); // ip -> unix seconds (one message per minute)
const readBody = async (req, limit) => { const chunks = []; let size = 0; for await (const c of req) { size += c.length; if (size > limit) return null; chunks.push(c); } return Buffer.concat(chunks); };
const adminHtml = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ballistics.ge — admin</title>
<style>body{margin:0;background:#121212;color:#e6e6e6;font:15px/1.4 system-ui,sans-serif}main{max-width:720px;margin:0 auto;padding:12px}.c{background:#1c1c1c;border:1px solid #333;border-radius:12px;padding:12px;margin-bottom:10px}.c.read{opacity:.55}.m{color:#9a9a9a;font-size:.85rem}button{background:#242424;color:#e6e6e6;border:1px solid #333;border-radius:8px;padding:8px 12px;cursor:pointer}img{max-width:100%;border-radius:8px;margin-top:8px}pre{white-space:pre-wrap;font:inherit;margin:6px 0}a{color:#4caf50}</style>
<main><div style="margin-bottom:10px"><button onclick="tab('fb')">📥 Feedback</button> <button onclick="tab('us')">👤 Users</button></div><section id="fb"><h2>📥 Feedback inbox</h2><div id="bar"><label><input type="checkbox" id="showread" onchange="load()"> show read</label> <button onclick="load()">↻</button></div><div id="list">Loading…</div></section><section id="us" hidden><h2>👤 Users <span class="m" id="ucount"></span></h2><div id="users">Loading…</div></section></main>
<script>
const $=s=>document.querySelector(s);const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function load(){const r=await fetch('/api/admin/feedback',{cache:'no-store'});if(r.status===401){$('#list').innerHTML='Sign in with an admin Google account in the app first: <a href="/auth/google">sign in</a>';return}
if(!r.ok){$('#list').textContent='Not allowed ('+r.status+')';return}const items=await r.json();const sr=$('#showread').checked;$('#list').innerHTML='';
if(!items.length){$('#list').textContent='No feedback yet.';return}
for(const f of items){if(f.read&&!sr)continue;const d=document.createElement('div');d.className='c'+(f.read?' read':'');const m=f.meta||{};
d.innerHTML='<div class="m"><b>'+esc(f.kind)+'</b> · '+new Date(f.created*1000).toISOString().slice(0,16).replace('T',' ')+' · '+esc(f.contact||'no contact')+(f.email?' · '+esc(f.email):'')+'</div><pre>'+esc(f.message)+'</pre>'
+'<div class="m">'+esc(m.version||'')+' · '+esc(m.units||'')+' · '+esc(m.rifle||'')+' / '+esc(m.ammo||'')+' · '+esc((f.ua||'').slice(0,80))+'</div>'
+(f.hasImage?'<img loading="lazy" src="/api/admin/feedback/'+encodeURIComponent(f.id)+'/image">':'')
+(f.read?'':'<div style="margin-top:8px"><button onclick="mark(\''+f.id+'\')">Mark read</button></div>');$('#list').appendChild(d)}}
async function mark(id){await fetch('/api/admin/feedback/'+encodeURIComponent(id)+'/read',{method:'POST'});load()}load();
const ts=t=>t?new Date(t*1000).toISOString().slice(0,16).replace('T',' '):'—';
function tab(n){$('#fb').hidden=n!=='fb';$('#us').hidden=n!=='us';if(n==='us')users()}
async function users(){const r=await fetch('/api/admin/users',{cache:'no-store'});if(!r.ok){$('#users').textContent='Not allowed ('+r.status+')';return}const list=await r.json();
$('#ucount').textContent=list.length+' total · '+list.filter(u=>u.plan==='pro').length+' paid';$('#users').innerHTML='';
for(const u of list){const d=document.createElement('div');d.className='c';
const loc=u.locations.map(l=>ts(l.created)+(l.lat!=null?' · <a href="https://www.google.com/maps?q='+l.lat+','+l.lon+'">'+l.lat+', '+l.lon+'</a>':'')).join('<br>');
d.innerHTML='<div><b>'+esc(u.name)+'</b> · '+esc(u.email)+' · <span class="m">'+esc(u.plan)+'</span></div><div class="m">registered '+ts(u.created)+' · last active '+ts(u.lastActive)+' · syncs rev '+u.revision+' · feedback '+u.feedback+'</div>'
+'<div class="m">🔫 '+(u.rifles.length?esc(u.rifles.join(', ')):'no rifles synced')+'</div><div class="m">🎯 '+(u.ammo.length?esc(u.ammo.join(', ')):'no loads synced')+'</div>'
+(loc?'<details><summary class="m">📍 '+u.activity+' weather syncs</summary><div class="m">'+loc+'</div></details>':'');$('#users').appendChild(d)}}
</script></html>`;
export function app({ db, origin, clientId, clientSecret, webRoot, adminEmails = [], paddle = {}, google = new OAuth2Client(clientId, clientSecret, `${origin}/auth/google/callback`) }) {
  const admins = new Set(adminEmails.map(e => e.trim().toLowerCase()).filter(Boolean));
  const secure = new URL(origin).protocol === 'https:';
  const cookie = (name, value, age) => `${name}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${age}${secure ? '; Secure' : ''}`;
  const ready = Boolean(clientId && clientSecret);
  // paddle: { required, clientToken, priceId, env ('sandbox'|'production'), webhookSecret }
  const proRequired = Boolean(paddle.required);
  const hasPro = plan => plan === 'pro' || plan === 'founder';
  const verifyPaddle = (sig, raw) => {
    if (!paddle.webhookSecret || !sig) return false;
    const parts = Object.fromEntries(sig.split(';').map(s => s.split('=')));
    if (!parts.ts || !parts.h1 || Math.abs(Date.now() / 1000 - Number(parts.ts)) > 300) return false;
    const h = createHmac('sha256', paddle.webhookSecret).update(`${parts.ts}:`).update(raw).digest('hex');
    return h.length === parts.h1.length && timingSafeEqual(Buffer.from(h), Buffer.from(parts.h1));
  };
  const root = resolve(webRoot);
  return createServer(async (req, res) => {
    const url = new URL(req.url, origin);
    const cookies = Object.fromEntries((req.headers.cookie || '').split(';').map(s => s.trim().split('=')));
    const now = Math.floor(Date.now() / 1000);
    const json = (status, value) => { res.writeHead(status, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' }); res.end(JSON.stringify(value)); };
    const redirect = path => { res.writeHead(302, { Location: path, 'Cache-Control': 'no-store' }); res.end(); };
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'same-origin');
    res.setHeader('X-Frame-Options', 'DENY');
    try {
      if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/')) {
        res.setHeader('Cache-Control', 'no-store');
        if (url.pathname === '/api/paddle/webhook') {
          if (req.method !== 'POST') return json(405, { error: 'method' });
          const raw = await readBody(req, 512 * 1024);
          if (!raw || !verifyPaddle(req.headers['paddle-signature'], raw)) return json(401, { error: 'signature' });
          let ev; try { ev = JSON.parse(raw.toString('utf8')); } catch { return json(400, { error: 'json' }); }
          if (ev.event_type === 'transaction.completed' || ev.event_type === 'transaction.paid') {
            const d = ev.data || {}; const account = d.custom_data?.account_id;
            if (account && db.prepare('SELECT id FROM accounts WHERE id=?').get(account)) {
              db.prepare('INSERT OR IGNORE INTO purchases VALUES (?,?,?,?,?,?)').run(d.id || ev.event_id, account, now, String(d.details?.totals?.total ?? ''), d.currency_code || '', raw.toString('utf8').slice(0, 20000));
              db.prepare("UPDATE accounts SET plan='pro', plan_since=? WHERE id=? AND plan<>'pro'").run(now, account);
            }
          }
          return json(200, { ok: true });
        }
        if (!['GET', 'HEAD'].includes(req.method) && req.headers.origin !== origin) return json(403, { error: 'origin' });
      }
      if (url.pathname === '/auth/google' && req.method === 'GET') {
        if (!ready) return redirect('/?auth=unavailable');
        db.prepare('DELETE FROM oauth WHERE expires < ?').run(now);
        db.prepare('DELETE FROM sessions WHERE expires < ?').run(now);
        if (db.prepare('SELECT count(*) AS n FROM oauth').get().n >= 10000) return json(429, { error: 'busy' });
        const id = token(), state = token(), nonce = token(), verifier = token();
        db.prepare('INSERT INTO oauth VALUES (?,?,?,?,?)').run(hash(id), state, nonce, verifier, now + 600);
        res.setHeader('Set-Cookie', cookie('bge_oauth', id, 600));
        return redirect(google.generateAuthUrl({ scope: ['openid', 'email', 'profile'], state, nonce,
          code_challenge: createHash('sha256').update(verifier).digest('base64url'), code_challenge_method: 'S256', prompt: 'select_account' }));
      }
      if (url.pathname === '/auth/google/callback' && req.method === 'GET') {
        const id = hash(cookies.bge_oauth || '');
        const attempt = db.prepare('SELECT * FROM oauth WHERE id = ?').get(id);
        db.prepare('DELETE FROM oauth WHERE id = ?').run(id);
        res.setHeader('Set-Cookie', cookie('bge_oauth', '', 0));
        if (!ready || !attempt || attempt.expires < now || attempt.state !== url.searchParams.get('state') || !url.searchParams.get('code')) return redirect('/?auth=failed');
        try {
          const { tokens } = await google.getToken({ code: url.searchParams.get('code'), codeVerifier: attempt.verifier });
          const ticket = await google.verifyIdToken({ idToken: tokens.id_token, audience: clientId });
          const identity = ticket.getPayload();
          if (!identity?.sub || !identity.email_verified || identity.nonce !== attempt.nonce) return redirect('/?auth=failed');
          db.prepare('INSERT INTO accounts (id,email,name,plan,created) VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email,name=excluded.name')
            .run(identity.sub, identity.email, identity.name || identity.email, proRequired ? 'free' : 'founder', now);
          const session = token();
          if (cookies.bge_session) db.prepare('DELETE FROM sessions WHERE id = ?').run(hash(cookies.bge_session));
          db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash(session), identity.sub, now + ttl);
          res.setHeader('Set-Cookie', [cookie('bge_oauth', '', 0), cookie('bge_session', session, ttl)]);
          return redirect('/?auth=success');
        } catch { return redirect('/?auth=failed'); }
      }
      if (url.pathname.startsWith('/api/')) {
        const user = db.prepare('SELECT accounts.* FROM sessions JOIN accounts ON accounts.id=sessions.account WHERE sessions.id=? AND expires>?').get(hash(cookies.bge_session || ''), now);
        if (url.pathname === '/api/account' && req.method === 'GET') return json(200, {
          user: user ? { id: user.id, email: user.email, name: user.name, plan: user.plan, pro: hasPro(user.plan) } : null, googleEnabled: ready,
          billing: { required: proRequired, priceId: paddle.priceId || null, clientToken: paddle.clientToken || null, env: paddle.env || 'production' } });
        // Feedback: anonymous, one message per minute per IP, optional screenshot (data URL, <= 2 MB).
        if (url.pathname === '/api/feedback' && req.method === 'POST') {
          const ip = (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || req.socket.remoteAddress || '?';
          if (now - (feedbackLast.get(ip) || 0) < 60) return json(429, { error: 'wait_a_minute' });
          const raw = await readBody(req, 3 * 1024 * 1024);
          if (!raw) return json(413, { error: 'too_large' });
          let body; try { body = JSON.parse(raw.toString('utf8')); } catch { return json(400, { error: 'invalid_json' }); }
          const message = String(body?.message || '').trim().slice(0, 4000);
          if (message.length < 5) return json(400, { error: 'message_too_short' });
          let image = null, imageType = null;
          const m = typeof body.screenshot === 'string' ? body.screenshot.match(/^data:image\/(png|jpeg|webp);base64,([A-Za-z0-9+/=]+)$/) : null;
          if (m) { image = Buffer.from(m[2], 'base64'); imageType = `image/${m[1]}`; if (image.length > 2 * 1024 * 1024) return json(413, { error: 'image_too_large' }); }
          const id = `${now}-${token().slice(0, 8)}`;
          db.prepare('INSERT INTO feedback (id,created,kind,message,contact,meta,ua,account,image,image_type) VALUES (?,?,?,?,?,?,?,?,?,?)').run(
            id, now, String(body.kind || '').slice(0, 40), message, String(body.contact || '').slice(0, 200),
            JSON.stringify(body.meta && typeof body.meta === 'object' ? body.meta : {}).slice(0, 4000), String(req.headers['user-agent'] || '').slice(0, 300), user?.id || null, image, imageType);
          feedbackLast.set(ip, now);
          if (feedbackLast.size > 10000) feedbackLast.clear();
          return json(200, { ok: true, id });
        }
        if (url.pathname.startsWith('/api/admin/')) {
          if (!user) return json(401, { error: 'sign_in_required' });
          if (!admins.has(user.email.toLowerCase())) return json(403, { error: 'not_admin' });
          if (url.pathname === '/api/admin/feedback' && req.method === 'GET') {
            const rows = db.prepare('SELECT f.id,f.created,f.kind,f.message,f.contact,f.meta,f.ua,f.read,(f.image IS NOT NULL) AS hasImage,a.email FROM feedback f LEFT JOIN accounts a ON a.id=f.account ORDER BY f.created DESC LIMIT 500').all();
            return json(200, rows.map(r => ({ ...r, meta: JSON.parse(r.meta || '{}'), read: Boolean(r.read), hasImage: Boolean(r.hasImage) })));
          }
          if (url.pathname === '/api/admin/users' && req.method === 'GET') {
            const rows = db.prepare(`SELECT a.id,a.email,a.name,a.plan,a.created,a.plan_since,p.revision,p.data,
                (SELECT COUNT(*) FROM feedback f WHERE f.account=a.id) AS feedback,
                (SELECT COUNT(*) FROM activity x WHERE x.account=a.id) AS activity,
                (SELECT MAX(created) FROM activity x WHERE x.account=a.id) AS lastActive
              FROM accounts a LEFT JOIN profiles p ON p.account=a.id ORDER BY a.created DESC, a.rowid DESC LIMIT 2000`).all();
            const last = db.prepare('SELECT created,kind,lat,lon FROM activity WHERE account=? ORDER BY created DESC LIMIT 20');
            return json(200, rows.map(r => { let d = {}; try { d = JSON.parse(r.data || '{}'); } catch {}
              return { id: r.id, email: r.email, name: r.name, plan: r.plan, created: r.created, planSince: r.plan_since, revision: r.revision || 0,
                rifles: (d.rifles || []).map(x => `${x.name || '?'} (${x.chambering || '?'})`), ammo: (d.ammo || []).map(x => `${x.name || '?'} (${x.cartridge || '?'})`),
                feedback: r.feedback, activity: r.activity, lastActive: r.lastActive, locations: last.all(r.id) }; }));
          }
          const fm = url.pathname.match(/^\/api\/admin\/feedback\/([\w-]+)\/(image|read)$/);
          if (fm && fm[2] === 'image' && req.method === 'GET') {
            const row = db.prepare('SELECT image,image_type FROM feedback WHERE id=?').get(fm[1]);
            if (!row?.image) return json(404, { error: 'not_found' });
            res.writeHead(200, { 'Content-Type': row.image_type, 'Cache-Control': 'private,max-age=3600' }); return res.end(row.image);
          }
          if (fm && fm[2] === 'read' && req.method === 'POST') { db.prepare('UPDATE feedback SET read=1 WHERE id=?').run(fm[1]); return json(200, { ok: true }); }
          return json(404, { error: 'not_found' });
        }
        if (!user) return json(401, { error: 'sign_in_required' });
        if (url.pathname === '/api/logout' && req.method === 'POST') {
          db.prepare('DELETE FROM sessions WHERE id=?').run(hash(cookies.bge_session));
          res.setHeader('Set-Cookie', cookie('bge_session', '', 0));
          return json(200, { ok: true });
        }
        if (url.pathname === '/api/activity' && req.method === 'POST') {
          let b; try { b = JSON.parse((await readBody(req, 4096)).toString('utf8')); } catch { return json(400, { error: 'json' }); }
          const kind = ['weather', 'locate'].includes(b?.kind) ? b.kind : 'weather';
          // Store ~1 km resolution only; we never keep exact positions.
          const ok = Number.isFinite(b?.lat) && Number.isFinite(b?.lon) && Math.abs(b.lat) <= 90 && Math.abs(b.lon) <= 180;
          db.prepare('INSERT INTO activity (account,created,kind,lat,lon) VALUES (?,?,?,?,?)').run(user.id, now, kind, ok ? Math.round(b.lat * 100) / 100 : null, ok ? Math.round(b.lon * 100) / 100 : null);
          db.prepare('DELETE FROM activity WHERE account=? AND id NOT IN (SELECT id FROM activity WHERE account=? ORDER BY created DESC LIMIT 500)').run(user.id, user.id);
          return json(200, { ok: true });
        }
        if (url.pathname === '/api/profiles' && req.headers['x-account-id'] !== user.id) return json(409, { error: 'account_changed' });
        if (url.pathname === '/api/profiles' && req.method === 'GET') {
          const row = db.prepare('SELECT * FROM profiles WHERE account=?').get(user.id);
          return json(200, row ? { revision: row.revision, data: JSON.parse(row.data) } : { revision: 0, data: empty() });
        }
        if (url.pathname === '/api/profiles' && req.method === 'PUT') {
          if (!req.headers['content-type']?.startsWith('application/json')) return json(415, { error: 'json_required' });
          const chunks = []; let size = 0;
          for await (const chunk of req) { size += chunk.length; if (size > 1024 * 1024) return json(413, { error: 'too_large' }); chunks.push(chunk); }
          let body; try { body = JSON.parse(Buffer.concat(chunks).toString('utf8')); } catch { return json(400, { error: 'invalid_json' }); }
          if (!body || !Number.isSafeInteger(body.revision) || body.revision < 0 || !validProfiles(body.data)) return json(400, { error: 'invalid_profiles' });
          const data = JSON.stringify(body.data);
          // One atomic compare-and-swap: stale devices cannot overwrite newer profiles.
          const result = body.revision === 0
            ? db.prepare('INSERT OR IGNORE INTO profiles VALUES (?,1,?)').run(user.id, data)
            : db.prepare('UPDATE profiles SET revision=revision+1,data=? WHERE account=? AND revision=?').run(data, user.id, body.revision);
          if (!result.changes) return json(409, { error: 'revision_conflict' });
          return json(200, { revision: body.revision + 1 });
        }
        return json(404, { error: 'not_found' });
      }
      if (url.pathname.startsWith('/auth/')) return json(404, { error: 'not_found' });
      if (!['GET', 'HEAD'].includes(req.method)) return json(405, { error: 'method' });
      if (url.pathname === '/healthz') return json(200, { ok: true });
      if (url.pathname === '/admin') { res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' }); return res.end(adminHtml); }
      if (url.pathname === '/blog') return redirect('/blog/');
      let file = resolve(root, '.' + decodeURIComponent(url.pathname));
      if (file !== root && !file.startsWith(root + sep)) return json(404, { error: 'not_found' });
      try { if ((await stat(file)).isDirectory()) file = resolve(file, 'index.html'); await stat(file); }
      catch { if (url.pathname.startsWith('/blog/') || extname(file)) return json(404, { error: 'not_found' }); file = resolve(root, 'index.html'); }
      const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.txt': 'text/plain', '.xml': 'application/xml', '.woff2': 'font/woff2' };
      res.writeHead(200, { 'Content-Type': types[extname(file)] || 'application/octet-stream', 'Cache-Control': file.includes(`${sep}assets${sep}`) ? 'public,max-age=31536000,immutable' : 'no-cache' });
      res.end(req.method === 'HEAD' ? undefined : await readFile(file));
    } catch { if (!res.headersSent) json(500, { error: 'server_error' }); else res.end(); }
  });
}
