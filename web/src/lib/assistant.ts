/** Client side of the AI assistant: builds the state snapshot sent to the model and executes its tool calls
 *  against the store with the app's own solver. Every run keeps a snapshot so the user can undo it. */
import { store } from "./store.svelte";
import { CLICK_OPTIONS } from "./units";
import { atRange, calculateSolution, dropMrad, windageMrad, trueMuzzleVelocity, trueBallisticCoefficient } from "../core";

const r1 = (x: number, d = 1) => +x.toFixed(d);

export function snapshotState() {
  const c = store.cond, r = store.rifle, a = store.ammoSel, s = store.settings;
  const pt = store.target();
  const dope = [100, 200, 300, 400, 500, 600, 800, 1000].map((m) => { const p = atRange(store.solve(Math.max(m, c.targetRangeM)), m); return p ? { range_m: m, elev_mrad: r1(-dropMrad(p), 2), wind_mrad: r1(-windageMrad(p), 2) } : null; }).filter(Boolean);
  return JSON.stringify({
    settings: { units: s.units, angular: s.angular, click: s.click, click_options: Object.keys(CLICK_OPTIONS) },
    rifle: { name: r.name, chambering: r.chambering, zero_range_m: r.zeroRangeM, sight_height_mm: r.sightHeightMm, zero_offset_cm: { vertical: r.zeroOffsetVCm, horizontal: r.zeroOffsetHCm } },
    ammo: { name: a.name, muzzle_velocity_mps: a.muzzleVelocityMps, effective_mv_mps: r1(store.actualMv), bc: a.bc, drag_model: a.dragModel },
    rifles: store.rifles.map((x) => x.name), ammo_list: store.ammo.map((x) => x.name),
    conditions: { target_range_m: c.targetRangeM, wind_speed_mps: c.windSpeedMps, wind_from_deg: c.windDirDeg, shooting_heading_deg: c.headingDeg, temperature_c: c.tempC, pressure_mbar: c.pressureMbar,
      humidity_pct: c.humidityPct, altitude_m: c.altitudeM, shot_angle_deg: c.shotAngleDeg, cant_deg: c.cantAngleDeg, target_speed_kmh: c.targetSpeedKmh },
    solution_at_target: pt ? { elev_mrad_up: r1(-dropMrad(pt), 2), wind_mrad_right: r1(-windageMrad(pt), 2), tof_s: r1(pt.timeS, 2), velocity_mps: Math.round(pt.velocityMps) } : null,
    dope,
  });
}

/** Deep copy of everything a tool can change. */
export function takeUndo() {
  return JSON.stringify({ cond: store.cond, settings: store.settings, rifle: store.rifle, ammo: store.ammoSel, rifleId: store.rifleId, ammoId: store.ammoId });
}
export function applyUndo(json: string) {
  const u = JSON.parse(json);
  store.rifleId = u.rifleId; store.ammoId = u.ammoId;
  Object.assign(store.cond, u.cond); Object.assign(store.settings, u.settings);
  const r = store.rifles.find((x) => x.id === u.rifle.id); if (r) Object.assign(r, u.rifle);
  const a = store.ammo.find((x) => x.id === u.ammo.id); if (a) Object.assign(a, u.ammo);
}

type Input = Record<string, any>;
const fin = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x);
const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));

