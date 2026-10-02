<script lang="ts">
  import { t } from "../lib/i18n.svelte";
  import { store } from "../lib/store.svelte";
  import Calculator from "../components/Calculator.svelte";
  import Profiles from "../components/Profiles.svelte";
  import DopeCard from "../components/DopeCard.svelte";
  import Reticle from "../components/Reticle.svelte";
  import Account from "../components/Account.svelte";
  import More from "../components/More.svelte";
  import Feedback from "../components/Feedback.svelte";
  import { installFeedbackFlusher } from "../lib/feedback";
  import { decodeShare, type SharedLoad } from "../lib/share";
  import { billing, FREE_RIFLES, FREE_AMMO } from "../lib/billing.svelte";

  type Tab = "calc" | "profiles" | "dope" | "reticle" | "more";
  let tab = $state<Tab>((localStorage.getItem("bge_tab") as Tab) || "calc");
  const tabs: Array<[Tab, string, string]> = [
    ["calc", "", "Calc"],
    ["profiles", "🔫", "Profiles"],
    ["dope", "📋", "Dope"],
    ["reticle", "🔭", "Reticle"],
    ["more", "⚙️", "More"],
  ];
  $effect(() => {
    localStorage.setItem("bge_tab", tab);
  });
  let fbOpen = $state(false);
  let aiOpen = $state(false);
  // Ad/landing links use ballistics.ge/?ai ; after Google sign-in we come back to "/" and reopen the chat.
  try {
    const q = new URLSearchParams(location.search);
    if (q.has("ai") || localStorage.getItem("bge_open_ai")) { aiOpen = true; tab = "calc"; localStorage.removeItem("bge_open_ai"); if (q.has("ai")) history.replaceState(null, "", location.pathname); }
  } catch { /* ignore */ }
  installFeedbackFlusher();

  // Shared rifle + load arriving as ballistics.ge/#p=... (see lib/share.ts).
  let incoming = $state<SharedLoad | null>(null);
  let shareMsg = $state("");
  async function readShare() {
    if (!location.hash.startsWith("#p=")) return;
    const s = await decodeShare(location.hash);
    history.replaceState(null, "", location.pathname + location.search);
    if (s) { incoming = s; shareMsg = ""; } else { incoming = null; shareMsg = t("This share link is damaged or from a newer version of the app."); }
  }
  void readShare();
  $effect(() => {
    const onHash = () => void readShare();
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  });
  const newId = () => Math.random().toString(36).slice(2, 10);
  const same = (a: object, b: object) => JSON.stringify(a) === JSON.stringify(b);
  function importShared() {
    const s = incoming; if (!s) return;
    const rifle = store.rifles.find(({ id, ...r }) => same(r, s.rifle));
    const ammo = store.ammo.find(({ id, ...a }) => same(a, s.ammo));
    if ((!rifle && billing.limited && store.rifles.length >= FREE_RIFLES) || (!ammo && billing.limited && store.ammo.length >= FREE_AMMO)) {
      shareMsg = t("Your free plan has no room for another profile. Upgrade to Pro in My account or delete one first."); return;
    }
    if (rifle) store.rifleId = rifle.id; else store.addRifle({ ...s.rifle, id: newId() });
    if (ammo) store.ammoId = ammo.id; else store.addAmmo({ ...s.ammo, id: newId() });
    incoming = null; tab = "calc";
  }
  $effect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { fbOpen = false; aiOpen = false; } };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });
  // Persist any state change (debounced).
  let timer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    // touch everything we persist so the effect re-runs on change
    void JSON.stringify([store.rifles, store.ammo, store.rifleId, store.ammoId, store.cond, store.settings, store.recent]);
    clearTimeout(timer);
    timer = setTimeout(() => store.persist(), 300);
  });
</script>

<main>
  <Account />
  {#if tab === "calc"}<Calculator />
  {:else if tab === "profiles"}<Profiles />
  {:else if tab === "dope"}<DopeCard />
  {:else if tab === "reticle"}<Reticle />
  {:else}<More />{/if}
</main>

{#if tab === "calc" || tab === "dope" || tab === "reticle"}
  <button class="fab ai" title={t("Ask the AI assistant")} aria-label={t("AI assistant")} onclick={() => (aiOpen = true)}>🤖</button>
{/if}
{#if tab !== "more"}
  <button class="fab" title={t("Report a bug or request a feature")} aria-label={t("Feedback")} onclick={() => (fbOpen = true)}>💬</button>
{/if}
{#if aiOpen}
  <div class="modal-bg" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) aiOpen = false; }}>
    <div class="modal" role="dialog" aria-modal="true" aria-label={t("AI assistant")}>
      <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:8px">
        <h2 style="margin:0">🤖 {t("Assistant")}</h2>
        <button type="button" aria-label={t("Close")} onclick={() => (aiOpen = false)}>✕</button>
      </div>
      {#await import("../components/Assistant.svelte") then { default: Assistant }}<Assistant />{/await}
    </div>
  </div>
{/if}
{#if incoming || shareMsg}
  <div class="modal-bg" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) { incoming = null; shareMsg = ""; } }}>
    <div class="modal" role="dialog" aria-modal="true" aria-label={t("Shared rifle and load")}>
      <h2 style="margin-top:0">🔗 {t("Shared rifle and load")}</h2>
      {#if incoming}
        <div class="card">
          <b>🔫 {incoming.rifle.name}</b> <span class="muted">· {incoming.rifle.chambering} · {t("Zero range")} {incoming.rifle.zeroRangeM} m · 1:{incoming.rifle.twistRateIn}</span><br />
          <b>{incoming.ammo.name}</b> <span class="muted">· {incoming.ammo.massGrains} gr · {incoming.ammo.dragModel} {incoming.ammo.bc} · {Math.round(incoming.ammo.muzzleVelocityMps)} m/s</span>
        </div>
        <p class="muted">{t("Add this rifle and load to your profiles? Your existing profiles are not changed.")}</p>
      {/if}
      {#if shareMsg}<div class="note warn">{shareMsg}</div>{/if}
      <div class="row">
        {#if incoming}<button class="primary" style="flex:1" onclick={importShared}>✔ {t("Add to my profiles")}</button>{/if}
        <button style="flex:1" onclick={() => { incoming = null; shareMsg = ""; }}>{incoming ? t("Cancel") : t("Close")}</button>
      </div>
    </div>
  </div>
{/if}
{#if fbOpen}
  <div class="modal-bg" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) fbOpen = false; }}>
    <div class="modal" role="dialog" aria-modal="true" aria-label={t("Feedback")}>
      <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:8px">
        <h2 style="margin:0">💬 {t("Feedback")}</h2>
        <button type="button" aria-label={t("Close")} onclick={() => (fbOpen = false)}>✕</button>
      </div>
      <Feedback page={tab} onsent={() => (fbOpen = false)} />
    </div>
  </div>
{/if}

<nav class="tabs">
  {#each tabs as [id, ico, name]}
    <button class:on={tab === id} onclick={() => (tab = id)}>
      <span class="ico">{#if id === "calc"}<img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" />{:else}{ico}{/if}</span><span>{t(name)}</span>
    </button>
  {/each}
</nav>
