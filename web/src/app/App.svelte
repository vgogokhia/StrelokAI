<script lang="ts">
  import { store } from "../lib/store.svelte";
  import Calculator from "../components/Calculator.svelte";
  import Profiles from "../components/Profiles.svelte";
  import DopeCard from "../components/DopeCard.svelte";
  import Reticle from "../components/Reticle.svelte";
  import More from "../components/More.svelte";

  type Tab = "calc" | "profiles" | "dope" | "reticle" | "more";
  let tab = $state<Tab>((localStorage.getItem("bge_tab") as Tab) || "calc");
  const tabs: Array<[Tab, string, string]> = [
    ["calc", "🎯", "Calc"],
    ["profiles", "🔫", "Profiles"],
    ["dope", "📋", "Dope"],
    ["reticle", "🔭", "Reticle"],
    ["more", "⚙️", "More"],
  ];
  $effect(() => {
    localStorage.setItem("bge_tab", tab);
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
  {#if tab === "calc"}<Calculator />
  {:else if tab === "profiles"}<Profiles />
  {:else if tab === "dope"}<DopeCard />
  {:else if tab === "reticle"}<Reticle />
  {:else}<More />{/if}
</main>

<nav class="tabs">
  {#each tabs as [id, ico, name]}
    <button class:on={tab === id} onclick={() => (tab = id)}>
      <span class="ico">{ico}</span><span>{name}</span>
    </button>
  {/each}
</nav>
