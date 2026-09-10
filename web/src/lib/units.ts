/** Unit helpers. The solver is metric; conversion happens at the UI edge. */
export type UnitSystem = "metric" | "imperial";
export type Angular = "MRAD" | "MOA";

export const MRAD_TO_MOA = 3.43775;
export const M_TO_YD = 1.09361;
export const MPS_TO_FPS = 3.28084;
export const MBAR_TO_INHG = 0.02953;
export const MPH_TO_MPS = 0.44704;

export const CLICK_OPTIONS: Record<string, number> = {
  "0.1 MRAD": 0.1,
  "0.05 MRAD": 0.05,
  "1 cm/100 m": 0.1,
  "1/4 MOA": 0.25 / MRAD_TO_MOA,
  "1/8 MOA": 0.125 / MRAD_TO_MOA,
  "1/3 MOA": (1 / 3) / MRAD_TO_MOA,
  "1/2 MOA": 0.5 / MRAD_TO_MOA,
};

export const fmt = (v: number, d = 1) => v.toFixed(d);

export function rangeLabel(u: UnitSystem) { return u === "imperial" ? "yd" : "m"; }
export function speedLabel(u: UnitSystem) { return u === "imperial" ? "mph" : "m/s"; }
export function velLabel(u: UnitSystem) { return u === "imperial" ? "fps" : "m/s"; }
export function tempLabel(u: UnitSystem) { return u === "imperial" ? "°F" : "°C"; }
export function pressLabel(u: UnitSystem) { return u === "imperial" ? "inHg" : "mbar"; }
export function altLabel(u: UnitSystem) { return u === "imperial" ? "ft" : "m"; }
export function smallLabel(u: UnitSystem) { return u === "imperial" ? "in" : "cm"; }
export function sightLabel(u: UnitSystem) { return u === "imperial" ? "in" : "mm"; }

export const rangeFrom = (m: number, u: UnitSystem) => (u === "imperial" ? m * M_TO_YD : m);
export const rangeTo = (v: number, u: UnitSystem) => (u === "imperial" ? v / M_TO_YD : v);
export const velFrom = (mps: number, u: UnitSystem) => (u === "imperial" ? mps * MPS_TO_FPS : mps);
export const velTo = (v: number, u: UnitSystem) => (u === "imperial" ? v / MPS_TO_FPS : v);
export const windFrom = (mps: number, u: UnitSystem) => (u === "imperial" ? mps / MPH_TO_MPS : mps);
export const windTo = (v: number, u: UnitSystem) => (u === "imperial" ? v * MPH_TO_MPS : v);
export const tempFrom = (c: number, u: UnitSystem) => (u === "imperial" ? c * 9 / 5 + 32 : c);
export const tempTo = (v: number, u: UnitSystem) => (u === "imperial" ? (v - 32) * 5 / 9 : v);
export const pressFrom = (mb: number, u: UnitSystem) => (u === "imperial" ? mb * MBAR_TO_INHG : mb);
export const pressTo = (v: number, u: UnitSystem) => (u === "imperial" ? v / MBAR_TO_INHG : v);
export const altFrom = (m: number, u: UnitSystem) => (u === "imperial" ? m * MPS_TO_FPS : m);
export const altTo = (v: number, u: UnitSystem) => (u === "imperial" ? v / MPS_TO_FPS : v);
export const smallFrom = (cm: number, u: UnitSystem) => (u === "imperial" ? cm / 2.54 : cm);
export const smallTo = (v: number, u: UnitSystem) => (u === "imperial" ? v * 2.54 : v);
export const sightFrom = (mm: number, u: UnitSystem) => (u === "imperial" ? mm / 25.4 : mm);
export const sightTo = (v: number, u: UnitSystem) => (u === "imperial" ? v * 25.4 : v);

export const toAngular = (mrad: number, a: Angular) => (a === "MOA" ? mrad * MRAD_TO_MOA : mrad);
export const fromAngular = (v: number, a: Angular) => (a === "MOA" ? v / MRAD_TO_MOA : v);
export const clicksFor = (mrad: number, clickMrad: number) => Math.round(Math.abs(mrad) / clickMrad);

export function fmtRange(m: number, u: UnitSystem) { return `${Math.round(rangeFrom(m, u))} ${rangeLabel(u)}`; }
export function fmtVel(mps: number, u: UnitSystem, d = 0) { return `${velFrom(mps, u).toFixed(d)} ${velLabel(u)}`; }
export function fmtTemp(c: number, u: UnitSystem) { return `${tempFrom(c, u).toFixed(0)} ${tempLabel(u)}`; }
export function fmtPress(mb: number, u: UnitSystem) { return u === "imperial" ? `${pressFrom(mb, u).toFixed(2)} inHg` : `${mb.toFixed(0)} mbar`; }
export function fmtDrop(m: number, u: UnitSystem) { return u === "imperial" ? `${(m * 39.3701).toFixed(1)} in` : `${(m * 100).toFixed(1)} cm`; }
export function fmtEnergy(j: number, u: UnitSystem) { return u === "imperial" ? `${(j * 0.737562).toFixed(0)} ft·lb` : `${j.toFixed(0)} J`; }
export function fmtAng(mrad: number, a: Angular, d = 2, signed = false) {
  const v = toAngular(mrad, a);
  return `${signed && v > 0 ? "+" : ""}${v.toFixed(d)} ${a}`;
}
