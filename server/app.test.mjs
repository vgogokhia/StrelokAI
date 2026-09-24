import { test } from 'node:test';
import assert from 'node:assert/strict';
import { app, database, hash } from './app.mjs';
const origin = 'http://localhost:8080';
async function setup(t, google) {
  const db = database(':memory:');
  db.prepare('INSERT INTO accounts (id,email,name) VALUES (?,?,?)').run('alice', 'a@example.test', 'Alice');
  db.prepare('INSERT INTO accounts (id,email,name) VALUES (?,?,?)').run('bob', 'b@example.test', 'Bob');
  for (const name of ['alice', 'bob']) db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash(name), name, Math.floor(Date.now()/1000)+60);
  const server = app({ db, origin, clientId: 'test-client', clientSecret: 'test-secret', webRoot: '../web/dist', google });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  t.after(() => new Promise(resolve => server.close(() => { db.close(); resolve(); })));
  const request = (path, options={}) => fetch(`http://127.0.0.1:${server.address().port}${path}`, { redirect: 'manual', ...options });
  return { db, request };
}
const headers = name => ({ Cookie: `bge_session=${name}`, Origin: origin, 'X-Account-Id': name, 'Content-Type': 'application/json' });
const data = { rifles: [{ id: 'one', name: 'Profile' }], ammo: [] };
test('accounts isolate data, reject forged identity and enforce revision/CSRF', async t => {
  const { request } = await setup(t);
  assert.equal((await request('/api/profiles')).status, 401);
  assert.equal((await request('/api/profiles', { headers: { ...headers('alice'), 'X-Account-Id': 'bob' } })).status, 409);
  const put = (name, revision, extra={}) => request('/api/profiles', { method:'PUT', headers:{...headers(name),...extra}, body:JSON.stringify({ revision,data }) });
  assert.equal((await put('alice',0,{Origin:'https://evil.test'})).status,403);
  assert.equal((await put('alice',0)).status,200);
  assert.equal((await put('alice',0)).status,409);
  assert.deepEqual(await (await request('/api/profiles',{headers:headers('bob')})).json(), {revision:0,data:{rifles:[],ammo:[]}});
  assert.deepEqual((await (await request('/api/profiles',{headers:headers('alice')})).json()).data,data);
  assert.equal((await put('alice',1)).status,200);
  assert.equal((await put('alice',1)).status,409);
  assert.equal((await request('/api/logout',{method:'POST',headers:headers('alice')})).status,200);
  assert.equal((await request('/api/profiles',{headers:headers('alice')})).status,401);
});
test('Google callback binds state, nonce and browser; rotates session; consumes callback', async t => {
  let params;
  const google = { generateAuthUrl(p) { params=p;return 'https://accounts.google.com/test'; },
    async getToken(p) { assert.ok(p.codeVerifier); return {tokens:{id_token:'verified-by-test-adapter'}}; },
    async verifyIdToken(p) { assert.equal(p.audience,'test-client'); return {getPayload:()=>({sub:'google-user',email:'g@example.test',name:'G',email_verified:true,nonce:params.nonce})}; } };
  const {request} = await setup(t,google);
  const start = await request('/auth/google');
  assert.equal(start.status,302);assert.equal(params.code_challenge_method,'S256');
  const cookie = start.headers.get('set-cookie').split(';')[0];
  const path = `/auth/google/callback?state=${params.state}&code=code`;
  assert.equal((await request(path)).headers.get('location'),'/?auth=failed');
  const callback = await request(path,{headers:{Cookie:cookie}});
  assert.equal(callback.headers.get('location'),'/?auth=success');
  const session = callback.headers.getSetCookie().find(c=>c.startsWith('bge_session='));
  assert.match(session,/HttpOnly/);assert.match(session,/SameSite=Lax/);
  const account = await (await request('/api/account',{headers:{Cookie:session.split(';')[0]}})).json();
  assert.equal(account.user.id,'google-user');
  assert.equal((await request(path,{headers:{Cookie:cookie}})).headers.get('location'),'/?auth=failed');
});
test('invalid nonce and malformed snapshots rejected', async t => {
  let params;
  const google = {generateAuthUrl(p){params=p;return 'https://accounts.google.com/test';},async getToken(){return {tokens:{id_token:'x'}};},async verifyIdToken(){return {getPayload:()=>({sub:'x',email_verified:true,nonce:'wrong'})};}};
  const {request} = await setup(t,google);
  const start=await request('/auth/google');
  const response=await request(`/auth/google/callback?code=x&state=${params.state}`,{headers:{Cookie:start.headers.get('set-cookie').split(';')[0]}});
  assert.equal(response.headers.get('location'),'/?auth=failed');
  for(const body of ['null','{}','broken',JSON.stringify({revision:0,data:{rifles:[{id:'x',name:'a'},{id:'x',name:'b'}],ammo:[]}})])
    assert.equal((await request('/api/profiles',{method:'PUT',headers:headers('alice'),body})).status,400);
});
test('profiles survive database reopen and expired sessions cannot read', async t => {
  const { mkdtempSync, rmSync } = await import('node:fs');
  const { tmpdir } = await import('node:os');
  const { join } = await import('node:path');
  const dir = mkdtempSync(join(tmpdir(), 'bge-accounts-'));
  t.after(() => rmSync(dir, {recursive:true,force:true}));
  const path = join(dir,'accounts.sqlite');
  let db = database(path);
  db.prepare('INSERT INTO accounts (id,email,name) VALUES (?,?,?)').run('owner','owner@example.test','Owner');
  db.prepare('INSERT INTO profiles VALUES (?,?,?)').run('owner',7,JSON.stringify(data));
  db.close();
  db=database(path);
  assert.deepEqual(JSON.parse(db.prepare('SELECT data FROM profiles WHERE account=?').get('owner').data),data);
  db.close();
  const setupResult = await setup(t);
  setupResult.db.prepare('UPDATE sessions SET expires=0').run();
  assert.equal((await setupResult.request('/api/profiles',{headers:headers('alice')})).status,401);
});
test('UTF-8 profile names survive network chunk boundaries', async t => {
  const { request: httpRequest } = await import('node:http');
  const db = database(':memory:');
  db.prepare('INSERT INTO accounts (id,email,name) VALUES (?,?,?)').run('alice','a@example.test','Alice');
  db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash('alice'),'alice',Math.floor(Date.now()/1000)+60);
  const server=app({db,origin,webRoot:'../web/dist'});
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  t.after(()=>new Promise(resolve=>server.close(()=>{db.close();resolve();})));
  const payload=Buffer.from(JSON.stringify({revision:0,data:{rifles:[{id:'one',name:'ქართული პროფილი'}],ammo:[]}}));
  const split=payload.indexOf(Buffer.from('ქ'))+1;
  const status=await new Promise((resolve,reject)=>{
    const req=httpRequest({hostname:'127.0.0.1',port:server.address().port,path:'/api/profiles',method:'PUT',headers:headers('alice')},res=>{res.resume();res.on('end',()=>resolve(res.statusCode));});
    req.on('error',reject);req.write(payload.subarray(0,split));setImmediate(()=>req.end(payload.subarray(split)));
  });
  assert.equal(status,200);
  assert.equal(JSON.parse(db.prepare('SELECT data FROM profiles').get().data).rifles[0].name,'ქართული პროფილი');
});

