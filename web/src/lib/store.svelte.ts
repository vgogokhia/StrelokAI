/**
 * Application state (Svelte 5 runes) persisted to localStorage.
 * Everything the solver needs lives here in metric; UI converts at the edge.
 */
import { atRange, applyZeroOffset, applyMvCurve, calculateSolution, type BallisticSolution, type CalcInputs } from "../core";
import type { UnitSystem, Angular } from "./units";
import { CLICK_OPTIONS } from "./units";

export interface RifleProfile {
  id: string;
  name: string;
  chambering: string;
  zeroRangeM: number;
  sightHeightMm: number;
  twistRateIn: number;
  twistDirection: "right" | "left";
  zeroTempC: number | null;
  zeroPressureMbar: number | null;
  zeroHumidityPct: number | null;
  zeroOffsetVCm: number;
  zeroOffsetHCm: number;
}

export interface AmmoProfile {
  id: string;
  name: string;
  cartridge: string;
  dragModel: "G1" | "G7";
  bc: number;
  bcSegments: Array<[number, number]> | null;
  massGrains: number;
  diameterIn: number;
  lengthIn: number;
  muzzleVelocityMps: number;
  mvTempC: number;
  tempSensitivity: number; // %/°C
}

export interface Conditions {
  targetRangeM: number;
  windSpeedMps: number;
  windDirDeg: number; // FROM, absolute
  headingDeg: number; // shooting direction
  tempC: number;
  pressureMbar: number;
  humidityPct: number;
  altitudeM: number;
  lat: number;
  lon: number;
  shotAngleDeg: number;
  cantAngleDeg: number;
}

export interface Settings {
  units: UnitSystem;
  angular: Angular;
  click: string;
  reticle: string;
  reticleFp: "FFP" | "SFP";
  reticleCalMag: number;
  reticleCurMag: number;
  turretPerRev: number;
}

const uid = () => Math.random().toString(36).slice(2, 10);

export const defaultRifle = (): RifleProfile => ({
  id: uid(), name: "My rifle", chambering: ".308 Win / 7.62", zeroRangeM: 100, sightHeightMm: 40,
  twistRateIn: 11.25, twistDirection: "right", zeroTempC: null, zeroPressureMbar: null, zeroHumidityPct: null,
  zeroOffsetVCm: 0, zeroOffsetHCm: 0,
});
export const defaultAmmo = (): AmmoProfile => ({
  id: uid(), name: "175 gr SMK", cartridge: ".308 Win / 7.62", dragModel: "G7", bc: 0.243, bcSegments: null,
  massGrains: 175, diameterIn: 0.308, lengthIn: 1.24, muzzleVelocityMps: 792, mvTempC: 15, tempSensitivity: 0.1,
});

const GUEST_KEY = "bge_state_v1";
const hadGuestProfiles = localStorage.getItem(GUEST_KEY) !== null;
let owner = localStorage.getItem("bge_owner") || "";
const stateKey = () => owner ? `bge_account_${owner}` : GUEST_KEY;

interface Persisted {
  rifles: RifleProfile[];
  ammo: AmmoProfile[];
  rifleId: string;
  ammoId: string;
  cond: Conditions;
  settings: Settings;
  recent: number[];
}

function load(): Persisted | null {
  try {
    const raw = localStorage.getItem(stateKey());
    return raw ? (JSON.parse(raw) as Persisted) : null;
  } catch {
    return null;
  }
}

class Store {
  rifles = $state<RifleProfile[]>([defaultRifle()]);
  ammo = $state<AmmoProfile[]>([defaultAmmo()]);
  rifleId = $state("");
  ammoId = $state("");
  cond = $state<Conditions>({
    targetRangeM: 500, windSpeedMps: 3, windDirDeg: 270, headingDeg: 0, tempC: 15, pressureMbar: 1013,
    humidityPct: 50, altitudeM: 0, lat: 41.7151, lon: 44.8271, shotAngleDeg: 0, cantAngleDeg: 0,
  });
  settings = $state<Settings>({
    units: "metric", angular: "MRAD", click: "0.1 MRAD", reticle: "MIL-Dot", reticleFp: "FFP",
    reticleCalMag: 10, reticleCurMag: 10, turretPerRev: 10,
  });
  recent = $state<number[]>([]);
  weatherStatus = $state("");

  constructor() {
    const p = load();
    if (p) {
      this.rifles = p.rifles?.length ? p.rifles : [defaultRifle()];
      this.ammo = p.ammo?.length ? p.ammo : [defaultAmmo()];
      this.rifleId = p.rifleId;
      this.ammoId = p.ammoId;
      this.cond = { ...this.cond, ...p.cond };
      this.settings = { ...this.settings, ...p.settings };
      this.recent = p.recent ?? [];
    }
    if (!this.rifles.find((r) => r.id === this.rifleId)) this.rifleId = this.rifles[0].id;
    if (!this.ammo.find((a) => a.id === this.ammoId)) this.ammoId = this.ammo[0].id;
  }

  get rifle(): RifleProfile { return this.rifles.find((r) => r.id === this.rifleId) ?? this.rifles[0]; }
  get ammoSel(): AmmoProfile { return this.ammo.find((a) => a.id === this.ammoId) ?? this.ammo[0]; }
  get clickMrad(): number { return CLICK_OPTIONS[this.settings.click] ?? 0.1; }
  get windRelDeg(): number { return ((this.cond.windDirDeg - this.cond.headingDeg) % 360 + 360) % 360; }

  /** Temperature-compensated muzzle velocity. */
  get actualMv(): number {
    const a = this.ammoSel;
    return applyMvCurve(a.muzzleVelocityMps, a.mvTempC, this.cond.tempC, a.tempSensitivity);
  }

