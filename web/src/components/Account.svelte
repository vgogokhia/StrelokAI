<script lang="ts">
  import { onMount } from 'svelte';
  import { store } from '../lib/store.svelte';
  import { emptyProfiles, mergeProfiles, type ProfileData } from '../lib/profile-sync';
  let user = $state<{ id: string; email: string; name: string } | null>(null);
  let enabled = $state(false);
  let status = $state('ანგარიშის შემოწმება…');
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
      status = 'პროფილები სინქრონიზებულია';
    } catch (error) {
      const code = (error as Error).message;
      if (code === '401' || code === 'account_changed') { user = null; initialized = false; }
      status = code === '401' ? 'სესია დასრულდა — შედით ხელახლა. ცვლილებები მოწყობილობაზე შენახულია.'
        : code === 'account_changed' ? 'ანგარიში შეიცვალა. ხელახლა ვამოწმებთ შესვლას.'
        : code === '409' ? 'ანგარიში ან მონაცემები შეიცვალა — ხელახლა სცადეთ სინქრონიზაცია.'
        : 'სინქრონიზაცია ვერ შესრულდა. ცვლილებები მოწყობილობაზე შენახულია.';
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
        status = store.owner ? 'შედით ხელახლა სინქრონიზაციისთვის. პროფილები მოწყობილობაზე შენახულია.' : 'შეინახეთ პროფილები ანგარიშზე და გახსენით სხვა მოწყობილობაზეც.';
      }
      const params = new URLSearchParams(location.search);
      if (params.has('auth')) {
        if (params.get('auth') === 'failed') { status = 'Google-ით შესვლა ვერ დასრულდა. სცადეთ ხელახლა.'; open = true; }
        params.delete('auth');
        history.replaceState(null, '', location.pathname + (params.size ? '?' + params : '') + location.hash);
      }
    } catch { status = 'ინტერნეტთან კავშირი ვერ დამყარდა. ადგილობრივი პროფილები ხელმისაწვდომია.'; }
  }
  async function logout() {
    if (busy) return;
    busy = true;
    try {
      await request('/api/logout', { method: 'POST' });
      store.switchOwner('');
      user = null; initialized = false; base = emptyProfiles();
      status = 'ანგარიშიდან გამოხვედით. თქვენი ანგარიშის ადგილობრივი ასლი შენარჩუნებულია.';
    } catch { status = 'გასვლა ვერ შესრულდა. შეამოწმეთ ინტერნეტი და სცადეთ ხელახლა.'; }
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
  <a href="/" class="brand">ballistics.ge</a>
  <button class="small" onclick={() => open = !open} aria-expanded={open}>{user ? 'ჩემი ანგარიში' : 'შესვლა'}</button>
</div>
{#if open}
  <section class="card" aria-label="ანგარიში">
    <h2>{user ? user.name : 'თქვენი პროფილები — ყველა მოწყობილობაზე'}</h2>
    {#if user}<p class="muted">{user.email}</p>{/if}
    <p class="muted" role="status">{status}</p>
    {#if user}
      <div class="row"><button onclick={sync} disabled={busy}>სინქრონიზაცია</button><button onclick={logout} disabled={busy}>გასვლა</button></div>
      <p class="muted">ერთდროული ცვლილებებისას ორივე ვერსია ინახება. ოფლაინ ცვლილებები კავშირის აღდგენისას აიტვირთება.</p>
    {:else if enabled}
      <a class="btn google" href="/auth/google" onclick={() => store.persist()}>Google-ით შესვლა</a>
      <p class="muted">პირველი შესვლისას ამ მოწყობილობის არსებული პროფილებიც თქვენს ანგარიშზე გადავა.</p>
    {:else}
      <p class="muted">Google-ით შესვლა ჯერ არ არის ხელმისაწვდომი. პროფილები ამ მოწყობილობაზე ინახება.</p>
    {/if}
  </section>
{/if}
<style>
  .account-bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
  .brand { color: var(--text); text-decoration: none; font-weight: 600; }
  .google { display: inline-flex; align-items: center; text-decoration: none; background: white; color: #1f1f1f; }
  p { overflow-wrap: anywhere; }
</style>
