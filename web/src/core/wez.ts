/** Hit probability ("weapon employment zone"): combines dispersion, muzzle-velocity spread, wind-call error and
 *  range error into a bivariate normal error at the target and integrates it over the target outline.
 *  Sensitivities come from three solves (base, MV+, wind+) so it is cheap enough to run live. */
import { atRange, type BallisticSolution } from "./solver";
import type { CalcInputs } from "./solver";

export interface WezConfig {
  groupMoa: number;      // shooter+rifle+ammo dispersion, extreme spread of a 5-shot group at 100 (MOA)
  mvSdMps: number;       // muzzle velocity standard deviation
  windSdMps: number;     // wind-call uncertainty (1σ, m/s)
  rangeSdPct: number;    // range uncertainty (1σ, % of range) — 0 for a laser rangefinder
  targetWm: number;      // target width (m)
  targetHm: number;      // target height (m)
  shape: "rect" | "ellipse";
}
export const DEFAULT_WEZ: WezConfig = { groupMoa: 1, mvSdMps: 8, windSdMps: 1, rangeSdPct: 0, targetWm: 0.2, targetHm: 0.2, shape: "ellipse" };
export const TARGET_PRESETS: { name: string; w: number; h: number; shape: "rect" | "ellipse" }[] = [
  { name: "Deer vitals", w: 0.2, h: 0.2, shape: "ellipse" }, { name: "Boar vitals", w: 0.15, h: 0.15, shape: "ellipse" },
  { name: "Steel 30 cm", w: 0.3, h: 0.3, shape: "ellipse" }, { name: "IPSC A-zone", w: 0.15, h: 0.28, shape: "rect" },
  { name: "Torso", w: 0.45, h: 0.6, shape: "rect" }, { name: "Chamois", w: 0.12, h: 0.12, shape: "ellipse" },
];

const MOA_TO_MRAD = 1 / 3.43775;
const erf = (x: number) => { const s = Math.sign(x); x = Math.abs(x); const t = 1 / (1 + 0.3275911 * x); const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x); return s * y; };
const Phi = (x: number) => 0.5 * (1 + erf(x / Math.SQRT2));

export interface WezResult { p: number; sigmaV: number; sigmaH: number; parts: { disp: number; mv: number; wind: number; range: number } }

/** Error budget at one range. sols: base, with MV + dMv, with wind + dWind (all solved to at least rangeM). */
export function hitProbability(rangeM: number, sols: { base: BallisticSolution; mv: BallisticSolution; wind: BallisticSolution }, dMv: number, dWind: number, cfg: WezConfig): WezResult | null {
  const b = atRange(sols.base, rangeM), m = atRange(sols.mv, rangeM), w = atRange(sols.wind, rangeM);
  const b2 = atRange(sols.base, Math.max(1, rangeM * 0.98));
  if (!b || !m || !w || !b2) return null;
  // 1σ of a 5-shot extreme spread ≈ ES/3 (radius from centre); as an angle it scales with range.
  const disp = ((cfg.groupMoa * MOA_TO_MRAD) / 3 / 1000) * rangeM;
  const mvErr = Math.abs((m.dropM - b.dropM) / dMv) * cfg.mvSdMps;
  const windErr = Math.abs((w.windageM - b.windageM) / dWind) * cfg.windSdMps;
  // range error → vertical miss through the trajectory slope (drop change per metre of range)
  const slope = (b.dropM - b2.dropM) / (rangeM * 0.02);
  const rangeErr = Math.abs(slope) * (cfg.rangeSdPct / 100) * rangeM;
  const sigmaV = Math.hypot(disp, mvErr, rangeErr), sigmaH = Math.hypot(disp, windErr);
  let p: number;
  if (cfg.shape === "rect") p = (2 * Phi(cfg.targetWm / 2 / sigmaH) - 1) * (2 * Phi(cfg.targetHm / 2 / sigmaV) - 1);
  else { // ellipse: numeric integration of the bivariate normal over the ellipse
    const a = cfg.targetWm / 2, c = cfg.targetHm / 2; const N = 60; let acc = 0;
    for (let i = 0; i < N; i++) { const x = -a + (a * 2 * (i + 0.5)) / N; const yh = c * Math.sqrt(Math.max(0, 1 - (x * x) / (a * a)));
      const px = Math.exp(-(x * x) / (2 * sigmaH * sigmaH)) / (sigmaH * Math.sqrt(2 * Math.PI)); acc += px * (2 * Phi(yh / sigmaV) - 1) * ((a * 2) / N); }
    p = acc;
  }
  return { p: Math.min(1, Math.max(0, p)), sigmaV, sigmaH, parts: { disp, mv: mvErr, wind: windErr, range: rangeErr } };
}

/** Inputs for the two perturbed solves. */
export function perturb(inp: CalcInputs, dMv: number, dWind: number): { mv: CalcInputs; wind: CalcInputs } {
  return { mv: { ...inp, muzzleVelocityMps: inp.muzzleVelocityMps + dMv }, wind: { ...inp, windSpeedMps: (inp.windSpeedMps ?? 0) + dWind, windDirectionDeg: inp.windSpeedMps ? inp.windDirectionDeg : 90 } };
}