  inputs(targetRangeM = this.cond.targetRangeM): CalcInputs {
    const r = this.rifle;
    const a = this.ammoSel;
    const c = this.cond;
    return {
      muzzleVelocityMps: this.actualMv,
      bcG7: a.dragModel === "G7" ? a.bc : null,
      bcG1: a.dragModel === "G1" ? a.bc : null,
      massGrains: a.massGrains,
      diameterIn: a.diameterIn,
      zeroRangeM: r.zeroRangeM,
      targetRangeM,
      temperatureC: c.tempC,
      pressureMbar: c.pressureMbar,
      humidityPct: c.humidityPct,
      altitudeM: c.altitudeM,
      windSpeedMps: c.windSpeedMps,
      windDirectionDeg: this.windRelDeg,
      latitudeDeg: c.lat,
      azimuthDeg: c.headingDeg,
      bulletLengthIn: a.lengthIn,
      twistRateIn: r.twistRateIn,
      twistDirection: r.twistDirection,
      sightHeightMm: r.sightHeightMm,
      elevationAngleDeg: c.shotAngleDeg,
      cantAngleDeg: c.cantAngleDeg,
      bcSegments: a.bcSegments,
      zeroTemperatureC: r.zeroTempC,
      zeroPressureMbar: r.zeroPressureMbar,
      zeroHumidityPct: r.zeroHumidityPct,
    };
  }

  /** Solve for the current state; cached on a key of the inputs. */
  private cacheKey = "";
  private cacheSol: BallisticSolution | null = null;
  solve(targetRangeM = this.cond.targetRangeM): BallisticSolution {
    const inp = this.inputs(targetRangeM);
    const r = this.rifle;
    const key = JSON.stringify([inp, r.zeroOffsetVCm, r.zeroOffsetHCm]);
    if (key === this.cacheKey && this.cacheSol) return this.cacheSol;
    const sol = applyZeroOffset(calculateSolution(inp), r.zeroRangeM, r.zeroOffsetVCm, r.zeroOffsetHCm);
    this.cacheKey = key;
    this.cacheSol = sol;
    return sol;
  }

  target() { return atRange(this.solve(), this.cond.targetRangeM); }

  setRange(m: number) {
    this.cond.targetRangeM = Math.max(10, Math.min(3000, Math.round(m * 10) / 10));
  }
  pushRecent(m: number) {
    const r = Math.round(m);
    this.recent = [r, ...this.recent.filter((x) => x !== r)].slice(0, 5);
  }

  addRifle(r: RifleProfile) { this.rifles = [...this.rifles, r]; this.rifleId = r.id; }
  addAmmo(a: AmmoProfile) { this.ammo = [...this.ammo, a]; this.ammoId = a.id; }
  deleteRifle(id: string) { if (this.rifles.length > 1) { this.rifles = this.rifles.filter((r) => r.id !== id); this.rifleId = this.rifles[0].id; } }
  deleteAmmo(id: string) { if (this.ammo.length > 1) { this.ammo = this.ammo.filter((a) => a.id !== id); this.ammoId = this.ammo[0].id; } }

  persist() {
    try {
      const p: Persisted = {
        rifles: $state.snapshot(this.rifles), ammo: $state.snapshot(this.ammo), rifleId: this.rifleId, ammoId: this.ammoId,
        cond: $state.snapshot(this.cond), settings: $state.snapshot(this.settings), recent: $state.snapshot(this.recent),
      };
      localStorage.setItem(stateKey(), JSON.stringify(p));
    } catch { /* storage unavailable */ }
  }
  get owner() { return owner; }
  hasSavedProfiles = load() !== null;
  profileData() {
    return JSON.parse(JSON.stringify({ rifles: this.rifles, ammo: this.ammo }));
  }
  applyProfiles(value: unknown) {
    const data = value as { rifles: RifleProfile[]; ammo: AmmoProfile[] };
    const valid = (records: unknown, template: object) => Array.isArray(records) && records.every(record =>
      record && Object.entries(template).every(([key, example]) => {
        const value = record[key];
        if (example === null) return value === null || typeof value === "number" && Number.isFinite(value) || key === "bcSegments" && Array.isArray(value);
        return typeof value === typeof example && (typeof value !== "number" || Number.isFinite(value));
      }));
    if (!data || !valid(data.rifles, defaultRifle()) || !valid(data.ammo, defaultAmmo())) throw new Error("Invalid profile data");
    this.rifles = data.rifles.length ? data.rifles : [defaultRifle()];
    this.ammo = data.ammo.length ? data.ammo : [defaultAmmo()];
    if (!this.rifles.some(r => r.id === this.rifleId)) this.rifleId = this.rifles[0].id;
    if (!this.ammo.some(a => a.id === this.ammoId)) this.ammoId = this.ammo[0].id;
    this.persist();
  }
  switchOwner(id: string): boolean {
    this.persist();
    owner = id;
    localStorage.setItem("bge_owner", id);
    let saved = load();
    // Import the original device profiles once. Guest data is retained as a backup.
    if (id && !saved && hadGuestProfiles && !localStorage.getItem("bge_guest_imported")) {
      const guest = localStorage.getItem(GUEST_KEY);
      if (guest) { saved = JSON.parse(guest); localStorage.setItem("bge_guest_imported", id); }
    }
    this.applyProfiles(saved || { rifles: [], ammo: [] });
    this.hasSavedProfiles = true;
    return Boolean(saved);
  }
  reset() {
    try { localStorage.removeItem(stateKey()); } catch { /* ignore */ }
    location.reload();
  }
}

export const store = new Store();
