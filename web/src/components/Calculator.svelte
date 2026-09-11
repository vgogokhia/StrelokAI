<script lang="ts">
  import { store } from "../lib/store.svelte";
  import Num from "./Num.svelte";
  import { dropMrad, windageMrad, densityAltitudeFt, airDensity, speedOfSound, trueMuzzleVelocity, trueBallisticCoefficient } from "../core";
  import {
    rangeFrom, rangeTo, rangeLabel, windFrom, windTo, speedLabel, tempFrom, tempTo, tempLabel, pressFrom, pressTo, pressLabel,
    altFrom, altTo, altLabel, fmtAng, fmtDrop, fmtRange, fmtVel, fmtEnergy, fmtTemp, fmtPress, clicksFor, toAngular, fromAngular,
  } from "../lib/units";
  import { fetchWeather, locate } from "../lib/weather";

  const u = $derived(store.settings.units);
  const ang = $derived(store.settings.angular);
  const sol = $derived(store.solve());
  const pt = $derived(store.target());
  const quick = $derived(u === "imperial" ? [100, 300, 500, 800, 1000].map((y) => Math.round(y / 1.09361 * 10) / 10) : [100, 300, 500, 800, 1000]);
  const quickLabels = [100, 300, 500, 800, 1000];
  const dispRange = $derived(Math.round(rangeFrom(store.cond.targetRangeM, u)));

  const elevDir = $derived(pt && pt.dropM < 0 ? "UP" : "DOWN");
  const windDial = $derived(pt && pt.windageM < 0 ? "RIGHT" : "LEFT");
  const impactSide = $derived(pt && pt.windageM < 0 ? "left" : "right");

  const relDesc = $derived.by(() => {
    const w = store.windRelDeg;
    if (w >= 337 || w < 23) return "↓ headwind";
    if (w < 67) return "↙ 2 o'clock";
    if (w < 113) return "← from right";
    if (w < 157) return "↖ 4 o'clock";
    if (w < 203) return "↑ tailwind";
    if (w < 247) return "↗ 8 o'clock";
    if (w < 293) return "→ from left";
    return "↘ 10 o'clock";
  });

  const atmoLine = $derived.by(() => {
    const c = { temperatureC: store.cond.tempC, pressureMbar: store.cond.pressureMbar, humidityPct: store.cond.humidityPct, altitudeM: store.cond.altitudeM };
    return `DA ${Math.round(densityAltitudeFt(c)).toLocaleString()} ft · ρ ${airDensity(c).toFixed(3)} · a ${fmtVel(speedOfSound(c), u)} · ${fmtTemp(store.cond.tempC, u)} · ${fmtPress(store.cond.pressureMbar, u)}`;
  });

  // Transonic notice
  const transonic = $derived.by(() => {
    const tr = sol.trajectory;
    if (!tr.length || !pt) return null;
    if (tr[0].mach < 1) return null; // subsonic load: nothing to warn about
    if (pt.mach >= 1.2) return null;
    const first = (m: number) => tr.find((p) => p.mach < m)?.rangeM;
    const a = first(1.2), b = first(1.0);
    const where = [a ? `transonic from ~${fmtRange(a, u)}` : "", b ? `subsonic from ~${fmtRange(b, u)}` : ""].filter(Boolean).join(" · ");
    return pt.mach >= 1.0
      ? { kind: "info", text: `Entering the transonic zone at target (Mach ${pt.mach.toFixed(2)}). Solution still valid; confirm on steel. ${where}` }
      : { kind: "warn", text: `Subsonic at target (Mach ${pt.mach.toFixed(2)}) after the transonic zone — expect drift from prediction. ${where}` };
  });

  let busy = $state(false);
  let msg = $state<{ kind: string; text: string } | null>(null);
  async function syncWeather() {
    busy = true; msg = null;
    try {
      const w = await fetchWeather(store.cond.lat, store.cond.lon);
      store.cond.tempC = w.temperatureC; store.cond.pressureMbar = w.pressureMbar; store.cond.humidityPct = w.humidityPct;
      store.cond.windSpeedMps = w.windSpeedMps; store.cond.windDirDeg = w.windDirectionDeg;
      if (w.elevationM) store.cond.altitudeM = w.elevationM;
      msg = { kind: "ok", text: `✅ ${fmtTemp(w.temperatureC, u)} · ${fmtPress(w.pressureMbar, u)} · RH ${w.humidityPct.toFixed(0)}% · wind ${windFrom(w.windSpeedMps, u).toFixed(1)} ${speedLabel(u)} from ${w.windDirectionDeg.toFixed(0)}°` };
    } catch (e) {
      msg = { kind: "err", text: "Weather service unreachable (offline?). Values left unchanged." };
    } finally { busy = false; }
  }
  async function useLocation() {
    busy = true; msg = null;
    try {
      const l = await locate();
      store.cond.lat = +l.lat.toFixed(4); store.cond.lon = +l.lon.toFixed(4);
      if (l.alt != null) store.cond.altitudeM = Math.max(0, l.alt);
      msg = { kind: "ok", text: `📍 ${store.cond.lat}, ${store.cond.lon}` };
    } catch { msg = { kind: "err", text: "Location permission denied or unavailable." }; }
    finally { busy = false; }
  }

  // Phone sensors: compass heading + inclinometer
  let sensorHeading = $state<number | null>(null);
  let sensorPitch = $state<number | null>(null);
  let sensorRoll = $state<number | null>(null);
  let sensorsOn = $state(false);
  function onOrient(e: DeviceOrientationEvent & { webkitCompassHeading?: number }) {
    let h: number | null = null;
    if (e.webkitCompassHeading != null) h = e.webkitCompassHeading;
    else if (e.alpha != null) h = 360 - e.alpha;
    if (h != null) sensorHeading = ((Math.round(h) % 360) + 360) % 360;
    if (e.beta != null) { let b = e.beta; if (b > 90) b = 180 - b; if (b < -90) b = -180 - b; sensorPitch = Math.round(b * 2) / 2; }
    if (e.gamma != null) sensorRoll = Math.round(e.gamma * 2) / 2;
  }
  async function startSensors() {
    const D = DeviceOrientationEvent as unknown as { requestPermission?: () => Promise<string> };
    try {
      if (typeof D.requestPermission === "function") { const r = await D.requestPermission(); if (r !== "granted") return; }
      window.addEventListener("deviceorientationabsolute", onOrient as EventListener);
      window.addEventListener("deviceorientation", onOrient as EventListener);
      sensorsOn = true;
    } catch { /* unsupported */ }
  }

  // Truing
  let truingMode = $state<"mv" | "bc">("mv");
  let dial = $state(2.5);
  let truingMsg = $state<{ kind: string; text: string; apply?: () => void } | null>(null);
  function computeTruing() {
    const obs = -fromAngular(dial, ang);
    const inp = store.inputs();
    try {
      if (truingMode === "mv") {
        const r = trueMuzzleVelocity(inp, obs, store.cond.targetRangeM);
        const comp = store.actualMv / store.ammoSel.muzzleVelocityMps || 1;
        truingMsg = r.converged
          ? { kind: "ok", text: `True MV ≈ ${fmtVel(r.value, u, 1)} (Δ ${fmtVel(r.value - store.actualMv, u, 1)})`, apply: () => { store.ammoSel.muzzleVelocityMps = +(r.value / comp).toFixed(1); truingMsg = null; } }
          : { kind: "warn", text: `Did not converge (best ${fmtVel(r.value, u, 1)}). Check the observed drop.` };
      } else {
        const r = trueBallisticCoefficient(inp, obs, store.cond.targetRangeM);
        truingMsg = r.converged
          ? { kind: "ok", text: `True ${store.ammoSel.dragModel} BC ≈ ${r.value.toFixed(3)} (was ${store.ammoSel.bc.toFixed(3)})`, apply: () => { store.ammoSel.bc = +r.value.toFixed(3); store.ammoSel.bcSegments = null; truingMsg = null; } }
          : { kind: "warn", text: `Did not converge (best ${r.value.toFixed(3)}). True MV first.` };
      }
    } catch (e) { truingMsg = { kind: "err", text: String(e) }; }
  }
