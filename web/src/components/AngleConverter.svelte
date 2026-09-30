<script lang="ts">
  import { store } from "../lib/store.svelte";
  import Num from "./Num.svelte";
  import { rangeFrom, rangeTo, rangeLabel, smallLabel } from "../lib/units";
  const u = $derived(store.settings.units);
  let rangeM = $state(500);
  let mrad = $state(1);
  const MRAD_TO_MOA = 3.43775;
  const sizeM = $derived((mrad / 1000) * rangeM);
  const fmtSize = (m: number) => (u === "imperial" ? `${(m * 39.3701).toFixed(1)} in` : `${(m * 100).toFixed(1)} cm`);
  const clickMrad = $derived(store.clickMrad);
</script>

<div class="grid2">
  <Num label={`Distance (${rangeLabel(u)})`} value={rangeM} from={(m) => rangeFrom(m, u)} to={(v) => rangeTo(v, u)} step={25} min={10} max={3000} digits={0} onchange={(m) => (rangeM = m)} />
  <Num label="Angle (MRAD)" value={mrad} step={0.1} min={0} max={100} digits={2} onchange={(v) => (mrad = v)} />
</div>
<div class="grid2" style="margin-top:8px;text-align:center">
  <div class="kv"><div class="muted">{mrad.toFixed(2)} MRAD = {(mrad * MRAD_TO_MOA).toFixed(2)} MOA</div><b style="font-size:1.3rem">{fmtSize(sizeM)}</b><div class="muted">at {Math.round(rangeFrom(rangeM, u))} {rangeLabel(u)}</div></div>
  <div class="kv"><div class="muted">1 click ({store.settings.click})</div><b style="font-size:1.3rem">{fmtSize((clickMrad / 1000) * rangeM)}</b><div class="muted">{Math.round(mrad / clickMrad)} clicks for {mrad.toFixed(2)} MRAD</div></div>
</div>
<div class="muted" style="margin-top:6px">1 MRAD = 10 cm at 100 m = 3.6 in at 100 yd. 1 MOA = 1.047 in at 100 yd.</div>
<style>.kv{background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:8px}</style>
