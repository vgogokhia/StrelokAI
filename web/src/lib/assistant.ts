/** Client side of the AI assistant. Builds the state snapshot for the model and executes its tool calls against
 *  the store with the app's own solver. Mutating tools are previewed (run on the live store, captured, reverted)
 *  so the UI can ask the user before applying; every applied run keeps an undo snapshot. */
import { store, defaultRifle, defaultAmmo, type RifleProfile, type AmmoProfile } from "./store.svelte";
import { CLICK_OPTIONS } from "./units";
import { LIBRARY, type BulletPreset } from "./library";
import { CHAMBERING_NAMES, LIBRARY_CALIBER_TO_CHAMBERING } from "./calibers";
import { RETICLES } from "./reticles";
import { billing, FREE_RIFLES, FREE_AMMO } from "./billing.svelte";
import { fetchWeather } from "./weather";
import { atRange, calculateSolution, dropMrad, windageMrad, trueMuzzleVelocity, trueBallisticCoefficient } from "../core";

const r1 = (x: number, d = 1) => +x.toFixed(d);
type Input = Record<string, any>;
const fin = (x: unknown): x is number => typeof x === "number" && Number.isFinite(x);
const clamp = (x: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, x));

/** Tools that only read — run immediately, never need confirmation. */
export const READ_ONLY = new Set(["search_library"]);

export function snapshotState() {
  const c = store.cond, r = store.rifle, a = store.ammoSel, s = store.settings;
  const pt = store.target();
  const dope = [100, 200, 300, 400, 500, 600, 800, 1000].map((m) => { const p = atRange(store.solve(Math.max(m, c.targetRangeM)), m); return p ? { range_m: m, elev_mrad: r1(-dropMrad(p), 2), wind_mrad: r1(-windageMrad(p), 2) } : null; }).filter(Boolean);
  return JSON.stringify({
    settings: { units: s.units, angular: s.angular, click: s.click, click_options: Object.keys(CLICK_OPTIONS),
      reticle: { name: s.reticle, focal_plane: s.reticleFp, true_at_mag: s.reticleCalMag, current_mag: s.reticleCurMag, scope_min_mag: s.scopeMinMag, scope_max_mag: s.scopeMaxMag, options: RETICLES.map((x) => x.name) },
      hit_probability: s.wez },
    selected_rifle: r, selected_ammo: { ...a, effective_mv_mps: r1(store.actualMv) },
    rifles: store.rifles.map((x) => `${x.name} (${x.chambering})`), ammo_list: store.ammo.map((x) => `${x.name} (${x.cartridge}, ${x.massGrains} gr)`),
    chamberings: CHAMBERING_NAMES,
    plan: billing.limited ? { free: true, max_rifles: FREE_RIFLES, max_ammo: FREE_AMMO } : { free: false },
    conditions: { ...c },
    solution_at_target: pt ? { elev_mrad_up: r1(-dropMrad(pt), 2), wind_mrad_right: r1(-windageMrad(pt), 2), tof_s: r1(pt.timeS, 2), velocity_mps: Math.round(pt.velocityMps) } : null,
    dope,
  });
}

export function takeUndo() {
  return JSON.stringify({ cond: store.cond, settings: store.settings, rifles: store.rifles, ammo: store.ammo, rifleId: store.rifleId, ammoId: store.ammoId });
}
export function applyUndo(json: string) {
  const u = JSON.parse(json);
  store.rifles = u.rifles; store.ammo = u.ammo; store.rifleId = u.rifleId; store.ammoId = u.ammoId;
  Object.assign(store.cond, u.cond); Object.assign(store.settings, u.settings);
}

