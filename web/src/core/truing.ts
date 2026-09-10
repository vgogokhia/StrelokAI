/**
 * MV and BC truing (port of ballistics/truing.py): secant search that
 * makes the predicted drop match an observed come-up.
 */
import { atRange, calculateSolution, dropMrad, type CalcInputs } from "./solver";

export interface TruingResult {
  value: number; // trued MV (m/s) or BC
  iterations: number;
  residualMrad: number;
  converged: boolean;
}

function dropFor(inputs: CalcInputs, rangeM: number): number {
  const sol = calculateSolution({ ...inputs, targetRangeM: rangeM, windSpeedMps: 0 });
  const pt = atRange(sol, rangeM);
  if (!pt) throw new Error("No trajectory point at observed range");
  return dropMrad(pt);
}

function secant(
  f: (x: number) => number,
  target: number,
  x0: number,
  lo: number,
  hi: number,
  clampLo: number,
  clampHi: number,
  tol: number,
  maxIter: number,
): TruingResult {
  let a = lo;
  let b = hi;
  let fa = f(a);
  let fb = f(b);
  let iterations = 2;
  let x = x0;
  let residual = 0;
  let converged = false;
  for (let k = 0; k < maxIter; k++) {
    if (Math.abs(fb - fa) < 1e-9) {
      x = (a + b) / 2;
      break;
    }
    const slope = (fb - fa) / (b - a);
    x = b + (target - fb) / slope;
    x = Math.max(clampLo, Math.min(x, clampHi));
    const fx = f(x);
    iterations++;
    residual = fx - target;
    if (Math.abs(residual) < tol) {
      converged = true;
      break;
    }
    a = b;
    fa = fb;
    b = x;
    fb = fx;
  }
  return { value: x, iterations, residualMrad: residual, converged };
}

/** True the muzzle velocity from an observed drop (mid range, 400–600 m). */
export function trueMuzzleVelocity(
  inputs: CalcInputs,
  observedDropMrad: number,
  observedRangeM: number,
  tol = 0.01,
  maxIter = 20,
): TruingResult {
  const mv0 = inputs.muzzleVelocityMps;
  return secant(
    (mv) => dropFor({ ...inputs, muzzleVelocityMps: mv }, observedRangeM),
    observedDropMrad,
    mv0,
    mv0 * 0.97,
    mv0 * 1.03,
    mv0 * 0.9,
    mv0 * 1.1,
    tol,
    maxIter,
  );
}

/** True the BC from an observed drop at long range (MV assumed already true). */
export function trueBallisticCoefficient(
  inputs: CalcInputs,
  observedDropMrad: number,
  observedRangeM: number,
  tol = 0.01,
  maxIter = 25,
): TruingResult {
  const useG7 = !!inputs.bcG7 && inputs.dragModel !== "G1";
  const bc0 = useG7 ? (inputs.bcG7 as number) : (inputs.bcG1 ?? inputs.bcG7 ?? 0.3);
  const withBc = (bc: number): CalcInputs =>
    useG7 ? { ...inputs, bcG7: bc, bcSegments: null } : { ...inputs, bcG1: bc, bcG7: null, bcSegments: null };
  return secant(
    (bc) => dropFor(withBc(bc), observedRangeM),
    observedDropMrad,
    bc0,
    bc0 * 0.9,
    bc0 * 1.1,
    bc0 * 0.5,
    bc0 * 2.0,
    tol,
    maxIter,
  );
}