test('paddle webhook upgrades the account only with a valid signature', async t => {
  const { createHmac } = await import('node:crypto');
  const db = database(':memory:');
  db.prepare("INSERT INTO accounts (id,email,name,plan) VALUES (?,?,?,?)").run('carol', 'c@example.test', 'Carol', 'free');
  db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash('carol'), 'carol', Math.floor(Date.now()/1000)+60);
  const server = app({ db, origin, clientId: 'x', clientSecret: 'y', webRoot: '../web/dist', paddle: { required: true, webhookSecret: 'whsec', priceId: 'pri_1', clientToken: 'tok' } });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise(r => server.close(() => { db.close(); r(); })));
  const base = `http://127.0.0.1:${server.address().port}`;
  const body = JSON.stringify({ event_id: 'evt_1', event_type: 'transaction.completed', data: { id: 'txn_1', currency_code: 'USD', details: { totals: { total: '500' } }, custom_data: { account_id: 'carol' } } });
  const ts = Math.floor(Date.now()/1000);
  const sign = secret => `ts=${ts};h1=${createHmac('sha256', secret).update(`${ts}:${body}`).digest('hex')}`;
  let r = await fetch(`${base}/api/paddle/webhook`, { method: 'POST', body, headers: { 'Paddle-Signature': sign('wrong') } });
  assert.equal(r.status, 401);
  assert.equal(db.prepare('SELECT plan FROM accounts WHERE id=?').get('carol').plan, 'free');
  r = await fetch(`${base}/api/paddle/webhook`, { method: 'POST', body, headers: { 'Paddle-Signature': sign('whsec') } });
  assert.equal(r.status, 200);
  assert.equal(db.prepare('SELECT plan FROM accounts WHERE id=?').get('carol').plan, 'pro');
  const acct = await (await fetch(`${base}/api/account`, { headers: { Cookie: 'bge_session=carol' } })).json();
  assert.equal(acct.user.pro, true);
  assert.equal(acct.billing.required, true);
  assert.equal(db.prepare('SELECT COUNT(*) AS n FROM purchases').get().n, 1);
});