function searchLibrary(i: Input) {
  const q = String(i.query ?? "").toLowerCase().replace(/[^a-z0-9. ]/g, " ").split(/\s+/).filter((w) => w.length > 1 && !["gr", "grain", "grains"].includes(w));
  const cal = String(i.caliber ?? "").toLowerCase().replace(/[^a-z0-9.]/g, "");
  const scored = LIBRARY.map((b) => {
    const hay = `${b.caliber} ${b.manufacturer} ${b.bullet} ${b.massGrains}`.toLowerCase();
    let s = q.reduce((n, w) => n + (hay.includes(w) ? 2 : 0), 0);
    if (cal && b.caliber.toLowerCase().replace(/[^a-z0-9.]/g, "").includes(cal)) s += 3;
    if (fin(i.grains)) s += Math.abs(b.massGrains - i.grains) <= 2 ? 4 : Math.abs(b.massGrains - i.grains) <= 10 ? 1 : -2;
    return { b, s };
  }).filter((x) => x.s > 0).sort((a, b) => b.s - a.s).slice(0, 8);
  return scored.map(({ b }) => ({ library_id: b.id, name: `${b.manufacturer} ${b.bullet}`, caliber: b.caliber, type: b.type, grains: b.massGrains, bc_g7: b.bcG7, bc_g1: b.bcG1, default_mv_mps: b.defaultMvMps }));
}

const RIFLE_FIELDS: Record<string, [keyof RifleProfile, number, number, number]> = {
  zero_range_m: ["zeroRangeM", 10, 1000, 0], sight_height_mm: ["sightHeightMm", 10, 150, 1], twist_in: ["twistRateIn", 5, 40, 2],
  zero_temp_c: ["zeroTempC", -40, 50, 1], zero_offset_vertical_cm: ["zeroOffsetVCm", -100, 100, 1], zero_offset_horizontal_cm: ["zeroOffsetHCm", -100, 100, 1],
};
const AMMO_FIELDS: Record<string, [keyof AmmoProfile, number, number, number]> = {
  bc: ["bc", 0.05, 1.5, 3], mass_grains: ["massGrains", 10, 800, 1], diameter_in: ["diameterIn", 0.17, 0.6, 3], length_in: ["lengthIn", 0.3, 3, 3],
  muzzle_velocity_mps: ["muzzleVelocityMps", 100, 1500, 1], mv_temp_c: ["mvTempC", -40, 60, 1], temp_sensitivity_pct_per_c: ["tempSensitivity", 0, 1, 3],
};
function patch<T extends object>(obj: T, i: Input, fields: Record<string, [keyof T, number, number, number]>, changed: string[], label: string) {
  for (const [k, [key, lo, hi, d]] of Object.entries(fields)) if (fin(i[k])) { const old = obj[key]; (obj as any)[key] = r1(clamp(i[k], lo, hi), d); changed.push(`${label} ${String(key)} ${old ?? "—"} → ${(obj as any)[key]}`); }
}
const chamb = (s: unknown) => { if (typeof s !== "string") return null; const t = s.toLowerCase().replace(/[^a-z0-9.]/g, ""); return CHAMBERING_NAMES.find((c) => c.toLowerCase().replace(/[^a-z0-9.]/g, "").includes(t) || t.includes(c.toLowerCase().replace(/[^a-z0-9.]/g, "").split("/")[0])) ?? null; };
const byName = <T extends { name: string }>(list: T[], q: unknown) => typeof q === "string" && q.trim() ? list.find((x) => x.name.toLowerCase() === q.toLowerCase().trim()) ?? list.find((x) => x.name.toLowerCase().includes(q.toLowerCase().trim())) : undefined;
function ammoFromPreset(b: BulletPreset): Partial<AmmoProfile> {
  const g7 = b.bcG7 != null;
  return { name: `${b.manufacturer} ${b.bullet}`, dragModel: g7 ? "G7" : "G1", bc: g7 ? b.bcG7! : b.bcG1!, bcSegments: null, massGrains: b.massGrains, diameterIn: b.diameterIn, lengthIn: b.lengthIn, muzzleVelocityMps: b.defaultMvMps, cartridge: LIBRARY_CALIBER_TO_CHAMBERING[b.caliber] ?? store.rifle.chambering };
}

