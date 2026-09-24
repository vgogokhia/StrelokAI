import { createServer } from 'node:http';
import { ADAPTERS, VENDORS, listModels } from './providers.mjs';
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
export function database(path, { sessionTtl = 60 * 60 * 24 * 30 } = {}) {
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
    CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS assistant_usage (account TEXT NOT NULL, day TEXT NOT NULL, count INTEGER NOT NULL, PRIMARY KEY (account, day));
    CREATE TABLE IF NOT EXISTS purchases (id TEXT PRIMARY KEY, account TEXT NOT NULL REFERENCES accounts(id), created INTEGER NOT NULL,
      amount TEXT NOT NULL, currency TEXT NOT NULL, raw TEXT NOT NULL);`);
  // Plans: 'founder' = signed in while everything was free (keeps Pro forever), 'free', 'pro' (paid).
  for (const col of ['plan TEXT NOT NULL DEFAULT \'founder\'', 'plan_since INTEGER', 'created INTEGER', 'last_seen INTEGER']) {
    try { db.exec(`ALTER TABLE accounts ADD COLUMN ${col}`); } catch { /* exists */ }
  }
  // Accounts that predate the `created` column: best estimate is when their oldest live session was issued.
  db.exec(`UPDATE accounts SET created = (SELECT MIN(expires) - ${sessionTtl} FROM sessions s WHERE s.account = accounts.id) WHERE created IS NULL`);
  return db;
}
const feedbackLast = new Map(); // ip -> unix seconds (one message per minute)
const readBody = async (req, limit) => { const chunks = []; let size = 0; for await (const c of req) { size += c.length; if (size > limit) return null; chunks.push(c); } return Buffer.concat(chunks); };
const adminHtml = `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ballistics.ge — admin</title>
<style>body{margin:0;background:#121212;color:#e6e6e6;font:15px/1.4 system-ui,sans-serif}main{max-width:720px;margin:0 auto;padding:12px}.c{background:#1c1c1c;border:1px solid #333;border-radius:12px;padding:12px;margin-bottom:10px}.c.read{opacity:.55}.m{color:#9a9a9a;font-size:.85rem}button{background:#242424;color:#e6e6e6;border:1px solid #333;border-radius:8px;padding:8px 12px;cursor:pointer}img{max-width:100%;border-radius:8px;margin-top:8px}pre{white-space:pre-wrap;font:inherit;margin:6px 0}a{color:#4caf50}</style>
<main><div style="margin-bottom:10px"><button onclick="tab('fb')">📥 Feedback</button> <button onclick="tab('us')">👤 Users</button> <button onclick="tab('ai')">🤖 AI</button></div><section id="fb"><h2>📥 Feedback inbox</h2><div id="bar"><label><input type="checkbox" id="showread" onchange="load()"> show read</label> <button onclick="load()">↻</button></div><div id="list">Loading…</div></section><section id="us" hidden><h2>👤 Users <span class="m" id="ucount"></span></h2><div id="users">Loading…</div></section><section id="ai" hidden><h2>🤖 AI assistant</h2><div class="c"><div class="m" id="aicur">Loading…</div>
<p><label>Vendor<br><select id="aiv" onchange="aiModels()"></select></label></p><p><label>Model<br><select id="aim" style="max-width:100%"></select></label> <span class="m" id="aimsg"></span></p>
<p><button onclick="aiSave()">💾 Save</button> <button onclick="aiTest()">▶ Test</button></p><div class="m" id="aiout"></div>
<p class="m">Vendors without an API key are disabled — add ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY in Railway → Variables.</p></div></section></main>
<script>
const $=s=>document.querySelector(s);const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function load(){const r=await fetch('/api/admin/feedback',{cache:'no-store'});if(r.status===401){$('#list').innerHTML='Sign in with an admin Google account in the app first: <a href="/auth/google">sign in</a>';return}
if(!r.ok){$('#list').textContent='Not allowed ('+r.status+')';return}const items=await r.json();const sr=$('#showread').checked;$('#list').innerHTML='';
if(!items.length){$('#list').textContent='No feedback yet.';return}
for(const f of items){if(f.read&&!sr)continue;const d=document.createElement('div');d.className='c'+(f.read?' read':'');const m=f.meta||{};
d.innerHTML='<div class="m"><b>'+esc(f.kind)+'</b> · '+new Date(f.created*1000).toISOString().slice(0,16).replace('T',' ')+' · '+esc(f.contact||'no contact')+(f.email?' · '+esc(f.email):'')+'</div><pre>'+esc(f.message)+'</pre>'
+'<div class="m">'+esc(m.version||'')+' · '+esc(m.units||'')+' · '+esc(m.rifle||'')+' / '+esc(m.ammo||'')+' · '+esc((f.ua||'').slice(0,80))+'</div>'
+(f.hasImage?'<img loading="lazy" src="/api/admin/feedback/'+encodeURIComponent(f.id)+'/image">':'')
+(f.read?'':'<div style="margin-top:8px"><button data-id=\"'+esc(f.id)+'\" onclick=\"mark(this.dataset.id)\">Mark read</button></div>');$('#list').appendChild(d)}}
async function mark(id){await fetch('/api/admin/feedback/'+encodeURIComponent(id)+'/read',{method:'POST'});load()}load();
const ts=t=>t?new Date(t*1000).toISOString().slice(0,16).replace('T',' '):'—';
function tab(n){$('#fb').hidden=n!=='fb';$('#us').hidden=n!=='us';$('#ai').hidden=n!=='ai';if(n==='us')users();if(n==='ai')aiLoad()}
let aiCur=null;async function aiLoad(){const r=await fetch('/api/admin/assistant',{cache:'no-store'});if(!r.ok){$('#aicur').textContent='Not allowed ('+r.status+')';return}const d=await r.json();aiCur=d.current;
$('#aicur').textContent='Active: '+(d.current?d.current.vendor+' · '+d.current.model:'none — pick a model')+' · today '+d.today.n+' questions from '+d.today.users+' users';
$('#aiv').innerHTML=d.vendors.map(v=>'<option value="'+v.id+'"'+(v.enabled?'':' disabled')+(d.current&&d.current.vendor===v.id?' selected':'')+'>'+esc(v.label)+(v.enabled?'':' — no key ('+v.env+')')+'</option>').join('');
if(!d.current){const f=d.vendors.find(v=>v.enabled);if(f)$('#aiv').value=f.id}aiModels()}
async function aiModels(){const v=$('#aiv').value;$('#aim').innerHTML='<option>Loading…</option>';$('#aimsg').textContent='';const r=await fetch('/api/admin/assistant/models?vendor='+encodeURIComponent(v));const d=await r.json();
if(!r.ok){$('#aim').innerHTML='';$('#aimsg').textContent=d.error||r.status;return}$('#aim').innerHTML=d.map(m=>'<option value="'+esc(m.id)+'"'+(aiCur&&aiCur.vendor===v&&aiCur.model===m.id?' selected':'')+'>'+esc(m.name)+(m.name!==m.id?' ('+esc(m.id)+')':'')+'</option>').join('');$('#aimsg').textContent=d.length+' models'}
async function aiSave(){const r=await fetch('/api/admin/assistant',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({vendor:$('#aiv').value,model:$('#aim').value})});$('#aiout').textContent=r.ok?'Saved ✓':'Error '+r.status;aiLoad()}
async function aiTest(){$('#aiout').textContent='Testing…';const r=await fetch('/api/admin/assistant/test',{method:'POST'});const d=await r.json();$('#aiout').textContent=r.ok?'✓ '+d.reply:'✗ '+(d.error||r.status)}
async function users(){const r=await fetch('/api/admin/users',{cache:'no-store'});if(!r.ok){$('#users').textContent='Not allowed ('+r.status+')';return}const list=await r.json();
$('#ucount').textContent=list.length+' total · '+list.filter(u=>u.plan==='pro').length+' paid';$('#users').innerHTML='';
for(const u of list){const d=document.createElement('div');d.className='c';
const loc=u.locations.map(l=>ts(l.created)+(l.lat!=null?' · <a href="https://www.google.com/maps?q='+l.lat+','+l.lon+'">'+l.lat+', '+l.lon+'</a>':'')).join('<br>');
d.innerHTML='<div><b>'+esc(u.name)+'</b> · '+esc(u.email)+' · <span class="m">'+esc(u.plan)+'</span></div><div class="m">registered '+ts(u.created)+' · last active '+ts(u.lastActive)+' · syncs rev '+u.revision+' · feedback '+u.feedback+'</div>'
+'<div class="m">🔫 '+(u.rifles.length?esc(u.rifles.join(', ')):'no rifles synced')+'</div><div class="m">🎯 '+(u.ammo.length?esc(u.ammo.join(', ')):'no loads synced')+'</div>'
+(loc?'<details><summary class="m">📍 '+u.activity+' weather syncs</summary><div class="m">'+loc+'</div></details>':'');$('#users').appendChild(d)}}
</script></html>`;

const ASSISTANT_SYSTEM = `You are the built-in assistant of ballistics.ge, a ballistic calculator for long-range shooters and hunters.
Users write in plain words (usually Georgian, sometimes English or Russian). You can read the full app state and change ANY setting with tools.
Reply in the user's language, briefly (2-5 sentences).

IMPORTANT — confirmation flow: every change-making tool call is shown to the user as a proposal with Apply/Cancel buttons and runs only if they approve.
So before calling a change tool, say in one sentence what you are about to change and why. If a tool result says "declined", acknowledge it and ask what they'd like instead; do not retry the same change.
After an approved change, read new_solution_at_target in the result and tell the user the new dial/hold.

What you can do:
- Add equipment: "I have an AR-10 in .308 and Fiocchi 175 gr HPBT" → search_library first (query, caliber, grains). Pick the best match: an exact factory load ('ammo') if present; otherwise the bullet that load uses (e.g. many 175 gr .308 match loads use the Sierra MatchKing 175) and say it is an approximation. Then create_rifle (if they don't already have it) and create_ammo with library_id, a clear name like "Fiocchi 175 HPBT", and the factory muzzle velocity if you know it reliably (otherwise keep the library default and tell them to chronograph or true it). Ask for barrel twist / sight height only if it matters and they may know it; otherwise use sensible defaults (AR-10 .308: twist 1:11.25, sight height ~65 mm on an AR-style rail).
- Edit anything on a rifle or load: update_rifle / update_ammo (zero range, sight height, twist, MV, BC, drag model, weight, length, powder temp sensitivity...). Rename, delete, switch profiles.
- Range feedback: "dialled the app's solution at 600 m and hit 15 cm low" → true_from_impact. "At my 100 m zero I hit 3 cm high, 1 cm left" → set_zero_offset (that's a zero shift, not truing).
- Conditions: wind, range, temperature, pressure, humidity, altitude, angle, cant, moving target → set_conditions; "update the weather" → sync_weather. Wind direction is where the wind comes FROM in degrees true; for a clock position, from = shooting heading + clock×30.
- Scope/reticle: set_reticle (reticle from the options list, FFP/SFP, magnification range, true-at power). Display: set_settings (metric/imperial, MRAD/MOA, click value).
- Hit probability settings: set_hit_probability (group size, MV SD, wind-call error, target size).
- Questions ("what's my hold at 700?", "why is my BC G7?") → answer from the state without tools.

Photos (the user may attach up to 3):
- Ammo box / cartridge: read brand, product line, calibre, bullet weight and type, and the printed muzzle velocity (convert fps → m/s, ×0.3048). Then search_library and create_ammo (library_id of the same bullet if found, the box's MV, a name like "Fiocchi Exacta 175 HPBT"). Say which values you read from the box.
- Rifle: identify make/model/calibre only from what is visible (markings on the barrel or receiver are best). State your confidence. Propose create_rifle with the calibre and a typical twist for that model; ask the user to confirm the calibre if it is not legible.
- Scope: identify make/model and magnification range from markings; choose the closest reticle from state.settings.reticle.options and FFP/SFP, then set_reticle. If the reticle itself is not visible, ask which reticle it has.
- Target with bullet holes: you need the range, the scale and where they aimed. Use a known size in the photo (grid squares, ring spacing, target diameter) — if there is none, ask for one. Estimate the group centre offset from the aiming point in cm (+ high / + right) and the group's extreme spread in cm and MOA (MOA = cm / (range_m × 0.0291)). Then, depending on the situation, propose set_zero_offset (at zero range), true_from_impact (vertical miss at a longer range after dialling the app's solution), or set_hit_probability group_moa (to record their real group size). Be honest about uncertainty from photo angle and resolution; round to whole cm.
- Anything else shooting-related (a Kestrel screen, a DOPE card, a range card) → read the numbers and propose the matching changes.
Never identify people in photos; ignore faces.
Rules: never invent measured values — if unknown, ask one short question or use a clearly-labelled default. Keep changes to what the user asked for. Suggest confirming on paper when MV changes > 30 m/s or BC > 15%.
Respect the plan limits in state.plan. Nothing illegal or unsafe.
Sign conventions: vertical + = high, horizontal + = right, relative to the point of aim. All values SI (m, m/s, °C, mbar, cm, grains, inches for bullet dimensions and twist).`;
const num = (d) => ({ type: 'number', description: d });
const ASSISTANT_TOOLS = [
  { name: 'search_library', description: 'Search the built-in bullet/factory-ammo library (read-only, runs without confirmation).', input_schema: { type: 'object', properties: {
    query: { type: 'string', description: 'free text, e.g. "fiocchi hpbt" or "sierra matchking"' }, caliber: { type: 'string', description: 'e.g. ".308", "6.5 Creedmoor"' }, grains: num('bullet weight') } } },
  { name: 'create_rifle', description: 'Add a new rifle and select it.', input_schema: { type: 'object', required: ['name', 'chambering'], properties: {
    name: { type: 'string' }, chambering: { type: 'string', description: 'one of state.chamberings (fuzzy ok, e.g. "308")' }, zero_range_m: num(''), sight_height_mm: num('bore axis to scope centre'),
    twist_in: num('barrel twist, inches per turn'), twist_direction: { type: 'string', enum: ['right', 'left'] } } } },
  { name: 'create_ammo', description: 'Add a new load and select it. Use library_id from search_library to fill bullet data; any other field overrides.', input_schema: { type: 'object', properties: {
    library_id: { type: 'string' }, name: { type: 'string' }, cartridge: { type: 'string' }, drag_model: { type: 'string', enum: ['G1', 'G7'] }, bc: num(''), mass_grains: num(''),
    diameter_in: num(''), length_in: num('bullet length'), muzzle_velocity_mps: num(''), mv_temp_c: num('temperature at which MV was measured'), temp_sensitivity_pct_per_c: num('MV change per °C, %') } } },
  { name: 'update_rifle', description: 'Edit a rifle (selected one unless target_name given). Omit fields you do not change.', input_schema: { type: 'object', properties: {
    target_name: { type: 'string' }, name: { type: 'string', description: 'new name' }, chambering: { type: 'string' }, zero_range_m: num(''), sight_height_mm: num(''), twist_in: num(''),
    twist_direction: { type: 'string', enum: ['right', 'left'] }, zero_temp_c: num(''), zero_offset_vertical_cm: num('absolute value, + high'), zero_offset_horizontal_cm: num('absolute value, + right') } } },
  { name: 'update_ammo', description: 'Edit a load (selected one unless target_name given). Omit fields you do not change.', input_schema: { type: 'object', properties: {
    target_name: { type: 'string' }, name: { type: 'string', description: 'new name' }, cartridge: { type: 'string' }, drag_model: { type: 'string', enum: ['G1', 'G7'] }, bc: num(''), mass_grains: num(''),
    diameter_in: num(''), length_in: num(''), muzzle_velocity_mps: num(''), mv_temp_c: num(''), temp_sensitivity_pct_per_c: num('') } } },
  { name: 'delete_profile', description: 'Delete a rifle or load by name.', input_schema: { type: 'object', required: ['kind', 'name'], properties: { kind: { type: 'string', enum: ['rifle', 'ammo'] }, name: { type: 'string' } } } },
  { name: 'select_profile', description: 'Switch rifle and/or load by (partial) name.', input_schema: { type: 'object', properties: { rifle_name: { type: 'string' }, ammo_name: { type: 'string' } } } },
  { name: 'set_conditions', description: 'Change shooting conditions. Omit fields you do not change.', input_schema: { type: 'object', properties: {
    target_range_m: num(''), wind_speed_mps: num(''), wind_from_deg: num('direction wind blows FROM, degrees true'), shooting_heading_deg: num(''), temperature_c: num(''),
    pressure_mbar: num('station pressure'), humidity_pct: num(''), altitude_m: num(''), shot_angle_deg: num('+ uphill'), cant_deg: num('+ right'),
    target_speed_kmh: num('moving target, 0 = stationary'), target_moving: { type: 'string', enum: ['left_to_right', 'right_to_left'] } } } },
  { name: 'sync_weather', description: 'Fetch current weather for the saved location and apply it.', input_schema: { type: 'object', properties: {} } },
  { name: 'true_from_impact', description: 'User dialled/held the app solution at a range and the group landed off vertically. Trues MV (<=500 m) or BC (beyond) so predictions match.', input_schema: { type: 'object', required: ['range_m', 'impact_vertical_cm'], properties: {
    range_m: num(''), impact_vertical_cm: num('+ high, - low'), method: { type: 'string', enum: ['auto', 'velocity', 'bc'] } } } },
  { name: 'set_zero_offset', description: 'Rifle does not hit point of aim AT ITS ZERO RANGE. Adds (default) or sets the offset.', input_schema: { type: 'object', properties: {
    vertical_cm: num('+ high'), horizontal_cm: num('+ right'), add: { type: 'boolean' } } } },
  { name: 'set_reticle', description: 'Scope and reticle settings.', input_schema: { type: 'object', properties: {
    reticle: { type: 'string', description: 'one of state.settings.reticle.options (partial ok)' }, focal_plane: { type: 'string', enum: ['FFP', 'SFP'] },
    true_at_mag: num('SFP: power where the reticle is true'), current_mag: num(''), scope_min_mag: num(''), scope_max_mag: num('') } } },
  { name: 'set_settings', description: 'Display settings.', input_schema: { type: 'object', properties: {
    units: { type: 'string', enum: ['metric', 'imperial'] }, angular: { type: 'string', enum: ['MRAD', 'MOA'] }, click: { type: 'string', description: 'one of state.settings.click_options' } } } },
  { name: 'set_hit_probability', description: 'Hit-probability model inputs.', input_schema: { type: 'object', properties: {
    group_moa: num('5-shot group at 100'), mv_sd_mps: num(''), wind_error_mps: num('wind-call uncertainty 1σ'), range_error_pct: num(''), target_width_cm: num(''), target_height_cm: num(''),
    shape: { type: 'string', enum: ['rect', 'ellipse'] } } } },
];

export function app({ db, origin, clientId, clientSecret, webRoot, adminEmails = [], paddle = {}, assistant = {}, google = new OAuth2Client(clientId, clientSecret, `${origin}/auth/google/callback`) }) {
  const admins = new Set(adminEmails.map(e => e.trim().toLowerCase()).filter(Boolean));
  const secure = new URL(origin).protocol === 'https:';
  const cookie = (name, value, age) => `${name}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${age}${secure ? '; Secure' : ''}`;
  const ready = Boolean(clientId && clientSecret);
  // paddle: { required, clientToken, priceId, env ('sandbox'|'production'), webhookSecret }
  const proRequired = Boolean(paddle.required);
  const aiKeys = assistant.keys || {};
  const aiFetch = assistant.fetch || fetch;
  const DEFAULT_MODEL = { anthropic: assistant.model || 'claude-haiku-4-5-20251001' };
  const getSetting = k => { try { return JSON.parse(db.prepare('SELECT value FROM app_settings WHERE key=?').get(k)?.value ?? 'null'); } catch { return null; } };
  const aiChoice = () => {
    const saved = getSetting('assistant');
    if (saved?.vendor && aiKeys[saved.vendor] && saved.model) return saved;
    for (const v of ['anthropic', 'openai', 'gemini']) if (aiKeys[v] && DEFAULT_MODEL[v]) return { vendor: v, model: DEFAULT_MODEL[v] };
    return null;
  };
  const modelCache = new Map();
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
        if (user && !(user.last_seen > now - 600)) db.prepare('UPDATE accounts SET last_seen=? WHERE id=?').run(now, user.id);
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
          if (url.pathname === '/api/admin/assistant' && req.method === 'GET') {
            const day = new Date().toISOString().slice(0, 10);
            const today = db.prepare('SELECT COALESCE(SUM(count),0) AS n, COUNT(*) AS users FROM assistant_usage WHERE day=?').get(day);
            return json(200, { vendors: Object.entries(VENDORS).map(([id, v]) => ({ id, label: v.label, env: v.env, enabled: Boolean(aiKeys[id]) })), current: aiChoice(), today });
          }
          if (url.pathname === '/api/admin/assistant/models' && req.method === 'GET') {
            const v = url.searchParams.get('vendor');
            if (!aiKeys[v]) return json(400, { error: 'no_key' });
            const hit = modelCache.get(v); if (hit && hit.t > Date.now() - 3600e3) return json(200, hit.list);
            try { const list = await listModels(v, aiKeys[v], aiFetch); modelCache.set(v, { t: Date.now(), list }); return json(200, list); }
            catch (e) { return json(502, { error: String(e?.message || e).slice(0, 200) }); }
          }
          if (url.pathname === '/api/admin/assistant' && req.method === 'POST') {
            let b; try { b = JSON.parse((await readBody(req, 4096)).toString('utf8')); } catch { return json(400, { error: 'json' }); }
            if (!aiKeys[b?.vendor] || typeof b.model !== 'string' || !b.model || b.model.length > 120) return json(400, { error: 'invalid' });
            db.prepare('INSERT INTO app_settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value').run('assistant', JSON.stringify({ vendor: b.vendor, model: b.model }));
            return json(200, { ok: true, current: aiChoice() });
          }
          if (url.pathname === '/api/admin/assistant/test' && req.method === 'POST') {
            const c = aiChoice(); if (!c) return json(400, { error: 'not_configured' });
            try { const out = await ADAPTERS[c.vendor]({ key: aiKeys[c.vendor], model: c.model, system: 'Reply with one short sentence.', state: '', tools: ASSISTANT_TOOLS, messages: [{ role: 'user', content: 'Say hello in Georgian.' }], fetch: aiFetch });
              return json(200, { ok: true, reply: out.content.filter(x => x.type === 'text').map(x => x.text).join(' ').slice(0, 300) }); }
            catch (e) { return json(502, { error: String(e?.message || e).slice(0, 300) }); }
          }
          if (url.pathname === '/api/admin/users' && req.method === 'GET') {
            const rows = db.prepare(`SELECT a.id,a.email,a.name,a.plan,a.created,a.plan_since,p.revision,p.data,
                (SELECT COUNT(*) FROM feedback f WHERE f.account=a.id) AS feedback,
                (SELECT COUNT(*) FROM activity x WHERE x.account=a.id) AS activity,
                MAX(COALESCE((SELECT MAX(created) FROM activity x WHERE x.account=a.id),0), COALESCE(a.last_seen,0)) AS lastActive
              FROM accounts a LEFT JOIN profiles p ON p.account=a.id ORDER BY a.created DESC, a.rowid DESC LIMIT 2000`).all();
            const last = db.prepare('SELECT created,kind,lat,lon FROM activity WHERE account=? ORDER BY created DESC LIMIT 20');
            return json(200, rows.map(r => { let d = {}; try { d = JSON.parse(r.data || '{}'); } catch {}
              return { id: r.id, email: r.email, name: r.name, plan: r.plan, created: r.created || null, planSince: r.plan_since, revision: r.revision || 0,
                rifles: (d.rifles || []).map(x => `${x.name || '?'} (${x.chambering || '?'})`), ammo: (d.ammo || []).map(x => `${x.name || '?'} (${x.cartridge || '?'})`),
                feedback: r.feedback, activity: r.activity, lastActive: r.lastActive || null, locations: last.all(r.id) }; }));
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
        if (url.pathname === '/api/assistant' && req.method === 'POST') {
          const choice = aiChoice(); if (!choice) return json(503, { error: 'assistant_disabled' });
          let b; try { b = JSON.parse((await readBody(req, 6 * 1024 * 1024)).toString('utf8')); } catch { return json(400, { error: 'json' }); }
          const msgs = Array.isArray(b?.messages) ? b.messages.slice(-24) : null;
          if (!msgs?.length || msgs[0].role !== 'user') return json(400, { error: 'messages' });
          // Photos: at most 3 per request, JPEG/PNG/WebP, ≤ 1.5 MB each (the client downsizes to ~1600 px).
          const images = msgs.flatMap(m => Array.isArray(m.content) ? m.content.filter(c => c?.type === 'image') : []);
          if (images.length > 3 || images.some(c => c.source?.type !== 'base64' || !['image/jpeg', 'image/png', 'image/webp'].includes(c.source.media_type) || typeof c.source.data !== 'string' || c.source.data.length > 2_000_000))
            return json(400, { error: 'images' });
          const last = msgs[msgs.length - 1];
          const newTurn = last.role === 'user' && (typeof last.content === 'string' || !last.content.some?.(c => c.type === 'tool_result'));
          const day = new Date().toISOString().slice(0, 10), limit = assistant.dailyLimit ?? 30;
          const used = db.prepare('SELECT count FROM assistant_usage WHERE account=? AND day=?').get(user.id, day)?.count ?? 0;
          if (newTurn && used >= limit) return json(429, { error: 'daily_limit', limit });
          if (newTurn) db.prepare('INSERT INTO assistant_usage VALUES (?,?,1) ON CONFLICT(account,day) DO UPDATE SET count=count+1').run(user.id, day);
          const state = typeof b.state === 'string' ? b.state.slice(0, 12000) : '';
          try {
            const out = await ADAPTERS[choice.vendor]({ key: aiKeys[choice.vendor], model: choice.model, system: ASSISTANT_SYSTEM, state: `Current app state (JSON, SI units):\n${state}`, tools: ASSISTANT_TOOLS, messages: msgs, fetch: aiFetch });
            return json(200, { ...out, remaining: Math.max(0, limit - used - (newTurn ? 1 : 0)) });
          } catch (e) { console.error('assistant', choice.vendor, choice.model, e?.message); return json(502, { error: 'upstream', detail: String(e?.message || '').slice(0, 200) }); }
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
