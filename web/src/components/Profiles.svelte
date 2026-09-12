<script lang="ts">
  import { store, defaultRifle, defaultAmmo, type AmmoProfile } from "../lib/store.svelte";
  import Num from "./Num.svelte";
  import { LIBRARY, label, type BulletPreset } from "../lib/library";
  import { CHAMBERING_NAMES, isCompatible, LIBRARY_CALIBER_TO_CHAMBERING } from "../lib/calibers";
  import { rangeFrom, rangeTo, rangeLabel, sightFrom, sightTo, sightLabel, velFrom, velTo, velLabel, tempFrom, tempTo, tempLabel, smallFrom, smallTo, smallLabel, pressFrom, pressTo, pressLabel } from "../lib/units";
  import { hasFeature } from "../lib/license";

  const u = $derived(store.settings.units);
  const rifle = $derived(store.rifle);
  const ammo = $derived(store.ammoSel);
  const fitting = $derived(LIBRARY.filter((b) => isCompatible(rifle.chambering, b.diameterIn)));
  const ammoFits = $derived(isCompatible(rifle.chambering, ammo.diameterIn, ammo.cartridge));
  let preset = $state("");
  let filter = $state("");
  const shown = $derived(fitting.filter((b) => !filter || label(b).toLowerCase().includes(filter.toLowerCase())));

  function applyPreset() {
    const b = fitting.find((x) => x.id === preset);
    if (!b) return;
    const useG7 = b.bcG7 != null;
    Object.assign(ammo, {
      name: `${b.manufacturer} ${b.bullet}`,
      dragModel: useG7 ? "G7" : "G1", bc: useG7 ? b.bcG7! : b.bcG1!, bcSegments: null,
      massGrains: b.massGrains, diameterIn: b.diameterIn, lengthIn: b.lengthIn,
      muzzleVelocityMps: b.defaultMvMps, cartridge: LIBRARY_CALIBER_TO_CHAMBERING[b.caliber] ?? rifle.chambering,
    } satisfies Partial<AmmoProfile>);
    if (b.defaultTwistIn && !rifle.twistRateIn) rifle.twistRateIn = b.defaultTwistIn;
    preset = "";
  }
  let zeroDiffers = $derived(rifle.zeroTempC != null);
  function toggleZero(on: boolean) {
    if (on) { rifle.zeroTempC = 15; rifle.zeroPressureMbar = 1013.25; rifle.zeroHumidityPct = 50; }
    else { rifle.zeroTempC = null; rifle.zeroPressureMbar = null; rifle.zeroHumidityPct = null; }
  }
  let bands = $derived(!!ammo.bcSegments);
  function toggleBands(on: boolean) {
    ammo.bcSegments = on ? [[2800, ammo.bc], [0, ammo.bc]] : null;
  }
</script>