export async function runTool(name: string, i: Input): Promise<string> {
  const c = store.cond, changed: string[] = [];
  const err = (e: string, extra: object = {}) => JSON.stringify({ error: e, ...extra });
  const set = (label: string, get: () => number, put: (v: number) => void, v: unknown, lo: number, hi: number, d = 1) => {
    if (!fin(v)) return; const old = get(); const nv = r1(clamp(v, lo, hi), d); put(nv); changed.push(`${label} ${old} → ${nv}`);
  };
  switch (name) {
    case "search_library": return JSON.stringify({ results: searchLibrary(i), note: "type 'ammo' = factory load, 'bullet' = component bullet (reloading data)" });
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
      if (i.target_moving === "left_to_right") { c.targetDirDeg = 90; changed.push("target moving L→R"); } else if (i.target_moving === "right_to_left") { c.targetDirDeg = 270; changed.push("target moving R→L"); }
      break;
    }
    case "sync_weather": {
      try { const w = await fetchWeather(c.lat, c.lon);
        set("temp °C", () => c.tempC, (v) => (c.tempC = v), w.temperatureC, -50, 60); set("pressure mbar", () => c.pressureMbar, (v) => (c.pressureMbar = v), w.pressureMbar, 500, 1100, 0);
        set("humidity %", () => c.humidityPct, (v) => (c.humidityPct = v), w.humidityPct, 0, 100, 0); set("wind m/s", () => c.windSpeedMps, (v) => (c.windSpeedMps = v), w.windSpeedMps, 0, 40);
        set("wind from °", () => c.windDirDeg, (v) => (c.windDirDeg = v), w.windDirectionDeg, 0, 360, 0);
      } catch { return err("weather service unreachable (offline?)"); }
      break;
    }
    case "true_from_impact": {
      if (!fin(i.range_m) || !fin(i.impact_vertical_cm)) return err("range_m and impact_vertical_cm are required");
      const R = clamp(i.range_m, 50, 2500), inp = store.inputs(R);
      const p = atRange(calculateSolution(inp), R); if (!p) return err("range out of solution");
      const obs = dropMrad(p) + (i.impact_vertical_cm / 100 / R) * 1000;
      const method = i.method === "velocity" || i.method === "bc" ? i.method : R <= 500 ? "velocity" : "bc";
      const a = store.ammoSel;
      if (method === "velocity") {
        const t = trueMuzzleVelocity(inp, obs, R); if (!t.converged) return err("truing did not converge", { best_mps: r1(t.value) });
        const comp = store.actualMv / a.muzzleVelocityMps || 1; const old = a.muzzleVelocityMps;
        a.muzzleVelocityMps = r1(t.value / comp); changed.push(`${a.name} MV ${old} → ${a.muzzleVelocityMps} m/s`);
      } else {
        const t = trueBallisticCoefficient(inp, obs, R); if (!t.converged) return err("truing did not converge, true velocity first", { best_bc: r1(t.value, 3) });
        const old = a.bc; a.bc = r1(t.value, 3); a.bcSegments = null; changed.push(`${a.name} ${a.dragModel} BC ${old} → ${a.bc}`);
      }
      break;
    }
    case "set_zero_offset": {
      const r = store.rifle, add = i.add !== false;
      set("zero offset vertical cm", () => r.zeroOffsetVCm, (v) => (r.zeroOffsetVCm = v), fin(i.vertical_cm) ? (add ? r.zeroOffsetVCm + i.vertical_cm : i.vertical_cm) : undefined, -100, 100);
      set("zero offset horizontal cm", () => r.zeroOffsetHCm, (v) => (r.zeroOffsetHCm = v), fin(i.horizontal_cm) ? (add ? r.zeroOffsetHCm + i.horizontal_cm : i.horizontal_cm) : undefined, -100, 100);
      break;
    }
    case "create_rifle": {
      if (billing.limited && store.rifles.length >= FREE_RIFLES) return err(`free plan allows ${FREE_RIFLES} rifle — Pro removes the limit`);
      const ch = chamb(i.chambering); if (!ch) return err("unknown chambering", { chamberings: CHAMBERING_NAMES });
      const r = { ...defaultRifle(), name: String(i.name || `Rifle ${store.rifles.length + 1}`).slice(0, 60), chambering: ch };
      if (i.twist_direction === "left" || i.twist_direction === "right") r.twistDirection = i.twist_direction;
      patch(r, i, RIFLE_FIELDS, [], "");
      store.addRifle(r); changed.push(`new rifle "${r.name}" (${ch}, zero ${r.zeroRangeM} m, sight ${r.sightHeightMm} mm, twist 1:${r.twistRateIn}) — selected`);
      break;
    }
    case "create_ammo": {
      if (billing.limited && store.ammo.length >= FREE_AMMO) return err(`free plan allows ${FREE_AMMO} loads — Pro removes the limit`);
      let base: Partial<AmmoProfile> = {};
      if (i.library_id) { const b = LIBRARY.find((x) => x.id === i.library_id); if (!b) return err("library_id not found — call search_library"); base = ammoFromPreset(b); }
      const a: AmmoProfile = { ...defaultAmmo(), ...base, name: String(i.name || base.name || `Ammo ${store.ammo.length + 1}`).slice(0, 60) } as AmmoProfile;
      const ch = chamb(i.cartridge); if (ch) a.cartridge = ch; else if (!base.cartridge) a.cartridge = store.rifle.chambering;
      if (i.drag_model === "G1" || i.drag_model === "G7") a.dragModel = i.drag_model;
      patch(a, i, AMMO_FIELDS, [], "");
      if (fin(i.bc)) a.bcSegments = null;
      store.addAmmo(a); changed.push(`new load "${a.name}" (${a.cartridge}, ${a.massGrains} gr, ${a.dragModel} ${a.bc}, ${a.muzzleVelocityMps} m/s) — selected`);
      break;
    }
    case "update_rifle": {
      const r = i.target_name ? byName(store.rifles, i.target_name) : store.rifle; if (!r) return err("rifle not found", { rifles: store.rifles.map((x) => x.name) });
      if (typeof i.name === "string" && i.name.trim()) { changed.push(`rifle name ${r.name} → ${i.name.trim()}`); r.name = i.name.trim().slice(0, 60); }
      if (i.chambering) { const ch = chamb(i.chambering); if (!ch) return err("unknown chambering", { chamberings: CHAMBERING_NAMES }); changed.push(`chambering ${r.chambering} → ${ch}`); r.chambering = ch; }
      if (i.twist_direction === "left" || i.twist_direction === "right") { changed.push(`twist direction → ${i.twist_direction}`); r.twistDirection = i.twist_direction; }
      patch(r, i, RIFLE_FIELDS, changed, r.name);
      break;
    }
    case "update_ammo": {
      const a = i.target_name ? byName(store.ammo, i.target_name) : store.ammoSel; if (!a) return err("ammo not found", { ammo: store.ammo.map((x) => x.name) });
      if (typeof i.name === "string" && i.name.trim()) { changed.push(`load name ${a.name} → ${i.name.trim()}`); a.name = i.name.trim().slice(0, 60); }
      if (i.cartridge) { const ch = chamb(i.cartridge); if (ch) { changed.push(`cartridge ${a.cartridge} → ${ch}`); a.cartridge = ch; } }
      if (i.drag_model === "G1" || i.drag_model === "G7") { changed.push(`drag model ${a.dragModel} → ${i.drag_model}`); a.dragModel = i.drag_model; }
      patch(a, i, AMMO_FIELDS, changed, a.name);
      if (fin(i.bc)) a.bcSegments = null;
      break;
    }
    case "delete_profile": {
      if (i.kind === "rifle") { const r = byName(store.rifles, i.name); if (!r) return err("rifle not found"); if (store.rifles.length < 2) return err("cannot delete the only rifle"); store.deleteRifle(r.id); changed.push(`deleted rifle "${r.name}"`); }
      else if (i.kind === "ammo") { const a = byName(store.ammo, i.name); if (!a) return err("ammo not found"); if (store.ammo.length < 2) return err("cannot delete the only load"); store.deleteAmmo(a.id); changed.push(`deleted load "${a.name}"`); }
      else return err("kind must be rifle or ammo");
      break;
    }
    case "select_profile": {
      const rf = byName(store.rifles, i.rifle_name); if (rf) { store.rifleId = rf.id; changed.push(`rifle → ${rf.name}`); } else if (i.rifle_name) return err(`no rifle matching "${i.rifle_name}"`, { rifles: store.rifles.map((x) => x.name) });
      const am = byName(store.ammo, i.ammo_name); if (am) { store.ammoId = am.id; changed.push(`ammo → ${am.name}`); } else if (i.ammo_name) return err(`no ammo matching "${i.ammo_name}"`, { ammo: store.ammo.map((x) => x.name) });
      break;
    }
    case "set_settings": {
      const s = store.settings;
      if (i.units === "metric" || i.units === "imperial") { changed.push(`units ${s.units} → ${i.units}`); s.units = i.units; }
      if (i.angular === "MRAD" || i.angular === "MOA") { changed.push(`angular ${s.angular} → ${i.angular}`); s.angular = i.angular; }
      if (typeof i.click === "string" && CLICK_OPTIONS[i.click] != null) { changed.push(`click ${s.click} → ${i.click}`); s.click = i.click; }
      break;
    }
    case "set_reticle": {
      const s = store.settings;
      if (typeof i.reticle === "string") { const rt = RETICLES.find((x) => x.name.toLowerCase().includes(i.reticle.toLowerCase())); if (!rt) return err("unknown reticle", { options: RETICLES.map((x) => x.name) }); changed.push(`reticle ${s.reticle} → ${rt.name}`); s.reticle = rt.name; }
      if (i.focal_plane === "FFP" || i.focal_plane === "SFP") { changed.push(`focal plane ${s.reticleFp} → ${i.focal_plane}`); s.reticleFp = i.focal_plane; }
      set("reticle true at ×", () => s.reticleCalMag, (v) => (s.reticleCalMag = v), i.true_at_mag, 1, 60);
      set("current magnification ×", () => s.reticleCurMag, (v) => (s.reticleCurMag = v), i.current_mag, 1, 60);
      set("scope min ×", () => s.scopeMinMag, (v) => (s.scopeMinMag = v), i.scope_min_mag, 1, 60);
      set("scope max ×", () => s.scopeMaxMag, (v) => (s.scopeMaxMag = v), i.scope_max_mag, 1, 60);
      break;
    }
    case "set_hit_probability": {
      const w = store.settings.wez;
      set("group MOA", () => w.groupMoa, (v) => (w.groupMoa = v), i.group_moa, 0.1, 10);
      set("MV SD m/s", () => w.mvSdMps, (v) => (w.mvSdMps = v), i.mv_sd_mps, 0, 100);
      set("wind error m/s", () => w.windSdMps, (v) => (w.windSdMps = v), i.wind_error_mps, 0, 20);
      set("range error %", () => w.rangeSdPct, (v) => (w.rangeSdPct = v), i.range_error_pct, 0, 30, 0);
      set("target width cm", () => r1(w.targetWm * 100), (v) => (w.targetWm = v / 100), i.target_width_cm, 1, 500, 0);
      set("target height cm", () => r1(w.targetHm * 100), (v) => (w.targetHm = v / 100), i.target_height_cm, 1, 500, 0);
      if (i.shape === "rect" || i.shape === "ellipse") { w.shape = i.shape; changed.push(`target shape → ${i.shape}`); }
      break;
    }
    default: return err(`unknown tool ${name}`);
  }
  if (!changed.length) return err("nothing to change — check the parameters");
  const pt = store.target();
  return JSON.stringify({ ok: true, changed, new_solution_at_target: pt ? { range_m: store.cond.targetRangeM, elev_mrad_up: r1(-dropMrad(pt), 2), wind_mrad_right: r1(-windageMrad(pt), 2) } : null });
}

/** Runs a tool on the live store, records what it would change, then restores the previous state. */
export async function previewTool(name: string, input: Input): Promise<{ changed: string[]; error?: string; raw: string }> {
  const u = takeUndo();
  try { const raw = await runTool(name, input); const o = JSON.parse(raw); return { changed: o.changed ?? [], error: o.error, raw }; }
  finally { applyUndo(u); }
}
