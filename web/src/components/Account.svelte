<script lang="ts">
  import { onMount } from 'svelte';
  import { store } from '../lib/store.svelte';
  import { emptyProfiles, mergeProfiles, type ProfileData } from '../lib/profile-sync';
  let user = $state<{ id: string; email: string; name: string } | null>(null);
  let enabled = $state(false);
  let status = $state('Checking your account…');
  let open = $state(false);
  let busy = $state(false);
  let initialized = false;
  let base: ProfileData = emptyProfiles();
  let localOnFirstSync: ProfileData | null = null;
  const cacheKey = (id: string) => `bge_sync_${id}`;
  const saveBase = () => { if (user) localStorage.setItem(cacheKey(user.id), JSON.stringify(base)); };
  async function request(path: string, options: RequestInit = {}) {
    const response = await fetch(path, { ...options, cache: 'no-store', headers: { 'X-Account-Id': user?.id || '', ...options.headers } });
    if (!response.ok) {
      const problem = await response.json().catch(() => ({}));
      throw new Error(problem.error === 'account_changed' ? 'account_changed' : String(response.status));
    }
    return response.json();
  }
  async function sync() {
    if (!user || busy || !initialized) return;
    busy = true;
    try {
      const displayedBefore = store.profileData();
      const local = localOnFirstSync || displayedBefore;
      const remote = await request('/api/profiles');
      const merged = mergeProfiles(base, local, remote.data);
      if (JSON.stringify(merged) !== JSON.stringify(remote.data)) {
        await request('/api/profiles', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: remote.revision, data: merged }) });
      }
      // Changes made while the request was in flight remain local and are sent next time.
      const applied = mergeProfiles(displayedBefore, store.profileData(), merged);
      base = merged;
      saveBase();
      if (JSON.stringify(applied) !== JSON.stringify(store.profileData())) store.applyProfiles(applied);
      localOnFirstSync = null;
      status = 'Profiles synced';
    } catch (error) {
      const code = (error as Error).message;
      if (code === '401' || code === 'account_changed') { user = null; initialized = false; }
      status = code === '401' ? 'Your session has expired. Sign in again. Changes are saved on this device.'
        : code === 'account_changed' ? 'Your account has changed. Checking your sign-in again.'
        : code === '409' ? 'Your account or profiles have changed. Please try syncing again.'
        : 'Could not sync. Changes are saved on this device.';
    } finally { busy = false; }
  }
  async function initialize() {
    try {
      const account = await request('/api/account');
      enabled = account.googleEnabled;
      user = account.user;
      if (user) {
        let hasLocal = store.hasSavedProfiles;
        if (store.owner !== user.id) hasLocal = store.switchOwner(user.id);
        localOnFirstSync = hasLocal ? null : emptyProfiles();
        try { base = hasLocal ? JSON.parse(localStorage.getItem(cacheKey(user.id)) || 'null') || emptyProfiles() : emptyProfiles(); } catch { base = emptyProfiles(); }
        initialized = true;
        await sync();
      } else {
        status = store.owner ? 'Sign in again to sync. Profiles are saved on this device.' : 'Save your profiles to your account and access them on other devices.';
      }
      const params = new URLSearchParams(location.search);
      if (params.has('auth')) {
        if (params.get('auth') === 'failed') { status = 'Google sign-in could not be completed. Please try again.'; open = true; }
        params.delete('auth');
        history.replaceState(null, '', location.pathname + (params.size ? '?' + params : '') + location.hash);
      }
    } catch { status = 'Could not connect. Your local profiles are still available.'; }
  }
  async function logout() {
    if (busy) return;
    busy = true;
    try {
      await request('/api/logout', { method: 'POST' });
      store.switchOwner('');
      user = null; initialized = false; base = emptyProfiles();
      status = 'Signed out. A local copy of your account profiles is retained.';
    } catch { status = 'Could not sign out. Check your connection and try again.'; }
    finally { busy = false; }
  }
  onMount(() => {
    void initialize();
    const refresh = () => { if (!user) void initialize(); else void sync(); };
    const interval = setInterval(refresh, 15000);
    window.addEventListener('online', refresh);
    window.addEventListener('focus', refresh);
    return () => { clearInterval(interval); window.removeEventListener('online', refresh); window.removeEventListener('focus', refresh); };
  });
  let timer: ReturnType<typeof setTimeout>;
  $effect(() => {
    void JSON.stringify([store.rifles, store.ammo]);
    clearTimeout(timer);
    timer = setTimeout(() => { if (initialized) void sync(); }, 1500);
    return () => clearTimeout(timer);
  });
</script>

<div class="account-bar">
  <a href="/" class="brand" aria-label="Ballistics.ge home"><img src="/brand/ballistics-logo.png" alt="Ballistics.ge" width="1200" height="520" fetchpriority="high" /></a>
  <button class="small" onclick={() => open = !open} aria-expanded={open}>{user ? 'My account' : 'Sign in'}</button>
</div>
{#if open}
  <section class="card" aria-label="Account">
    <h2>{user ? user.name : 'Your profiles, on every device'}</h2>
    {#if user}<p class="muted">{user.email}</p>{/if}
    <p class="muted" role="status">{status}</p>
    {#if user}
      <div class="row"><button onclick={sync} disabled={busy}>Sync now</button><button onclick={logout} disabled={busy}>Sign out</button></div>
      <p class="muted">Conflicting edits keep both versions. Offline changes upload when you reconnect.</p>
    {:else if enabled}
      <a class="btn google" href="/auth/google" onclick={() => store.persist()}>Sign in with Google</a>
      <p class="muted">When you first sign in, existing profiles on this device are also added to your account.</p>
    {:else}
      <p class="muted">Google sign-in is not available yet. Profiles are saved on this device.</p>
    {/if}
  </section>
{/if}
<style>
  .account-bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
  .brand { display: block; position: relative; flex: 0 1 350px; min-width: 0; aspect-ratio: 3.2; overflow: hidden; }
  .brand img { position: absolute; width: 120%; max-width: none; height: auto; left: 50%; top: 50%; transform: translate(-50%, -50%); }
  .account-bar > button { flex-shrink: 0; }
  .google { display: inline-flex; align-items: center; text-decoration: none; background: white; color: #1f1f1f; }
  p { overflow-wrap: anywhere; }
</style>