test('assistant proxies to Anthropic with server-side tools and enforces sign-in and daily limit', async t => {
  const db = database(':memory:');
  db.prepare("INSERT INTO accounts (id,email,name) VALUES ('dan','d@example.test','Dan')").run();
  db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash('dan'), 'dan', Math.floor(Date.now()/1000)+60);
  let sent;
  const fakeFetch = async (_url, init) => { sent = JSON.parse(init.body); return { ok: true, json: async () => ({ content: [{ type: 'text', text: 'ok' }], stop_reason: 'end_turn' }) }; };
  const server = app({ db, origin, clientId: 'x', clientSecret: 'y', webRoot: '../web/dist', assistant: { keys: { anthropic: 'k' }, fetch: fakeFetch, dailyLimit: 1 } });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise(r => server.close(() => { db.close(); r(); })));
  const base = `http://127.0.0.1:${server.address().port}`;
  const body = JSON.stringify({ messages: [{ role: 'user', content: '600-ზე 15 სმ-ით დაბლა მოხვდა' }], state: '{}' });
  let r = await fetch(`${base}/api/assistant`, { method: 'POST', body, headers: { Origin: origin } });
  assert.equal(r.status, 401);
  const h = { Origin: origin, Cookie: 'bge_session=dan' };
  r = await fetch(`${base}/api/assistant`, { method: 'POST', body, headers: h });
  assert.equal(r.status, 200);
  assert.equal((await r.json()).content[0].text, 'ok');
  assert.ok(sent.tools.some(x => x.name === 'true_from_impact'));
  r = await fetch(`${base}/api/assistant`, { method: 'POST', body, headers: h });
  assert.equal(r.status, 429);
});

