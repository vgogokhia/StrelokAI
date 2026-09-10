/** Bullet / factory-ammo library (bundled JSON, synced from data/bullet_library.json). */
import raw from "../data/bullets.json";

export interface BulletPreset {
  id: string;
  manufacturer: string;
  caliber: string;
  bullet: string;
  massGrains: number;
  diameterIn: number;
  lengthIn: number;
  bcG7: number | null;
  bcG1: number | null;
  defaultMvMps: number;
  defaultTwistIn: number;
  type: "bullet" | "ammo";
}

type RawEntry = {
  id: string; manufacturer: string; caliber: string; bullet: string; mass_grains: number;
  diameter_in: number; length_in: number; bc_g7: number | null; bc_g1: number | null;
  default_mv_mps: number; default_twist_in: number; type?: string;
};

export const LIBRARY: BulletPreset[] = ((raw as { bullets: RawEntry[] }).bullets)
  .filter((b) => b.bc_g7 != null || b.bc_g1 != null)
  .map((b) => ({
    id: b.id, manufacturer: b.manufacturer, caliber: b.caliber, bullet: b.bullet,
    massGrains: b.mass_grains, diameterIn: b.diameter_in, lengthIn: b.length_in,
    bcG7: b.bc_g7 ?? null, bcG1: b.bc_g1 ?? null, defaultMvMps: b.default_mv_mps,
    defaultTwistIn: b.default_twist_in, type: (b.type === "ammo" ? "ammo" : "bullet") as "ammo" | "bullet",
  }))
  .sort((a, b) => a.caliber.localeCompare(b.caliber) || a.manufacturer.localeCompare(b.manufacturer) || a.massGrains - b.massGrains);

export const label = (b: BulletPreset) => `${b.caliber} | ${b.manufacturer} ${b.bullet}`;
export const CALIBERS = [...new Set(LIBRARY.map((b) => b.caliber))];
