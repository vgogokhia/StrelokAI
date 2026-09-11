import { createServer } from 'node:http';
import { randomBytes, createHash } from 'node:crypto';
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
    CREATE TABLE IF NOT EXISTS profiles (account TEXT PRIMARY KEY REFERENCES accounts(id), revision INTEGER NOT NULL, data TEXT NOT NULL);`);
  return db;
}
export function app({ db, origin, clientId, clientSecret, webRoot, google = new OAuth2Client(clientId, clientSecret, `${origin}/auth/google/callback`) }) {
  const secure = new URL(origin).protocol === 'https:';
  const cookie = (name, value, age) => `${name}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${age}${secure ? '; Secure' : ''}`;
  const ready = Boolean(clientId && clientSecret);
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
          db.prepare('INSERT INTO accounts VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET email=excluded.email,name=excluded.name')
            .run(identity.sub, identity.email, identity.name || identity.email);
          const session = token();
          if (cookies.bge_session) db.prepare('DELETE FROM sessions WHERE id = ?').run(hash(cookies.bge_session));
          db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash(session), identity.sub, now + ttl);
          res.setHeader('Set-Cookie', [cookie('bge_oauth', '', 0), cookie('bge_session', session, ttl)]);
          return redirect('/?auth=success');
        } catch { return redirect('/?auth=failed'); }
      }
      if (url.pathname.startsWith('/api/')) {
        const user = db.prepare('SELECT accounts.* FROM sessions JOIN accounts ON accounts.id=sessions.account WHERE sessions.id=? AND expires>?').get(hash(cookies.bge_session || ''), now);
        if (url.pathname === '/api/account' && req.method === 'GET') return json(200, { user: user || null, googleEnabled: ready });
        if (!user) return json(401, { error: 'sign_in_required' });
        if (url.pathname === '/api/logout' && req.method === 'POST') {
          db.prepare('DELETE FROM sessions WHERE id=?').run(hash(cookies.bge_session));
          res.setHeader('Set-Cookie', cookie('bge_session', '', 0));
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
