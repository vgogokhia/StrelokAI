/**
 * Dope-card builder (port of ballistics/dope_card.py): one long solve,
 * sampled at the requested ranges.
 */
import { atRange, calculateSolution, dropMrad, windageMrad, MRAD_TO_MOA, type CalcInputs } from "./solver";

export interface DopeRow {
  rangeM: number;
  dropMrad: number;
  dropMoa: number;
  windMrad: number; // full-value crosswind at the reference speed (magnitude)
  windHalfMrad: number;
  velocityMps: number;
  mach: number;
  energyJ: number;
  tofS: number;
}

export function buildDopeTable(
  inputs: CalcInputs,
  rangesM: number[],
  windReferenceMps = 4.47,
): DopeRow[] {
  const maxR = Math.max(...rangesM);
  const sol = calculateSolution({
    ...inputs,
    targetRangeM: maxR + 1,
    windSpeedMps: windReferenceMps,
    windDirectionDeg: 270, // full value from 9 o'clock
  });
  const rows: DopeRow[] = [];
  for (const r of rangesM) {
    const pt = atRange(sol, r);
    if (!pt) continue;
    const w = Math.abs(windageMrad(pt));
    rows.push({
      rangeM: r,
      dropMrad: dropMrad(pt),
      dropMoa: dropMrad(pt) * MRAD_TO_MOA,
      windMrad: w,
      windHalfMrad: w / 2,
      velocityMps: pt.velocityMps,
      mach: pt.mach,
      energyJ: pt.energyJ,
      tofS: pt.timeS,
    });
  }
  return rows;
}

export function rowsToCsv(rows: DopeRow[]): string {
  const head = "Range_m,Drop_MRAD,Drop_MOA,Wind_MRAD,WindHalf_MRAD,Velocity_mps,Mach,Energy_J,TOF_s\n";
  return (
    head +
    rows
      .map(
        (r) =>
          `${r.rangeM},${r.dropMrad.toFixed(3)},${r.dropMoa.toFixed(2)},${r.windMrad.toFixed(3)},` +
          `${r.windHalfMrad.toFixed(3)},${r.velocityMps.toFixed(1)},${r.mach.toFixed(3)},${r.energyJ.toFixed(0)},${r.tofS.toFixed(3)}\n`,
      )
      .join("")
  );
}
