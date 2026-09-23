<script lang="ts">
  import { store } from "../lib/store.svelte";
  import Calculator from "../components/Calculator.svelte";
  import Profiles from "../components/Profiles.svelte";
  import DopeCard from "../components/DopeCard.svelte";
  import Reticle from "../components/Reticle.svelte";
  import Account from "../components/Account.svelte";
  import More from "../components/More.svelte";
  import Feedback from "../components/Feedback.svelte";
  import Assistant from "../components/Assistant.svelte";
  import { installFeedbackFlusher } from "../lib/feedback";

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
  installFeedbackFlusher();
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
  <button class="fab ai" title="Ask the AI assistant" aria-label="AI assistant" onclick={() => (aiOpen = true)}>🤖</button>
{/if}
{#if tab !== "more"}
  <button class="fab" title="Report a bug or request a feature" aria-label="Feedback" onclick={() => (fbOpen = true)}>💬</button>
{/if}
{#if aiOpen}
  <div class="modal-bg" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) aiOpen = false; }}>
    <div class="modal" role="dialog" aria-modal="true" aria-label="AI assistant">
      <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:8px">
        <h2 style="margin:0">🤖 Assistant</h2>
        <button type="button" aria-label="Close" onclick={() => (aiOpen = false)}>✕</button>
      </div>
      <Assistant />
    </div>
  </div>
{/if}
{#if fbOpen}
  <div class="modal-bg" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) fbOpen = false; }}>
    <div class="modal" role="dialog" aria-modal="true" aria-label="Feedback">
      <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:8px">
        <h2 style="margin:0">💬 Feedback</h2>
        <button type="button" aria-label="Close" onclick={() => (fbOpen = false)}>✕</button>
      </div>
      <Feedback page={tab} onsent={() => (fbOpen = false)} />
    </div>
  </div>
{/if}

<nav class="tabs">
  {#each tabs as [id, ico, name]}
    <button class:on={tab === id} onclick={() => (tab = id)}>
      <span class="ico">{#if id === "calc"}<img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" />{:else}{ico}{/if}</span><span>{name}</span>
    </button>
  {/each}
</nav>
