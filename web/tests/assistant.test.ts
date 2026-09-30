import { describe, it, expect, beforeEach, vi } from "vitest";
const mem = new Map<string, string>();
vi.stubGlobal("localStorage", { getItem: (k: string) => mem.get(k) ?? null, setItem: (k: string, v: string) => mem.set(k, v), removeItem: (k: string) => mem.delete(k) });
vi.stubGlobal("confirm", () => true);
const { store } = await import("../src/lib/store.svelte");
const { runTool, previewTool, takeUndo, applyUndo, snapshotState } = await import("../src/lib/assistant");
const { dropMrad } = await import("../src/core");

describe("assistant tools", () => {
  beforeEach(() => { store.rifle.zeroOffsetVCm = 0; store.rifle.zeroOffsetHCm = 0; store.settings.angular = "MRAD"; store.setRange(500); });
  it("trues MV so the prediction matches a low impact, and undo restores it", async () => {
    const u = takeUndo(); const mv0 = store.ammoSel.muzzleVelocityMps;
    const before = -dropMrad(store.target()!);
    const out = JSON.parse(await runTool("true_from_impact", { range_m: 500, impact_vertical_cm: -15 }));
    expect(out.ok).toBe(true);
    expect(store.ammoSel.muzzleVelocityMps).toBeLessThan(mv0);           // hit low → slower than assumed
    const after = -dropMrad(store.target()!);
    expect(after - before).toBeCloseTo(0.3, 1);                          // 15 cm at 500 m = 0.3 mrad more elevation
    applyUndo(u); expect(store.ammoSel.muzzleVelocityMps).toBe(mv0);
  });
  it("sets conditions with clamping and reports changes", async () => {
    const out = JSON.parse(await runTool("set_conditions", { wind_speed_mps: 4, wind_from_deg: 450, target_range_m: 99999 }));
    expect(store.cond.windSpeedMps).toBe(4); expect(store.cond.windDirDeg).toBe(90); expect(store.cond.targetRangeM).toBe(3000);
    expect(out.changed.length).toBe(3);
  });
  it("adds zero offset and switches settings", async () => {
    const v0 = store.rifle.zeroOffsetVCm;
    await runTool("set_zero_offset", { vertical_cm: 2, horizontal_cm: -1 });
    expect(store.rifle.zeroOffsetVCm).toBe(v0 + 2);
    await runTool("set_settings", { angular: "MOA", click: "1/4 MOA" });
    expect(store.settings.angular).toBe("MOA");
    expect(JSON.parse(snapshotState()).settings.angular).toBe("MOA");
  });
  it("finds a 175 gr .308 bullet, previews creating the load without changing anything, then creates it", async () => {
    const found = JSON.parse(await runTool("search_library", { query: "fiocchi hpbt 175", caliber: ".308", grains: 175 })).results;
    expect(found.length).toBeGreaterThan(0);
    expect(found[0].grains).toBe(175);
    const n = store.ammo.length, sel = store.ammoId;
    const pv = await previewTool("create_ammo", { library_id: found[0].library_id, name: "Fiocchi 175 HPBT", muzzle_velocity_mps: 790 });
    expect(pv.changed[0]).toContain("Fiocchi 175 HPBT");
    expect(store.ammo.length).toBe(n); expect(store.ammoId).toBe(sel);          // preview reverted
    await runTool("create_ammo", { library_id: found[0].library_id, name: "Fiocchi 175 HPBT", muzzle_velocity_mps: 790 });
    expect(store.ammo.length).toBe(n + 1); expect(store.ammoSel.name).toBe("Fiocchi 175 HPBT"); expect(store.ammoSel.muzzleVelocityMps).toBe(790);
    expect(store.ammoSel.massGrains).toBe(175);
  });
  it("creates a rifle with a fuzzy chambering and edits it", async () => {
    const out = JSON.parse(await runTool("create_rifle", { name: "AR-10", chambering: "308", twist_in: 11.25, sight_height_mm: 60 }));
    expect(out.ok).toBe(true); expect(store.rifle.name).toBe("AR-10"); expect(store.rifle.chambering).toBe(".308 Win / 7.62");
    await runTool("update_rifle", { zero_range_m: 200 }); expect(store.rifle.zeroRangeM).toBe(200);
  });
});
