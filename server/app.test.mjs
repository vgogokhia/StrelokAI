import { test } from 'node:test';
import assert from 'node:assert/strict';
import { app, database, hash } from './app.mjs';
const origin = 'http://localhost:8080';
async function setup(t, google) {
  const db = database(':memory:');
  db.prepare('INSERT INTO accounts VALUES (?,?,?)').run('alice', 'a@example.test', 'Alice');
  db.prepare('INSERT INTO accounts VALUES (?,?,?)').run('bob', 'b@example.test', 'Bob');
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
  db.prepare('INSERT INTO accounts VALUES (?,?,?)').run('owner','owner@example.test','Owner');
  db.prepare('INSERT INTO profiles VALUES (?,?,?)').run('owner',7,JSON.stringify(data));
  db.close();
  db=database(path);
  assert.deepEqual(JSON.parse(db.prepare('SELECT data FROM profiles WHERE account=?').get('owner').data),data);
  db.close();
  const setupResult = await setup(t);
  setupResult.db.prepare('UPDATE sessions SET expires=0').run();
  assert.equal((await setupResult.request('/api/profiles',{headers:headers('alice')})).status,401);
});
