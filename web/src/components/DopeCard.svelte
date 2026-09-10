<script lang="ts">
  import { store } from "../lib/store.svelte";
  import { buildDopeTable, rowsToCsv } from "../core";
  import Num from "./Num.svelte";
  import { rangeFrom, rangeTo, rangeLabel, windFrom, windTo, speedLabel, velFrom, velLabel, toAngular } from "../lib/units";

  const u = $derived(store.settings.units);
  const ang = $derived(store.settings.angular);
  let start = $state(100);
  let end = $state(1000);
  let step = $state(50);
  let refWind = $state(4);
  let useCurrent = $state(true);

  const rangesDisp = $derived.by(() => { const out: number[] = []; for (let r = start; r <= end; r += step) out.push(r); return out.slice(0, 80); });
  const rows = $derived.by(() => {
    const inp = store.inputs(end);
    const base = useCurrent ? inp : { ...inp, temperatureC: 15, pressureMbar: 1013.25, humidityPct: 0 };
    return buildDopeTable({ ...base, windSpeedMps: 0 }, rangesDisp.map((d) => rangeTo(d, u)), windTo(refWind, u));
  });
  function download() {
    const blob = new Blob([rowsToCsv(rows)], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `dope_${store.rifle.name}_${store.ammoSel.name}.csv`.replace(/\s+/g, "_");
    a.click();
  }
</script>

<h2>📋 Dope card</h2>
<div class="muted" style="margin:-6px 0 10px">{store.rifle.name} · {store.ammoSel.name} · {useCurrent ? "current atmosphere" : "ICAO standard"}</div>
<div class="card">
  <div class="grid2">
    <Num label={`Start (${rangeLabel(u)})`} value={start} step={50} min={25} digits={0} onchange={(v) => (start = v)} />
    <Num label={`End (${rangeLabel(u)})`} value={end} step={50} min={100} max={3000} digits={0} onchange={(v) => (end = v)} />
    <Num label={`Step (${rangeLabel(u)})`} value={step} step={25} min={10} max={200} digits={0} onchange={(v) => (step = v)} />
  </div>
  <div class="grid2" style="margin-top:8px">
    <Num label={`Reference wind (${speedLabel(u)}, full value)`} value={refWind} step={1} min={1} max={30} digits={0} onchange={(v) => (refWind = v)} />
    <label class="row" style="align-self:end"><input type="checkbox" bind:checked={useCurrent} /> current atmosphere</label>
  </div>
</div>
<div class="card scroll">
  <table>
    <thead><tr><th>{rangeLabel(u)}</th><th>Drop {ang}</th><th>Drop {ang === "MRAD" ? "MOA" : "MRAD"}</th><th>Wind {refWind}{speedLabel(u)}</th><th>½ wind</th><th>{velLabel(u)}</th><th>Mach</th><th>TOF</th></tr></thead>
    <tbody>
      {#each rows as r, i}
        <tr style={r.mach < 1.2 ? "color:#ffb74d" : ""}>
          <td>{rangesDisp[i]}</td>
          <td>{toAngular(r.dropMrad, ang).toFixed(2)}</td>
          <td>{(ang === "MRAD" ? r.dropMoa : r.dropMrad).toFixed(2)}</td>
          <td>{toAngular(r.windMrad, ang).toFixed(2)}</td>
          <td>{toAngular(r.windHalfMrad, ang).toFixed(2)}</td>
          <td>{velFrom(r.velocityMps, u).toFixed(0)}</td>
          <td>{r.mach.toFixed(2)}</td>
          <td>{r.tofS.toFixed(2)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
  <div class="muted" style="margin-top:6px">Orange rows: transonic/subsonic (Mach &lt; 1.2). Drop negative = dial UP.</div>
  <button style="width:100%;margin-top:8px" onclick={download}>⬇ CSV</button>
</div>
