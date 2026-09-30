/**
 * Share a rifle + load as a link: https://ballistics.ge/#p=<data>.
 * The data sits in the URL fragment, so it never reaches the server. It is JSON, deflated when the
 * browser supports CompressionStream ("z" prefix) or plain ("j" prefix), then base64url-encoded.
 * Everything decoded from a link is untrusted: sanitize() rebuilds the profiles field by field.
 */
import type { AmmoProfile, RifleProfile } from "./store.svelte";

export type SharedRifle = Omit<RifleProfile, "id">;
export type SharedAmmo = Omit<AmmoProfile, "id">;
export interface SharedLoad { v: 1; rifle: SharedRifle; ammo: SharedAmmo }

const SITE = "https://ballistics.ge/";
const MAX_LEN = 4000;

const b64url = (bytes: Uint8Array) => btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64url = (s: string) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));

async function pipe(bytes: Uint8Array, stream: CompressionStream | DecompressionStream): Promise<Uint8Array> {
  const out = new Blob([bytes as BlobPart]).stream().pipeThrough(stream);
  return new Uint8Array(await new Response(out).arrayBuffer());
}

export async function encodeShare(rifle: RifleProfile, ammo: AmmoProfile): Promise<string> {
  const { id: _r, ...r } = rifle;
  const { id: _a, ...a } = ammo;
  const json = new TextEncoder().encode(JSON.stringify({ v: 1, rifle: r, ammo: a } satisfies SharedLoad));
  let data = "j" + b64url(json);
  if (typeof CompressionStream !== "undefined") {
    try { data = "z" + b64url(await pipe(json, new CompressionStream("deflate-raw"))); } catch { /* keep plain */ }
  }
  return `${SITE}#p=${data}`;
}

/** Reads a shared load from a location hash like "#p=...". Returns null if absent or invalid. */
export async function decodeShare(hash: string): Promise<SharedLoad | null> {
  const m = /^#p=([jz])([A-Za-z0-9_-]+)$/.exec(hash);
  if (!m || m[2].length > MAX_LEN) return null;
  try {
    let bytes: Uint8Array = unb64url(m[2]);
    if (m[1] === "z") {
      if (typeof DecompressionStream === "undefined") return null;
      bytes = await pipe(bytes, new DecompressionStream("deflate-raw"));
    }
    if (bytes.length > 20000) return null;
    return sanitize(JSON.parse(new TextDecoder().decode(bytes)));
  } catch {
    return null;
  }
}

const num = (v: unknown, lo: number, hi: number): number | undefined =>
  typeof v === "number" && Number.isFinite(v) && v >= lo && v <= hi ? v : undefined;
const optNum = (v: unknown, lo: number, hi: number): number | null | undefined => (v === null ? null : num(v, lo, hi));
const str = (v: unknown, max = 60): string | undefined =>
  typeof v === "string" && v.trim() ? v.replace(/[\u0000-\u001f\u007f]/g, "").trim().slice(0, max) : undefined;

/** Rebuilds a shared load from untrusted JSON. Every field is type- and range-checked; unknown keys are dropped. */
export function sanitize(x: unknown): SharedLoad | null {
  if (!x || typeof x !== "object") return null;
  const { v, rifle: r, ammo: a } = x as Record<string, any>;
  if (v !== 1 || !r || !a || typeof r !== "object" || typeof a !== "object") return null;
  const rifle = {
    name: str(r.name), chambering: str(r.chambering, 40),
    zeroRangeM: num(r.zeroRangeM, 5, 1000), sightHeightMm: num(r.sightHeightMm, 0, 200),
    twistRateIn: num(r.twistRateIn, 3, 40), twistDirection: r.twistDirection === "left" ? "left" : r.twistDirection === "right" ? "right" : undefined,
    zeroTempC: optNum(r.zeroTempC, -50, 60), zeroPressureMbar: optNum(r.zeroPressureMbar, 500, 1100), zeroHumidityPct: optNum(r.zeroHumidityPct, 0, 100),
    zeroOffsetVCm: num(r.zeroOffsetVCm, -100, 100), zeroOffsetHCm: num(r.zeroOffsetHCm, -100, 100),
  };
  const segs = a.bcSegments === null ? null
    : Array.isArray(a.bcSegments) && a.bcSegments.length >= 1 && a.bcSegments.length <= 12 &&
      a.bcSegments.every((s: unknown) => Array.isArray(s) && s.length === 2 && num(s[0], 0, 10000) !== undefined && num(s[1], 0.01, 2) !== undefined)
      ? (a.bcSegments as Array<[number, number]>).map(([s, b]) => [s, b] as [number, number]) : undefined;
  const ammo = {
    name: str(a.name), cartridge: str(a.cartridge, 40),
    dragModel: a.dragModel === "G1" || a.dragModel === "G7" ? a.dragModel : undefined,
    bc: num(a.bc, 0.01, 2), bcSegments: segs,
    massGrains: num(a.massGrains, 5, 1500), diameterIn: num(a.diameterIn, 0.1, 1), lengthIn: num(a.lengthIn, 0.1, 5),
    muzzleVelocityMps: num(a.muzzleVelocityMps, 50, 2000), mvTempC: num(a.mvTempC, -50, 60), tempSensitivity: num(a.tempSensitivity, 0, 10),
  };
  if (Object.values(rifle).some((f) => f === undefined) || Object.values(ammo).some((f) => f === undefined)) return null;
  return { v: 1, rifle: rifle as SharedRifle, ammo: ammo as SharedAmmo };
}
