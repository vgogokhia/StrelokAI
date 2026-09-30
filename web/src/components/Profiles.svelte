<script lang="ts">
  import { t } from "../lib/i18n.svelte";
  import { billing, FREE_RIFLES, FREE_AMMO } from "../lib/billing.svelte";
  const rifleLocked = $derived(billing.limited && store.rifles.length >= FREE_RIFLES);
  const ammoLocked = $derived(billing.limited && store.ammo.length >= FREE_AMMO);
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

<h2>🔫 {t("Rifle")}</h2>
<div class="card">
  <div class="row">
    <select style="flex:1" value={store.rifleId} onchange={(e) => (store.rifleId = (e.target as HTMLSelectElement).value)}>
      {#each store.rifles as r}<option value={r.id}>{r.name}</option>{/each}
    </select>
    <button class="small" title={rifleLocked ? t("Free plan: {n} rifle. Upgrade to Pro in My account.", { n: FREE_RIFLES }) : t("Add rifle")} onclick={() => rifleLocked ? alert(t("Free plan is limited to {n} rifle. Upgrade to Pro ($5 one-time) in My account for unlimited profiles.", { n: FREE_RIFLES })) : store.addRifle({ ...defaultRifle(), name: `${t("Rifle")} ${store.rifles.length + 1}` })}>{rifleLocked ? "🔒" : "＋"}</button>
    <button class="small" disabled={store.rifles.length < 2} onclick={() => store.deleteRifle(rifle.id)}>🗑</button>
  </div>
  <div class="grid2" style="margin-top:8px">
    <div><label class="f">{t("Name")}</label><input type="text" bind:value={rifle.name} /></div>
    <div><label class="f">{t("Chambering")}</label>
      <select bind:value={rifle.chambering}>{#each CHAMBERING_NAMES as c}<option>{c}</option>{/each}</select></div>
    <Num label={`${t("Zero range")} (${rangeLabel(u)})`} value={rifle.zeroRangeM} from={(v) => rangeFrom(v, u)} to={(v) => rangeTo(v, u)} step={25} min={10} max={600} digits={0} onchange={(v) => (rifle.zeroRangeM = v)} />
    <Num label={`${t("Sight height")} (${sightLabel(u)})`} value={rifle.sightHeightMm} from={(v) => sightFrom(v, u)} to={(v) => sightTo(v, u)} step={u === "imperial" ? 0.05 : 1} digits={u === "imperial" ? 2 : 0} min={0} onchange={(v) => (rifle.sightHeightMm = v)} />
    <Num label={t("Twist 1:X (in)")} value={rifle.twistRateIn} step={0.25} min={4} max={30} digits={2} onchange={(v) => (rifle.twistRateIn = v)} />
    <div><label class="f">{t("Twist direction")}</label>
      <div class="seg"><button class:on={rifle.twistDirection === "right"} onclick={() => (rifle.twistDirection = "right")}>{t("Right")}</button><button class:on={rifle.twistDirection === "left"} onclick={() => (rifle.twistDirection = "left")}>{t("Left")}</button></div></div>
  </div>
  <details>
    <summary>⚙ {t("Advanced zero")}</summary>
    <label class="row"><input type="checkbox" checked={zeroDiffers} onchange={(e) => toggleZero((e.target as HTMLInputElement).checked)} /> {t("Zeroed in different conditions")}</label>
    {#if zeroDiffers}
      <div class="grid3">
        <Num label={`${t("Zero temp")} (${tempLabel(u)})`} value={rifle.zeroTempC ?? 15} from={(v) => tempFrom(v, u)} to={(v) => tempTo(v, u)} digits={0} onchange={(v) => (rifle.zeroTempC = v)} />
        <Num label={`${t("Zero pressure")} (${pressLabel(u)})`} value={rifle.zeroPressureMbar ?? 1013.25} from={(v) => pressFrom(v, u)} to={(v) => pressTo(v, u)} step={u === "imperial" ? 0.01 : 1} digits={u === "imperial" ? 2 : 0} onchange={(v) => (rifle.zeroPressureMbar = v)} />
        <Num label={t("Zero RH (%)")} value={rifle.zeroHumidityPct ?? 50} step={5} min={0} max={100} digits={0} onchange={(v) => (rifle.zeroHumidityPct = v)} />
      </div>
    {/if}
    <div class="muted" style="margin-top:8px">{t("Zero offset: where the group sits at the zero range.")}</div>
    <div class="grid2">
      <Num label={`${t("Vertical")} (${smallLabel(u)}, ${t("+ high")})`} value={rifle.zeroOffsetVCm} from={(v) => smallFrom(v, u)} to={(v) => smallTo(v, u)} step={u === "imperial" ? 0.1 : 0.5} digits={u === "imperial" ? 2 : 1} onchange={(v) => (rifle.zeroOffsetVCm = v)} />
      <Num label={`${t("Horizontal")} (${smallLabel(u)}, ${t("+ right")})`} value={rifle.zeroOffsetHCm} from={(v) => smallFrom(v, u)} to={(v) => smallTo(v, u)} step={u === "imperial" ? 0.1 : 0.5} digits={u === "imperial" ? 2 : 1} onchange={(v) => (rifle.zeroOffsetHCm = v)} />
    </div>
  </details>
</div>

<h2><img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" /> {t("Ammo")}</h2>
<div class="card">
  <div class="row">
    <select style="flex:1" value={store.ammoId} onchange={(e) => (store.ammoId = (e.target as HTMLSelectElement).value)}>
      {#each store.ammo as a}<option value={a.id}>{a.name}{isCompatible(rifle.chambering, a.diameterIn, a.cartridge) ? "" : " ⚠"}</option>{/each}
    </select>
    <button class="small" title={ammoLocked ? t("Free plan: {n} loads. Upgrade to Pro in My account.", { n: FREE_AMMO }) : t("Add load")} onclick={() => ammoLocked ? alert(t("Free plan is limited to {n} loads. Upgrade to Pro ($5 one-time) in My account for unlimited profiles.", { n: FREE_AMMO })) : store.addAmmo({ ...defaultAmmo(), name: `${t("Ammo")} ${store.ammo.length + 1}`, cartridge: rifle.chambering })}>{ammoLocked ? "🔒" : "＋"}</button>
    <button class="small" disabled={store.ammo.length < 2} onclick={() => store.deleteAmmo(ammo.id)}>🗑</button>
  </div>
  {#if !ammoFits}<div class="note warn">⚠️ {t("This ammo ({a}) doesn't fit a {r} rifle.", { a: ammo.cartridge, r: rifle.chambering })}</div>{/if}

  {#if hasFeature("library")}
    <div style="margin-top:8px">
      <label class="f">📚 {t("Bullet library ({n} that fit this rifle)", { n: fitting.length })}</label>
      <input type="text" placeholder={t("search: Lapua, 175, subsonic…")} bind:value={filter} />
      <div class="row" style="margin-top:6px">
        <select style="flex:1" bind:value={preset}>
          <option value="">— {t("pick")} —</option>
          {#each shown as b}<option value={b.id}>{label(b)}</option>{/each}
        </select>
        <button class="small" disabled={!preset} onclick={applyPreset}>⬇ {t("Apply")}</button>
      </div>
    </div>
  {/if}

  <div class="grid2" style="margin-top:8px">
    <div><label class="f">{t("Name")}</label><input type="text" bind:value={ammo.name} /></div>
    <div><label class="f">{t("Cartridge")}</label>
      <select bind:value={ammo.cartridge}>{#each CHAMBERING_NAMES as c}<option>{c}</option>{/each}</select></div>
    <div><label class="f">{t("Drag model")}</label>
      <div class="seg"><button class:on={ammo.dragModel === "G1"} onclick={() => (ammo.dragModel = "G1")}>G1</button><button class:on={ammo.dragModel === "G7"} onclick={() => (ammo.dragModel = "G7")}>G7</button></div></div>
    <Num label={`BC (${ammo.dragModel})`} value={ammo.bc} step={0.001} min={0.05} max={1.5} digits={3} onchange={(v) => (ammo.bc = v)} />
    <Num label={t("Weight (gr)")} value={ammo.massGrains} step={1} min={10} max={800} digits={1} onchange={(v) => (ammo.massGrains = v)} />
    <Num label={t("Diameter (in)")} value={ammo.diameterIn} step={0.001} min={0.17} max={0.51} digits={4} onchange={(v) => (ammo.diameterIn = v)} />
    <Num label={t("Length (in)")} value={ammo.lengthIn} step={0.01} min={0.3} max={3} digits={3} onchange={(v) => (ammo.lengthIn = v)} />
    <Num label={`${t("Muzzle velocity")} (${velLabel(u)})`} value={ammo.muzzleVelocityMps} from={(v) => velFrom(v, u)} to={(v) => velTo(v, u)} step={u === "imperial" ? 5 : 1} digits={u === "imperial" ? 0 : 1} min={100} onchange={(v) => (ammo.muzzleVelocityMps = v)} />
    <Num label={`${t("MV measured at")} (${tempLabel(u)})`} value={ammo.mvTempC} from={(v) => tempFrom(v, u)} to={(v) => tempTo(v, u)} digits={0} onchange={(v) => (ammo.mvTempC = v)} />
    <Num label={t("Temp sensitivity (%/°C)")} value={ammo.tempSensitivity} step={0.05} min={0} max={5} digits={2} onchange={(v) => (ammo.tempSensitivity = v)} />
  </div>
  <details>
    <summary>⚙ {t("Velocity-banded BC")}</summary>
    <label class="row"><input type="checkbox" checked={bands} onchange={(e) => toggleBands((e.target as HTMLInputElement).checked)} /> {t("Use bands (high to low)")}</label>
    {#if ammo.bcSegments}
      {#each ammo.bcSegments as seg, i}
        <div class="grid2">
          <Num label={`${t("Above")} (${velLabel(u)})`} value={seg[0] * 0.3048} from={(v) => velFrom(v, u)} to={(v) => velTo(v, u)} step={u === "imperial" ? 50 : 10} digits={0} min={0} onchange={(v) => { ammo.bcSegments![i] = [v / 0.3048, seg[1]]; }} />
          <Num label="BC" value={seg[1]} step={0.001} digits={3} min={0} onchange={(v) => { ammo.bcSegments![i] = [seg[0], v]; }} />
        </div>
      {/each}
      <div class="row">
        <button class="small" onclick={() => (ammo.bcSegments = [...ammo.bcSegments!, [0, ammo.bc]])}>+ {t("band")}</button>
        <button class="small" disabled={ammo.bcSegments.length < 2} onclick={() => (ammo.bcSegments = ammo.bcSegments!.slice(0, -1))}>− {t("band")}</button>
      </div>
    {/if}
  </details>
</div>
