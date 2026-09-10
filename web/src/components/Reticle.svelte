<script lang="ts">
  import { store } from "../lib/store.svelte";
  import { RETICLES, holdUnits, renderSvg } from "../lib/reticles";
  import { dropMrad, windageMrad } from "../core";
  import Num from "./Num.svelte";
  import { fmtRange, fmtAng } from "../lib/units";

  const u = $derived(store.settings.units);
  const s = $derived(store.settings);
  const spec = $derived(RETICLES.find((r) => r.name === s.reticle) ?? RETICLES[0]);
  const pt = $derived(store.target());
  const sfp = $derived(s.reticleFp === "SFP" && s.reticleCalMag ? s.reticleCurMag / s.reticleCalMag : 1);
  const hx = $derived(pt ? holdUnits(windageMrad(pt), spec, sfp) : 0);
  const hy = $derived(pt ? holdUnits(-dropMrad(pt), spec, sfp) : 0);
  let targetCm = $state(0);
  const ring = $derived(targetCm && store.cond.targetRangeM ? holdUnits((targetCm / 100 / store.cond.targetRangeM) * 1000, spec, sfp) : null);
  const svg = $derived(renderSvg(spec, hx, hy, 480, ring));
  const off = $derived(Math.abs(hx) > spec.view || Math.abs(hy) > spec.view);
  // Turret dial
  const perRev = $derived(s.turretPerRev);
  const dialVal = $derived(pt ? Math.abs(s.angular === "MOA" ? dropMrad(pt) * 3.43775 : dropMrad(pt)) : 0);
</script>

<h2>🔭 Reticle holdover</h2>
<div class="muted" style="margin:-6px 0 10px">Red dot = the reticle mark to put on the target.</div>
<div class="card">
  <div class="grid2">
    <div><label class="f">Reticle</label>
      <select bind:value={s.reticle}>{#each RETICLES as r}<option value={r.name}>{r.name}</option>{/each}</select></div>
    <div><label class="f">Focal plane</label>
      <div class="seg"><button class:on={s.reticleFp === "FFP"} onclick={() => (s.reticleFp = "FFP")}>FFP</button><button class:on={s.reticleFp === "SFP"} onclick={() => (s.reticleFp = "SFP")}>SFP</button></div></div>
    {#if s.reticleFp === "SFP"}
      <Num label="Reticle true at (×)" value={s.reticleCalMag} step={0.5} min={1} max={50} onchange={(v) => (s.reticleCalMag = v)} />
      <Num label="Current magnification (×)" value={s.reticleCurMag} step={0.5} min={1} max={50} onchange={(v) => (s.reticleCurMag = v)} />
    {/if}
  </div>
  {#if spec.note}<div class="muted" style="margin-top:6px">{spec.note}</div>{/if}
</div>

{#if pt}
  <div class="card" style="padding:6px">{@html svg}</div>
  <div class="grid3">
    <div class="metric"><div class="v">{fmtRange(store.cond.targetRangeM, u)}</div><div class="l">range</div></div>
    <div class="metric"><div class="v">{hy > 0 ? "+" : ""}{hy.toFixed(2)} {spec.unit}</div><div class="l">elev hold{sfp !== 1 ? " (reticle)" : ""}</div></div>
    <div class="metric"><div class="v">{hx > 0 ? "+" : ""}{hx.toFixed(2)} {spec.unit}</div><div class="l">wind hold{sfp !== 1 ? " (reticle)" : ""}</div></div>
  </div>
  {#if sfp !== 1}<div class="muted" style="margin-top:6px">SFP at {s.reticleCurMag}× of {s.reticleCalMag}×: each mark = {(1 / sfp).toFixed(2)} {spec.unit}. True hold {fmtAng(-dropMrad(pt), s.angular)} up.</div>{/if}
  {#if off}<div class="note warn">Hold is outside the reticle — dial some elevation and hold the rest.</div>{/if}
  <div class="card" style="margin-top:10px">
    <Num label="Show target size on reticle (cm, 0 = off)" value={targetCm} step={5} min={0} max={500} digits={0} onchange={(v) => (targetCm = v)} />
  </div>

  <div class="card">
    <h3>🎛️ Turret</h3>
    <div class="row">
      <div style="flex:1"><Num label={`${s.angular} per revolution`} value={perRev} step={1} min={1} max={60} digits={0} onchange={(v) => (s.turretPerRev = v)} /></div>
      <div class="metric" style="flex:1"><div class="v">{Math.floor(dialVal / perRev)} rev + {(dialVal % perRev).toFixed(2)}</div><div class="l">dial {pt.dropM < 0 ? "UP" : "DOWN"} {dialVal.toFixed(2)} {s.angular}</div></div>
    </div>
  </div>
{/if}
