import { beforeEach, afterEach, it, expect, vi } from 'vitest';
let memory: Map<string,string>;
beforeEach(() => {
  vi.resetModules(); memory = new Map();
  vi.stubGlobal('localStorage', {getItem:(k:string)=>memory.get(k)??null,setItem:(k:string,v:string)=>memory.set(k,v),removeItem:(k:string)=>memory.delete(k)});
});
afterEach(() => vi.unstubAllGlobals());
it('imports original guest records once and isolates subsequent accounts', async () => {
  const first = await import('../src/lib/store.svelte');
  first.store.rifles[0].name = 'Guest original'; first.store.persist();
  vi.resetModules();
  const {store} = await import('../src/lib/store.svelte');
  expect(store.switchOwner('alice')).toBe(true);
  expect(store.rifles[0].name).toBe('Guest original');
  store.rifles[0].name='Alice private'; store.persist();
  expect(store.switchOwner('bob')).toBe(false);
  expect(store.rifles[0].name).not.toBe('Alice private');
  expect(store.rifles[0].name).not.toBe('Guest original');
  store.switchOwner('alice'); expect(store.rifles[0].name).toBe('Alice private');
  store.switchOwner(''); expect(store.rifles[0].name).toBe('Guest original');
});
it('a new device does not import generated defaults and rejects malformed profiles', async () => {
  const {store} = await import('../src/lib/store.svelte');
  store.persist();
  expect(store.switchOwner('alice')).toBe(false);
  expect(()=>store.applyProfiles({rifles:[{id:'x',name:'broken'}],ammo:[]})).toThrow('Invalid profile data');
});
