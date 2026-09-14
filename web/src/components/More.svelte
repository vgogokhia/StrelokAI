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

  // Feedback
  import { compressImage, sendFeedback } from "../lib/feedback";
  let fbKind = $state("🐞 Bug");
  let fbMsg = $state("");
  let fbContact = $state("");
  let fbShot = $state<string | null>(null);
  let fbBusy = $state(false);
  let fbNote = $state<{ kind: string; text: string } | null>(null);
  async function pickShot(e: Event) {
    const f = (e.target as HTMLInputElement).files?.[0];
    if (!f) { fbShot = null; return; }
    try { fbShot = await compressImage(f); } catch { fbNote = { kind: "err", text: "Could not read the image." }; }
  }
  async function submitFeedback() {
    if (fbMsg.trim().length < 5) { fbNote = { kind: "warn", text: "შეტყობინება ძალიან მოკლეა / message too short" }; return; }
    fbBusy = true; fbNote = null;
    const r = await sendFeedback({
      kind: fbKind, message: fbMsg, contact: fbContact, screenshot: fbShot,
      meta: { version, units: s.units, angular: s.angular, rifle: `${store.rifle.name} (${store.rifle.chambering})`, ammo: store.ammoSel.name,
              range: store.cond.targetRangeM, screen: `${screen.width}x${screen.height}` },
    });
    fbBusy = false;
    if (r.ok) { fbNote = { kind: "ok", text: "მადლობა, მივიღე! / Thanks, received." }; fbMsg = ""; fbContact = ""; fbShot = null; }
    else fbNote = { kind: "err", text: r.error === "offline" ? "ინტერნეტი არ არის — სცადე მოგვიანებით. / Offline, try later." : `ვერ გაიგზავნა: ${r.error}` };
  }
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
    <button class="primary" onclick={() => { store.setRange(rangeM); store.pushRecent(rangeM); }}>🎯 Use</button>
  </div>
  <div class="muted" style="margin-top:6px">Torso ~45 cm · head ~18 cm · deer chest ~45–50 cm · IPSC 30×45 cm</div>
</div>

<h2>💬 Feedback / უკუკავშირი</h2>
<div class="card">
  <div class="muted" style="margin-bottom:8px">იპოვე ხარვეზი ან გინდა ფუნქცია? დაწერე, სქრინშოტიც მიაბი. / Found a bug or want a feature? Write here, attach a screenshot.</div>
  <div class="seg" style="margin-bottom:8px">
    {#each ["🐞 Bug", "💡 Idea", "💬 Other"] as k}<button class:on={fbKind === k} onclick={() => (fbKind = k)}>{k}</button>{/each}
  </div>
  <textarea bind:value={fbMsg} rows="4" maxlength="4000" placeholder="რა მოხდა, რა მოელოდი, რომელი ვაზნა/მანძილი… / what happened, what you expected…"
    style="width:100%;background:var(--panel2);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px;font:inherit"></textarea>
  <div class="grid2" style="margin-top:8px">
    <div><label class="f">კონტაქტი (არასავალდებულო) / contact</label><input type="text" bind:value={fbContact} placeholder="email / Facebook / phone" /></div>
    <div><label class="f">სქრინშოტი / screenshot</label><input type="file" accept="image/*" onchange={pickShot} style="width:100%" /></div>
  </div>
  {#if fbShot}<img src={fbShot} alt="screenshot" style="max-height:120px;border-radius:8px;margin-top:8px" />{/if}
  <button class="primary" style="width:100%;margin-top:8px" disabled={fbBusy} onclick={submitFeedback}>📨 გაგზავნა / Send</button>
  {#if fbNote}<div class="note {fbNote.kind}">{fbNote.text}</div>{/if}
</div>

<h2>ℹ️ About</h2>
<div class="card">
  <p><b>ballistics.ge</b> — უფასო ბალისტიკური კალკულატორი. მუშაობს ოფლაინ: დაამატე მთავარ ეკრანზე (Add to Home Screen) და პოლიგონზე ინტერნეტი აღარ დაგჭირდება.</p>
  <p class="muted">RK4 point-mass solver, G1/G7 (BRL/JBM), spin drift, aero jump, Coriolis, cant, incline, powder temperature; validated against py_ballisticcalc. Bullet library: manufacturer published data.</p>
  <p class="muted">v{version} · <a href="https://ballistics.ge" style="color:var(--green)">ballistics.ge</a></p>
  <button style="width:100%" onclick={() => { if (confirm("Reset all profiles and settings?")) store.reset(); }}>↺ Reset everything</button>
</div>