</script>

<h2 class="visually-hidden">Ballistics calculator</h2>
<div class="muted" style="margin:-6px 0 10px">{store.rifle.name} · {store.ammoSel.name} · {fmtVel(store.actualMv, u)}</div>

<div class="card">
  <div class="row" style="flex-wrap:nowrap">
    <div style="flex:1">
      <Num label={`Distance (${rangeLabel(u)})`} value={store.cond.targetRangeM} from={(m) => rangeFrom(m, u)} to={(v) => rangeTo(v, u)} step={5} min={10} max={3000} digits={0} onchange={(m) => store.setRange(m)} />
    </div>
  </div>
  <input type="range" min={u === "imperial" ? 50 : 50} max={u === "imperial" ? 2200 : 2000} step="5" value={dispRange}
    oninput={(e) => store.setRange(rangeTo(+(e.target as HTMLInputElement).value, u))} />
  <div class="chips">
    {#each quick as m, i}
      <button class:active={Math.abs(store.cond.targetRangeM - m) < 0.6} onclick={() => store.setRange(m)}>{quickLabels[i]}</button>
    {/each}
  </div>
  {#if store.recent.length}
    <div class="row muted" style="margin-top:6px">recent:
      {#each store.recent as r}<button class="small" onclick={() => store.setRange(r)}>{Math.round(rangeFrom(r, u))}</button>{/each}
    </div>
  {/if}
</div>

{#if pt}
  <div class="solution">
    <div class="elev">{clicksFor(dropMrad(pt), store.clickMrad)} {elevDir}</div>
    <div class="sub">ELEVATION · dial {elevDir} {fmtAng(Math.abs(dropMrad(pt)), ang)} · {store.settings.click} clicks</div>
    <div style="margin-top:8px"></div>
    <div class="wind">{clicksFor(windageMrad(pt), store.clickMrad)} {windDial[0]}</div>
    <div class="sub">WINDAGE · dial {windDial} {fmtAng(Math.abs(windageMrad(pt)), ang)} (impact {impactSide})</div>
    <div class="sub" style="color:#667;margin-top:6px">{fmtRange(store.cond.targetRangeM, u)} · impacts {fmtDrop(Math.abs(pt.dropM), u)} {pt.dropM < 0 ? "low" : "high"} · {fmtDrop(Math.abs(pt.windageM), u)} {impactSide}</div>
  </div>
  {#if transonic}<div class="note {transonic.kind}">{transonic.text}</div>{/if}
  {#if sol.stabilityFactor && sol.stabilityFactor < 1.3}<div class="note warn">Marginal stability (SG {sol.stabilityFactor.toFixed(2)}). Check twist and bullet length.</div>{/if}
{/if}

<div class="card">
  <h3>💨 Wind</h3>
  <div class="grid2">
    <Num label={`Speed (${speedLabel(u)})`} value={store.cond.windSpeedMps} from={(v) => windFrom(v, u)} to={(v) => windTo(v, u)} step={0.5} min={0} max={40} onchange={(v) => (store.cond.windSpeedMps = v)} />
    <Num label="Wind from (° true)" value={store.cond.windDirDeg} step={15} min={0} max={360} digits={0} onchange={(v) => (store.cond.windDirDeg = ((v % 360) + 360) % 360)} />
    <Num label="Shooting direction (°)" value={store.cond.headingDeg} step={5} min={0} max={359} digits={0} onchange={(v) => (store.cond.headingDeg = ((v % 360) + 360) % 360)} />
    <div>
      <label class="f">Phone compass / level</label>
      {#if !sensorsOn}
        <button style="width:100%" onclick={startSensors}>🧭 Enable sensors</button>
      {:else}
        <div class="row" style="gap:4px">
          <button class="small" style="flex:1" disabled={sensorHeading == null} onclick={() => sensorHeading != null && (store.cond.headingDeg = sensorHeading)}>🧭 {sensorHeading ?? "--"}°</button>
          <button class="small" style="flex:1" disabled={sensorPitch == null} onclick={() => { if (sensorPitch != null) store.cond.shotAngleDeg = Math.max(-60, Math.min(60, sensorPitch)); if (sensorRoll != null) store.cond.cantAngleDeg = Math.max(-45, Math.min(45, sensorRoll)); }}>📐 {sensorPitch ?? "--"}° / {sensorRoll ?? "--"}°</button>
        </div>
      {/if}
    </div>
  </div>
  <div class="muted" style="margin-top:6px">Relative: <b>{relDesc}</b> ({store.windRelDeg.toFixed(0)}° off the muzzle)</div>
  <details>
    <summary>Shot angle {store.cond.shotAngleDeg}° · cant {store.cond.cantAngleDeg}°</summary>
    <div class="grid2">
      <Num label="Shot angle (° + uphill)" value={store.cond.shotAngleDeg} step={1} min={-60} max={60} onchange={(v) => (store.cond.shotAngleDeg = v)} />
      <Num label="Cant (° + right)" value={store.cond.cantAngleDeg} step={1} min={-45} max={45} onchange={(v) => (store.cond.cantAngleDeg = v)} />
    </div>
  </details>
</div>

<div class="card">
  <h3>🌡️ Atmosphere</h3>
  <div class="muted" style="margin-bottom:8px">{atmoLine}</div>
  <div class="row" style="margin-bottom:8px">
    <button class="primary" style="flex:2" disabled={busy} onclick={syncWeather}>🌍 Sync weather</button>
    <button style="flex:1" disabled={busy} onclick={useLocation}>📍 Locate</button>
  </div>
  {#if msg}<div class="note {msg.kind}">{msg.text}</div>{/if}
  {#if store.weatherStatus}<div class="muted">{store.weatherStatus}</div>{/if}
  <div class="grid2">
    <Num label={`Temp (${tempLabel(u)})`} value={store.cond.tempC} from={(v) => tempFrom(v, u)} to={(v) => tempTo(v, u)} step={1} digits={0} onchange={(v) => (store.cond.tempC = v)} />
    <Num label={`Station pressure (${pressLabel(u)})`} value={store.cond.pressureMbar} from={(v) => pressFrom(v, u)} to={(v) => pressTo(v, u)} step={u === "imperial" ? 0.01 : 1} digits={u === "imperial" ? 2 : 0} onchange={(v) => (store.cond.pressureMbar = v)} />
    <Num label="Humidity (%)" value={store.cond.humidityPct} step={5} min={0} max={100} digits={0} onchange={(v) => (store.cond.humidityPct = v)} />
    <Num label={`Altitude (${altLabel(u)})`} value={store.cond.altitudeM} from={(v) => altFrom(v, u)} to={(v) => altTo(v, u)} step={100} min={0} digits={0} onchange={(v) => (store.cond.altitudeM = v)} />
    <Num label="Latitude" value={store.cond.lat} step={0.1} min={-90} max={90} digits={4} onchange={(v) => (store.cond.lat = v)} />
    <Num label="Longitude" value={store.cond.lon} step={0.1} min={-180} max={180} digits={4} onchange={(v) => (store.cond.lon = v)} />
  </div>
</div>

{#if pt}
  <div class="card">
    <h3>📊 Details at target</h3>
    <div class="grid3">
      <div class="metric"><div class="v">{pt.timeS.toFixed(2)} s</div><div class="l">time of flight</div></div>
      <div class="metric"><div class="v">{fmtVel(pt.velocityMps, u)}</div><div class="l">velocity</div></div>
      <div class="metric"><div class="v">{fmtEnergy(pt.energyJ, u)}</div><div class="l">energy</div></div>
      <div class="metric"><div class="v">{pt.mach.toFixed(2)}</div><div class="l">Mach</div></div>
      <div class="metric"><div class="v">{sol.stabilityFactor.toFixed(2)}</div><div class="l">SG</div></div>
      <div class="metric"><div class="v">{fmtAng(sol.spinDriftM / store.cond.targetRangeM * 1000, ang, 2, true)}</div><div class="l">spin drift</div></div>
    </div>
    <div class="muted" style="margin-top:6px">Aero jump {fmtAng(sol.aeroJumpMrad, ang, 3, true)} · Coriolis H {(sol.coriolisHorizontalM * 100).toFixed(1)} cm / V {(sol.coriolisVerticalM * 100).toFixed(1)} cm</div>
  </div>

  <div class="card">
    <details>
      <summary><img class="brand-icon" src="/icons/ballistics-b-192.png" alt="" width="24" height="24" /> Truing — match an observed drop (MV / BC)</summary>
      <div class="seg" style="margin:8px 0">
        <button class:on={truingMode === "mv"} onclick={() => (truingMode = "mv")}>Muzzle velocity (400–600 m)</button>
        <button class:on={truingMode === "bc"} onclick={() => (truingMode = "bc")}>BC (800 m+)</button>
      </div>
      <div class="muted">At the current distance {fmtRange(store.cond.targetRangeM, u)}, enter the elevation you ACTUALLY dialed to hit.</div>
      <Num label={`Actual dialed UP (${ang})`} value={dial} step={ang === "MOA" ? 0.25 : 0.05} min={0} digits={2} onchange={(v) => (dial = v)} />
      <button class="primary" style="width:100%;margin-top:8px" onclick={computeTruing}>🔧 Compute</button>
      {#if truingMsg}
        <div class="note {truingMsg.kind}">{truingMsg.text}</div>
        {#if truingMsg.apply}<button style="width:100%" onclick={truingMsg.apply}>✔ Apply to ammo profile</button>{/if}
      {/if}
    </details>
  </div>
{/if}
