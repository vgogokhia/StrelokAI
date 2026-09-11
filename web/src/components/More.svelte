<script lang="ts">
  import { store } from "../lib/store.svelte";
  import Num from "./Num.svelte";
  import { CLICK_OPTIONS } from "../lib/units";
  import { MRAD_TO_MOA } from "../lib/units";

  const s = $derived(store.settings);
  // Rangefinder
  let sizeCm = $state(45);
  let observed = $state(1.0);
  const rangeM = $derived.by(() => {
    const mrad = s.angular === "MOA" ? observed / MRAD_TO_MOA : observed;
    return mrad > 0 ? (sizeCm / 100) * 1000 / mrad : 0;
  });
  const version = "0.1.0";
</script>

<h2>⚙️ Settings</h2>
<div class="card">
  <div class="grid2">
    <div><label class="f">Units</label>
      <div class="seg"><button class:on={s.units === "metric"} onclick={() => (s.units = "metric")}>Metric</button><button class:on={s.units === "imperial"} onclick={() => (s.units = "imperial")}>Imperial</button></div></div>
    <div><label class="f">Angular</label>
      <div class="seg"><button class:on={s.angular === "MRAD"} onclick={() => { s.angular = "MRAD"; if (!s.click.includes("MRAD") && !s.click.includes("cm")) s.click = "0.1 MRAD"; }}>MRAD</button><button class:on={s.angular === "MOA"} onclick={() => { s.angular = "MOA"; if (!s.click.includes("MOA")) s.click = "1/4 MOA"; }}>MOA</button></div></div>
    <div style="grid-column:1/3"><label class="f">Scope click value</label>
      <select bind:value={s.click}>{#each Object.keys(CLICK_OPTIONS) as c}<option>{c}</option>{/each}</select></div>
  </div>
</div>

<h2>📏 Rangefinder</h2>
<div class="card">
  <div class="grid2">
    <Num label="Target size (cm)" value={sizeCm} step={1} min={1} max={500} digits={0} onchange={(v) => (sizeCm = v)} />
    <Num label={`Observed (${s.angular})`} value={observed} step={0.1} min={0.05} digits={2} onchange={(v) => (observed = v)} />
  </div>
  <div class="row" style="margin-top:8px">
    <div class="metric" style="flex:1"><div class="v">{Math.round(rangeM)} m</div><div class="l">estimated range</div></div>
    <button class="primary" onclick={() => { store.setRange(rangeM); store.pushRecent(rangeM); }}><img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" /> Use</button>
  </div>
  <div class="muted" style="margin-top:6px">Torso ~45 cm · head ~18 cm · deer chest ~45–50 cm · IPSC 30×45 cm</div>
</div>

<h2>Blog (Georgian)</h2>
<div class="card"><a href="/blog/" style="color:var(--green)">Firearm storage, ammunition transport and FAQs</a></div>

<h2>ℹ️ About</h2>
<div class="card">
  <p><b>ballistics.ge</b> — a free ballistic calculator that works offline. Add it to your home screen to use it at the range without an internet connection.</p>
  <p class="muted">RK4 point-mass solver, G1/G7 (BRL/JBM), spin drift, aero jump, Coriolis, cant, incline, powder temperature; validated against py_ballisticcalc. Bullet library: manufacturer published data.</p>
  <p class="muted">v{version} · <a href="https://ballistics.ge" style="color:var(--green)">ballistics.ge</a></p>
  <button style="width:100%" onclick={() => { if (confirm("Reset all profiles and settings?")) store.reset(); }}>↺ Reset everything</button>
</div>