test('admin picks vendor/model; openai and gemini adapters translate tool calls both ways', async t => {
  const db = database(':memory:');
  db.prepare("INSERT INTO accounts (id,email,name) VALUES ('adm','boss@example.test','Boss')").run();
  db.prepare('INSERT INTO sessions VALUES (?,?,?)').run(hash('adm'), 'adm', Math.floor(Date.now()/1000)+60);
  const calls = [];
  const fakeFetch = async (url, init) => {
    const body = init?.body ? JSON.parse(init.body) : null; calls.push({ url: String(url), body });
    if (String(url).includes('api.openai.com/v1/models')) return { ok: true, json: async () => ({ data: [{ id: 'gpt-test-mini', created: 2 }, { id: 'text-embedding-x', created: 3 }, { id: 'whisper-1', created: 1 }] }) };
    if (String(url).includes('generativelanguage') && String(url).includes('/models?')) return { ok: true, json: async () => ({ models: [{ name: 'models/gemini-test-flash', displayName: 'Gemini Test Flash', supportedGenerationMethods: ['generateContent'] }, { name: 'models/text-embedding', supportedGenerationMethods: ['embedContent'] }] }) };
    if (String(url).includes('chat/completions')) {
      const hasTool = body.messages.some(m => m.role === 'tool');
      return { ok: true, json: async () => ({ choices: [{ message: hasTool ? { content: 'done' } : { content: 'Adding it.', tool_calls: [{ id: 'call_1', type: 'function', function: { name: 'set_conditions', arguments: '{"wind_speed_mps":4}' } }] } }] }) };
    }
    if (String(url).includes(':generateContent')) {
      const last = body.contents.at(-1);
      return { ok: true, json: async () => ({ candidates: [{ content: { parts: last.parts[0].functionResponse ? [{ text: 'ok' }] : [{ functionCall: { name: 'sync_weather', args: {} }, thoughtSignature: 'SIG' }] } }] }) };
    }
    return { ok: false, status: 500, json: async () => ({}) };
  };
  const server = app({ db, origin, clientId: 'x', clientSecret: 'y', webRoot: '../web/dist', adminEmails: ['boss@example.test'], assistant: { keys: { openai: 'o', gemini: 'g' }, fetch: fakeFetch } });
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise(r => server.close(() => { db.close(); r(); })));
  const base = `http://127.0.0.1:${server.address().port}`, h = { Origin: origin, Cookie: 'bge_session=adm', 'content-type': 'application/json' };
  let r = await (await fetch(`${base}/api/admin/assistant`, { headers: h })).json();
  assert.equal(r.current, null);                                                   // no Anthropic key and nothing chosen yet
  assert.deepEqual(r.vendors.filter(v => v.enabled).map(v => v.id), ['openai', 'gemini']);
  assert.deepEqual((await (await fetch(`${base}/api/admin/assistant/models?vendor=openai`, { headers: h })).json()).map(m => m.id), ['gpt-test-mini']);
  assert.deepEqual((await (await fetch(`${base}/api/admin/assistant/models?vendor=gemini`, { headers: h })).json()).map(m => m.id), ['gemini-test-flash']);
  assert.equal((await fetch(`${base}/api/admin/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ vendor: 'anthropic', model: 'x' }) })).status, 400);

  // OpenAI round trip
  await fetch(`${base}/api/admin/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ vendor: 'openai', model: 'gpt-test-mini' }) });
  let a = await (await fetch(`${base}/api/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ messages: [{ role: 'user', content: 'wind 4' }], state: '{}' }) })).json();
  assert.equal(a.stop_reason, 'tool_use'); assert.deepEqual(a.content[1], { type: 'tool_use', id: 'call_1', name: 'set_conditions', input: { wind_speed_mps: 4 } });
  const hist = [{ role: 'user', content: 'wind 4' }, { role: 'assistant', content: a.content }, { role: 'user', content: [{ type: 'tool_result', tool_use_id: 'call_1', content: '{"ok":true}' }] }];
  a = await (await fetch(`${base}/api/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ messages: hist, state: '{}' }) })).json();
  assert.equal(a.content[0].text, 'done');
  const sent = calls.filter(c => c.url.includes('chat/completions')).at(-1).body;
  assert.equal(sent.model, 'gpt-test-mini'); assert.equal(sent.messages.at(-1).role, 'tool'); assert.equal(sent.messages.at(-2).tool_calls[0].function.name, 'set_conditions');

  // Gemini round trip keeps the thought signature and maps the function name back
  await fetch(`${base}/api/admin/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ vendor: 'gemini', model: 'gemini-test-flash' }) });
  a = await (await fetch(`${base}/api/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ messages: [{ role: 'user', content: 'weather' }], state: '{}' }) })).json();
  const tu = a.content[0]; assert.equal(tu.name, 'sync_weather'); assert.equal(tu._sig, 'SIG');
  a = await (await fetch(`${base}/api/assistant`, { method: 'POST', headers: h, body: JSON.stringify({ messages: [{ role: 'user', content: 'weather' }, { role: 'assistant', content: [tu] }, { role: 'user', content: [{ type: 'tool_result', tool_use_id: tu.id, content: '{"ok":true}' }] }], state: '{}' }) })).json();
  assert.equal(a.content[0].text, 'ok');
  const g = calls.filter(c => c.url.includes(':generateContent')).at(-1).body;
  assert.equal(g.contents[1].parts[0].thoughtSignature, 'SIG'); assert.equal(g.contents[2].parts[0].functionResponse.name, 'sync_weather');
  assert.ok(!g.tools[0].functionDeclarations.find(f => f.name === 'sync_weather').parameters);
});
