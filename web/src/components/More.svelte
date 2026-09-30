<script lang="ts">
  import { t, i18n, setLang } from "../lib/i18n.svelte";
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
  const version = __APP_VERSION__;

  import Feedback from "./Feedback.svelte";
  import Metronome from "./Metronome.svelte";
  import AngleConverter from "./AngleConverter.svelte";
</script>

<h2>⚙️ {t("Settings")}</h2>
<div class="card">
  <div class="grid2">
    <div style="grid-column:1/3"><label class="f">{t("Language")} / ენა</label>
      <div class="seg"><button class:on={i18n.lang === "en"} onclick={() => setLang("en")}>English</button><button class:on={i18n.lang === "ka"} onclick={() => setLang("ka")}>ქართული</button></div></div>
    <div><label class="f">{t("Units")}</label>
      <div class="seg"><button class:on={s.units === "metric"} onclick={() => (s.units = "metric")}>{t("Metric")}</button><button class:on={s.units === "imperial"} onclick={() => (s.units = "imperial")}>{t("Imperial")}</button></div></div>
    <div><label class="f">{t("Angular")}</label>
      <div class="seg"><button class:on={s.angular === "MRAD"} onclick={() => { s.angular = "MRAD"; if (!s.click.includes("MRAD") && !s.click.includes("cm")) s.click = "0.1 MRAD"; }}>MRAD</button><button class:on={s.angular === "MOA"} onclick={() => { s.angular = "MOA"; if (!s.click.includes("MOA")) s.click = "1/4 MOA"; }}>MOA</button></div></div>
    <div style="grid-column:1/3"><label class="f">{t("Scope click value")}</label>
      <select bind:value={s.click}>{#each Object.keys(CLICK_OPTIONS) as c}<option>{c}</option>{/each}</select></div>
  </div>
</div>

<h2>📏 {t("Rangefinder")}</h2>
<div class="card">
  <div class="grid2">
    <Num label={t("Target size (cm)")} value={sizeCm} step={1} min={1} max={500} digits={0} onchange={(v) => (sizeCm = v)} />
    <Num label={`${t("Observed")} (${s.angular})`} value={observed} step={0.1} min={0.05} digits={2} onchange={(v) => (observed = v)} />
  </div>
  <div class="row" style="margin-top:8px">
    <div class="metric" style="flex:1"><div class="v">{Math.round(rangeM)} m</div><div class="l">{t("estimated range")}</div></div>
    <button class="primary" onclick={() => { store.setRange(rangeM); store.pushRecent(rangeM); }}><img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" /> {t("Use")}</button>
  </div>
  <div class="muted" style="margin-top:6px">{t("Torso ~45 cm · head ~18 cm · deer chest ~45–50 cm · IPSC 30×45 cm")}</div>
</div>

<h2>📐 {t("MIL / MOA at distance")}</h2>
<div class="card"><AngleConverter /></div>

<h2>🎵 {t("Metronome")}</h2>
<div class="card"><Metronome /></div>

<h2>💬 {t("Feedback")}</h2>
<div class="card"><Feedback page="more" /></div>

<h2>📖 {t("Learn")}</h2>
<div class="card">
  <p style="margin:0 0 6px"><a href={i18n.lang === "ka" ? "/ka/glossary/" : "/glossary/"} style="color:var(--green)">{t("Shooting glossary")}</a>: {t("MIL vs MOA, FFP vs SFP, BC, zeroing, wind, drop charts")}</p>
  <p style="margin:0"><a href="/blog/" hreflang="ka" style="color:var(--green)">{t("Blog (Georgian)")}</a>: {t("firearm storage, ammunition transport and FAQs")}</p>
</div>

<h2>ℹ️ {t("About")}</h2>
<div class="card">
  <p><b>ballistics.ge</b> — {t("a free ballistic calculator that works offline. Add it to your home screen to use it at the range without an internet connection.")}</p>
  <p class="muted">{t("RK4 point-mass solver, G1/G7 (BRL/JBM), spin drift, aero jump, Coriolis, cant, incline, powder temperature; validated against py_ballisticcalc. Bullet library: manufacturer published data.")}</p>
  <p class="muted">{t("Free for now. If usage grows a lot, a small one-time Pro fee may be introduced to cover costs — everyone who signed in before that keeps Pro free.")} <a href="/pricing/" style="color:var(--green)">{t("Pricing")}</a></p>
  <p class="muted">v{version} · <a href="/ballistics/" style="color:var(--green)">{t("Ballistics charts")}</a> · <a href="/terms/" style="color:var(--green)">{t("Terms")}</a> · <a href="/privacy/" style="color:var(--green)">{t("Privacy")}</a> · <a href="/refunds/" style="color:var(--green)">{t("Refunds")}</a> · <a href="mailto:hello@ballistics.ge" style="color:var(--green)">hello@ballistics.ge</a></p>
  <button style="width:100%" onclick={() => { if (confirm(t("Reset all profiles and settings?"))) store.reset(); }}>↺ {t("Reset everything")}</button>
</div>