<h2>🔫 Rifle</h2>
<div class="card">
  <div class="row">
    <select style="flex:1" value={store.rifleId} onchange={(e) => (store.rifleId = (e.target as HTMLSelectElement).value)}>
      {#each store.rifles as r}<option value={r.id}>{r.name}</option>{/each}
    </select>
    <button class="small" onclick={() => store.addRifle({ ...defaultRifle(), name: `Rifle ${store.rifles.length + 1}` })}>＋</button>
    <button class="small" disabled={store.rifles.length < 2} onclick={() => store.deleteRifle(rifle.id)}>🗑</button>
  </div>
  <div class="grid2" style="margin-top:8px">
    <div><label class="f">Name</label><input type="text" bind:value={rifle.name} /></div>
    <div><label class="f">Chambering</label>
      <select bind:value={rifle.chambering}>{#each CHAMBERING_NAMES as c}<option>{c}</option>{/each}</select></div>
    <Num label={`Zero range (${rangeLabel(u)})`} value={rifle.zeroRangeM} from={(v) => rangeFrom(v, u)} to={(v) => rangeTo(v, u)} step={25} min={10} max={600} digits={0} onchange={(v) => (rifle.zeroRangeM = v)} />
    <Num label={`Sight height (${sightLabel(u)})`} value={rifle.sightHeightMm} from={(v) => sightFrom(v, u)} to={(v) => sightTo(v, u)} step={u === "imperial" ? 0.05 : 1} digits={u === "imperial" ? 2 : 0} min={0} onchange={(v) => (rifle.sightHeightMm = v)} />
    <Num label="Twist 1:X (in)" value={rifle.twistRateIn} step={0.25} min={4} max={30} digits={2} onchange={(v) => (rifle.twistRateIn = v)} />
    <div><label class="f">Twist direction</label>
      <div class="seg"><button class:on={rifle.twistDirection === "right"} onclick={() => (rifle.twistDirection = "right")}>Right</button><button class:on={rifle.twistDirection === "left"} onclick={() => (rifle.twistDirection = "left")}>Left</button></div></div>
  </div>
  <details>
    <summary>⚙ Advanced zero</summary>
    <label class="row"><input type="checkbox" checked={zeroDiffers} onchange={(e) => toggleZero((e.target as HTMLInputElement).checked)} /> Zeroed in different conditions</label>
    {#if zeroDiffers}
      <div class="grid3">
        <Num label={`Zero temp (${tempLabel(u)})`} value={rifle.zeroTempC ?? 15} from={(v) => tempFrom(v, u)} to={(v) => tempTo(v, u)} digits={0} onchange={(v) => (rifle.zeroTempC = v)} />
        <Num label={`Zero pressure (${pressLabel(u)})`} value={rifle.zeroPressureMbar ?? 1013.25} from={(v) => pressFrom(v, u)} to={(v) => pressTo(v, u)} step={u === "imperial" ? 0.01 : 1} digits={u === "imperial" ? 2 : 0} onchange={(v) => (rifle.zeroPressureMbar = v)} />
        <Num label="Zero RH (%)" value={rifle.zeroHumidityPct ?? 50} step={5} min={0} max={100} digits={0} onchange={(v) => (rifle.zeroHumidityPct = v)} />
      </div>
    {/if}
    <div class="muted" style="margin-top:8px">Zero offset: where the group sits at the zero range.</div>
    <div class="grid2">
      <Num label={`Vertical (${smallLabel(u)}, + high)`} value={rifle.zeroOffsetVCm} from={(v) => smallFrom(v, u)} to={(v) => smallTo(v, u)} step={u === "imperial" ? 0.1 : 0.5} digits={u === "imperial" ? 2 : 1} onchange={(v) => (rifle.zeroOffsetVCm = v)} />
      <Num label={`Horizontal (${smallLabel(u)}, + right)`} value={rifle.zeroOffsetHCm} from={(v) => smallFrom(v, u)} to={(v) => smallTo(v, u)} step={u === "imperial" ? 0.1 : 0.5} digits={u === "imperial" ? 2 : 1} onchange={(v) => (rifle.zeroOffsetHCm = v)} />
    </div>
  </details>
</div>

<h2><img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" /> Ammo</h2>
<div class="card">
  <div class="row">
    <select style="flex:1" value={store.ammoId} onchange={(e) => (store.ammoId = (e.target as HTMLSelectElement).value)}>
      {#each store.ammo as a}<option value={a.id}>{a.name}{isCompatible(rifle.chambering, a.diameterIn, a.cartridge) ? "" : " ⚠"}</option>{/each}
    </select>
    <button class="small" onclick={() => store.addAmmo({ ...defaultAmmo(), name: `Ammo ${store.ammo.length + 1}`, cartridge: rifle.chambering })}>＋</button>
    <button class="small" disabled={store.ammo.length < 2} onclick={() => store.deleteAmmo(ammo.id)}>🗑</button>
  </div>
  {#if !ammoFits}<div class="note warn">⚠️ This ammo ({ammo.cartridge}) doesn't fit a {rifle.chambering} rifle.</div>{/if}

  {#if hasFeature("library")}
    <div style="margin-top:8px">
      <label class="f">📚 Bullet library ({fitting.length} that fit this rifle)</label>
      <input type="text" placeholder="search: Lapua, 175, subsonic…" bind:value={filter} />
      <div class="row" style="margin-top:6px">
        <select style="flex:1" bind:value={preset}>
          <option value="">— pick —</option>
          {#each shown as b}<option value={b.id}>{label(b)}</option>{/each}
        </select>
        <button class="small" disabled={!preset} onclick={applyPreset}>⬇ Apply</button>
      </div>
    </div>
  {/if}

  <div class="grid2" style="margin-top:8px">
    <div><label class="f">Name</label><input type="text" bind:value={ammo.name} /></div>
    <div><label class="f">Cartridge</label>
      <select bind:value={ammo.cartridge}>{#each CHAMBERING_NAMES as c}<option>{c}</option>{/each}</select></div>
    <div><label class="f">Drag model</label>
      <div class="seg"><button class:on={ammo.dragModel === "G1"} onclick={() => (ammo.dragModel = "G1")}>G1</button><button class:on={ammo.dragModel === "G7"} onclick={() => (ammo.dragModel = "G7")}>G7</button></div></div>
    <Num label={`BC (${ammo.dragModel})`} value={ammo.bc} step={0.001} min={0.05} max={1.5} digits={3} onchange={(v) => (ammo.bc = v)} />
    <Num label="Weight (gr)" value={ammo.massGrains} step={1} min={10} max={800} digits={1} onchange={(v) => (ammo.massGrains = v)} />
    <Num label="Diameter (in)" value={ammo.diameterIn} step={0.001} min={0.17} max={0.51} digits={4} onchange={(v) => (ammo.diameterIn = v)} />
    <Num label="Length (in)" value={ammo.lengthIn} step={0.01} min={0.3} max={3} digits={3} onchange={(v) => (ammo.lengthIn = v)} />
    <Num label={`Muzzle velocity (${velLabel(u)})`} value={ammo.muzzleVelocityMps} from={(v) => velFrom(v, u)} to={(v) => velTo(v, u)} step={u === "imperial" ? 5 : 1} digits={u === "imperial" ? 0 : 1} min={100} onchange={(v) => (ammo.muzzleVelocityMps = v)} />
    <Num label={`MV measured at (${tempLabel(u)})`} value={ammo.mvTempC} from={(v) => tempFrom(v, u)} to={(v) => tempTo(v, u)} digits={0} onchange={(v) => (ammo.mvTempC = v)} />
    <Num label="Temp sensitivity (%/°C)" value={ammo.tempSensitivity} step={0.05} min={0} max={5} digits={2} onchange={(v) => (ammo.tempSensitivity = v)} />
  </div>
  <details>
    <summary>⚙ Velocity-banded BC</summary>
    <label class="row"><input type="checkbox" checked={bands} onchange={(e) => toggleBands((e.target as HTMLInputElement).checked)} /> Use bands (high to low)</label>
    {#if ammo.bcSegments}
      {#each ammo.bcSegments as seg, i}
        <div class="grid2">
          <Num label={`Above (${velLabel(u)})`} value={seg[0] * 0.3048} from={(v) => velFrom(v, u)} to={(v) => velTo(v, u)} step={u === "imperial" ? 50 : 10} digits={0} min={0} onchange={(v) => { ammo.bcSegments![i] = [v / 0.3048, seg[1]]; }} />
          <Num label="BC" value={seg[1]} step={0.001} digits={3} min={0} onchange={(v) => { ammo.bcSegments![i] = [seg[0], v]; }} />
        </div>
      {/each}
      <div class="row">
        <button class="small" onclick={() => (ammo.bcSegments = [...ammo.bcSegments!, [0, ammo.bc]])}>+ band</button>
        <button class="small" disabled={ammo.bcSegments.length < 2} onclick={() => (ammo.bcSegments = ammo.bcSegments!.slice(0, -1))}>− band</button>
      </div>
    {/if}
  </details>
</div>
