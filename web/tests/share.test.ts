import { describe, it, expect, vi } from "vitest";
vi.mock("../src/lib/store.svelte", () => ({}));
import { encodeShare, decodeShare, sanitize } from "../src/lib/share";

const rifle = { id: "r1", name: "Tikka T1x", chambering: ".22 LR", zeroRangeM: 50, sightHeightMm: 38, twistRateIn: 16, twistDirection: "right" as const,
  zeroTempC: null, zeroPressureMbar: null, zeroHumidityPct: null, zeroOffsetVCm: 0, zeroOffsetHCm: 0 };
const ammo = { id: "a1", name: "Fiocchi F320 40 gr", cartridge: ".22 LR", dragModel: "G1" as const, bc: 0.125, bcSegments: null,
  massGrains: 40, diameterIn: 0.223, lengthIn: 0.45, muzzleVelocityMps: 320, mvTempC: 15, tempSensitivity: 0.1 };

describe("share links", () => {
  it("round-trips a rifle and load without ids", async () => {
    const url = await encodeShare(rifle, ammo);
    expect(url.startsWith("https://ballistics.ge/#p=")).toBe(true);
    expect(url.length).toBeLessThan(700);
    const back = await decodeShare(url.slice(url.indexOf("#")));
    const { id: _r, ...r } = rifle; const { id: _a, ...a } = ammo;
    expect(back).toEqual({ v: 1, rifle: r, ammo: a });
  });

  it("keeps velocity bands", async () => {
    const withBands = { ...ammo, bcSegments: [[1200, 0.13], [0, 0.12]] as Array<[number, number]> };
    const back = await decodeShare((await encodeShare(rifle, withBands)).split("https://ballistics.ge/")[1]);
    expect(back?.ammo.bcSegments).toEqual([[1200, 0.13], [0, 0.12]]);
  });

  it("rejects garbage and out-of-range values", async () => {
    expect(await decodeShare("#p=zAAAA")).toBeNull();
    expect(await decodeShare("#q=abc")).toBeNull();
    expect(await decodeShare("#p=j" + "A".repeat(5000))).toBeNull();
    const { id: _r, ...r } = rifle; const { id: _a, ...a } = ammo;
    expect(sanitize({ v: 1, rifle: r, ammo: { ...a, muzzleVelocityMps: 1e9 } })).toBeNull();
    expect(sanitize({ v: 1, rifle: { ...r, twistDirection: "up" }, ammo: a })).toBeNull();
    expect(sanitize({ v: 2, rifle: r, ammo: a })).toBeNull();
  });

  it("drops unknown keys and cleans names", () => {
    const { id: _r, ...r } = rifle; const { id: _a, ...a } = ammo;
    const out = sanitize({ v: 1, rifle: { ...r, name: "  <b>x</b>\u0007" + "y".repeat(100), evil: 1 }, ammo: a });
    expect(out?.rifle).not.toHaveProperty("evil");
    expect(out?.rifle.name.length).toBe(60);
    expect(out?.rifle.name.includes("\u0007")).toBe(false);
  });
});
