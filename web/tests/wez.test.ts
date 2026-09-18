import { describe, it, expect } from "vitest";
import { calculateSolution } from "../src/core/solver";
import { hitProbability, perturb, DEFAULT_WEZ } from "../src/core/wez";
describe("wez", () => {
  const inp = { muzzleVelocityMps: 792, bcG7: 0.243, dragModel: "G7" as const, massGrains: 175, diameterIn: 0.308, bulletLengthIn: 1.24, twistRateIn: 11.25, zeroRangeM: 100, targetRangeM: 1200, windSpeedMps: 3, windDirectionDeg: 90, sightHeightMm: 40 };
  const p = perturb(inp, 10, 1);
  const sols = { base: calculateSolution(inp), mv: calculateSolution(p.mv), wind: calculateSolution(p.wind) };
  it("is high close and falls with range", () => {
    const r100 = hitProbability(100, sols, 10, 1, DEFAULT_WEZ)!, r500 = hitProbability(500, sols, 10, 1, DEFAULT_WEZ)!, r900 = hitProbability(900, sols, 10, 1, DEFAULT_WEZ)!;
    expect(r100.p).toBeGreaterThan(0.99); expect(r500.p).toBeLessThan(r100.p); expect(r900.p).toBeLessThan(r500.p); expect(r900.p).toBeLessThan(0.6);
  });
  it("bigger target and tighter group raise probability", () => {
    const a = hitProbability(500, sols, 10, 1, DEFAULT_WEZ)!.p;
    expect(hitProbability(500, sols, 10, 1, { ...DEFAULT_WEZ, targetWm: 0.45, targetHm: 0.6, shape: "rect" })!.p).toBeGreaterThan(a);
    expect(hitProbability(500, sols, 10, 1, { ...DEFAULT_WEZ, groupMoa: 0.5, mvSdMps: 3, windSdMps: 0.5 })!.p).toBeGreaterThan(a);
  });
});