export function runTool(name: string, i: Input): string {
  const c = store.cond, changed: string[] = [];
  const set = (label: string, get: () => number, put: (v: number) => void, v: unknown, lo: number, hi: number, d = 1) => {
    if (!fin(v)) return; const old = get(); const nv = r1(clamp(v, lo, hi), d); put(nv); changed.push(`${label} ${old} → ${nv}`);
  };
  switch (name) {
    case "set_conditions": {
      if (fin(i.target_range_m)) { const old = c.targetRangeM; store.setRange(clamp(i.target_range_m, 10, 3000)); changed.push(`range ${old} → ${c.targetRangeM} m`); }
      set("wind m/s", () => c.windSpeedMps, (v) => (c.windSpeedMps = v), i.wind_speed_mps, 0, 40);
      set("wind from °", () => c.windDirDeg, (v) => (c.windDirDeg = ((v % 360) + 360) % 360), i.wind_from_deg, -720, 720, 0);
      set("heading °", () => c.headingDeg, (v) => (c.headingDeg = ((v % 360) + 360) % 360), i.shooting_heading_deg, -720, 720, 0);
      set("temp °C", () => c.tempC, (v) => (c.tempC = v), i.temperature_c, -50, 60);
      set("pressure mbar", () => c.pressureMbar, (v) => (c.pressureMbar = v), i.pressure_mbar, 500, 1100, 0);
      set("humidity %", () => c.humidityPct, (v) => (c.humidityPct = v), i.humidity_pct, 0, 100, 0);
      set("altitude m", () => c.altitudeM, (v) => (c.altitudeM = v), i.altitude_m, -500, 6000, 0);
      set("shot angle °", () => c.shotAngleDeg, (v) => (c.shotAngleDeg = v), i.shot_angle_deg, -60, 60, 0);
      set("cant °", () => c.cantAngleDeg, (v) => (c.cantAngleDeg = v), i.cant_deg, -45, 45, 1);
      set("target speed km/h", () => c.targetSpeedKmh, (v) => (c.targetSpeedKmh = v), i.target_speed_kmh, 0, 120, 0);
      if (i.target_moving === "left_to_right") c.targetDirDeg = 90; else if (i.target_moving === "right_to_left") c.targetDirDeg = 270;
      break;
    }
    case "true_from_impact": {
      if (!fin(i.range_m) || !fin(i.impact_vertical_cm)) return JSON.stringify({ error: "range_m and impact_vertical_cm are required" });
      const R = clamp(i.range_m, 50, 2500);
      const inp = store.inputs(R);
      const p = atRange(calculateSolution(inp), R); if (!p) return JSON.stringify({ error: "range out of solution" });
      const obs = dropMrad(p) + (i.impact_vertical_cm / 100 / R) * 1000;
      const method = i.method === "velocity" || i.method === "bc" ? i.method : R <= 500 ? "velocity" : "bc";
      const a = store.ammoSel;
      if (method === "velocity") {
        const t = trueMuzzleVelocity(inp, obs, R); if (!t.converged) return JSON.stringify({ error: "truing did not converge", best_mps: r1(t.value) });
        const comp = store.actualMv / a.muzzleVelocityMps || 1; const old = a.muzzleVelocityMps;
        a.muzzleVelocityMps = r1(t.value / comp); changed.push(`muzzle velocity ${old} → ${a.muzzleVelocityMps} m/s`);
      } else {
        const t = trueBallisticCoefficient(inp, obs, R); if (!t.converged) return JSON.stringify({ error: "truing did not converge, try method velocity first", best_bc: r1(t.value, 3) });
        const old = a.bc; a.bc = r1(t.value, 3); a.bcSegments = null; changed.push(`${a.dragModel} BC ${old} → ${a.bc}`);
      }
      break;
    }
    case "set_zero_offset": {
      const r = store.rifle, add = i.add !== false;
      set("zero offset vertical cm", () => r.zeroOffsetVCm, (v) => (r.zeroOffsetVCm = v), fin(i.vertical_cm) ? (add ? r.zeroOffsetVCm + i.vertical_cm : i.vertical_cm) : undefined, -100, 100);
      set("zero offset horizontal cm", () => r.zeroOffsetHCm, (v) => (r.zeroOffsetHCm = v), fin(i.horizontal_cm) ? (add ? r.zeroOffsetHCm + i.horizontal_cm : i.horizontal_cm) : undefined, -100, 100);
      break;
    }
    case "set_ammo": {
      const a = store.ammoSel;
      set("muzzle velocity m/s", () => a.muzzleVelocityMps, (v) => (a.muzzleVelocityMps = v), i.muzzle_velocity_mps, 100, 1500);
      if (fin(i.bc)) { const old = a.bc; a.bc = r1(clamp(i.bc, 0.05, 1.5), 3); a.bcSegments = null; changed.push(`BC ${old} → ${a.bc}`); }
      break;
    }
    case "set_settings": {
      const s = store.settings;
      if (i.units === "metric" || i.units === "imperial") { changed.push(`units ${s.units} → ${i.units}`); s.units = i.units; }
      if (i.angular === "MRAD" || i.angular === "MOA") { changed.push(`angular ${s.angular} → ${i.angular}`); s.angular = i.angular; }
      if (typeof i.click === "string" && CLICK_OPTIONS[i.click] != null) { changed.push(`click ${s.click} → ${i.click}`); s.click = i.click; }
      break;
    }
    case "select_profile": {
      const find = <T extends { id: string; name: string }>(list: T[], q: unknown) => typeof q === "string" && q.trim() ? list.find((x) => x.name.toLowerCase().includes(q.toLowerCase().trim())) : undefined;
      const rf = find(store.rifles, i.rifle_name); if (rf) { store.rifleId = rf.id; changed.push(`rifle → ${rf.name}`); } else if (i.rifle_name) return JSON.stringify({ error: `no rifle matching "${i.rifle_name}"`, rifles: store.rifles.map((x) => x.name) });
      const am = find(store.ammo, i.ammo_name); if (am) { store.ammoId = am.id; changed.push(`ammo → ${am.name}`); } else if (i.ammo_name) return JSON.stringify({ error: `no ammo matching "${i.ammo_name}"`, ammo: store.ammo.map((x) => x.name) });
      break;
    }
    default: return JSON.stringify({ error: `unknown tool ${name}` });
  }
  const pt = store.target();
  return JSON.stringify({ ok: true, changed, new_solution_at_target: pt ? { range_m: store.cond.targetRangeM, elev_mrad_up: r1(-dropMrad(pt), 2), wind_mrad_right: r1(-windageMrad(pt), 2) } : null });
}
