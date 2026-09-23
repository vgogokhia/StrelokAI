import { describe, it, expect, beforeEach, vi } from "vitest";
const mem = new Map<string, string>();
vi.stubGlobal("localStorage", { getItem: (k: string) => mem.get(k) ?? null, setItem: (k: string, v: string) => mem.set(k, v), removeItem: (k: string) => mem.delete(k) });
vi.stubGlobal("confirm", () => true);
const { store } = await import("../src/lib/store.svelte");
const { runTool, takeUndo, applyUndo, snapshotState } = await import("../src/lib/assistant");
const { dropMrad } = await import("../src/core");

describe("assistant tools", () => {
  beforeEach(() => { store.rifle.zeroOffsetVCm = 0; store.rifle.zeroOffsetHCm = 0; store.settings.angular = "MRAD"; store.setRange(500); });
  it("trues MV so the prediction matches a low impact, and undo restores it", () => {
    const u = takeUndo(); const mv0 = store.ammoSel.muzzleVelocityMps;
    const before = -dropMrad(store.target()!);
    const out = JSON.parse(runTool("true_from_impact", { range_m: 500, impact_vertical_cm: -15 }));
    expect(out.ok).toBe(true);
    expect(store.ammoSel.muzzleVelocityMps).toBeLessThan(mv0);           // hit low → slower than assumed
    const after = -dropMrad(store.target()!);
    expect(after - before).toBeCloseTo(0.3, 1);                          // 15 cm at 500 m = 0.3 mrad more elevation
    applyUndo(u); expect(store.ammoSel.muzzleVelocityMps).toBe(mv0);
  });
  it("sets conditions with clamping and reports changes", () => {
    const out = JSON.parse(runTool("set_conditions", { wind_speed_mps: 4, wind_from_deg: 450, target_range_m: 99999 }));
    expect(store.cond.windSpeedMps).toBe(4); expect(store.cond.windDirDeg).toBe(90); expect(store.cond.targetRangeM).toBe(3000);
    expect(out.changed.length).toBe(3);
  });
  it("adds zero offset and switches settings", () => {
    const v0 = store.rifle.zeroOffsetVCm;
    runTool("set_zero_offset", { vertical_cm: 2, horizontal_cm: -1 });
    expect(store.rifle.zeroOffsetVCm).toBe(v0 + 2);
    runTool("set_settings", { angular: "MOA", click: "1/4 MOA" });
    expect(store.settings.angular).toBe("MOA");
    expect(JSON.parse(snapshotState()).settings.angular).toBe("MOA");
  });
});
