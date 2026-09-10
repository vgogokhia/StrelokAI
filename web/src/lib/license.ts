/**
 * License token skeleton.
 *
 * The server (later) issues a compact token `base64url(payload).base64url(sig)`
 * signed with Ed25519; the app verifies it offline with the embedded public
 * key. Payload: { sub, plan: "free"|"pro", exp: unixSeconds, grace: days }.
 * While EVERYTHING_FREE is true every feature is enabled regardless of token,
 * so switching to paid later is a server-side change plus flipping this flag.
 */
export const EVERYTHING_FREE = true;

/** Replace with the real Ed25519 public key (raw 32 bytes, base64url) when issuing tokens. */
const PUBLIC_KEY_B64URL = "";

export type Plan = "free" | "pro";
export interface License { sub: string; plan: Plan; exp: number; grace: number }

export const PRO_FEATURES = ["library", "cloud_sync", "truing", "photo_ai", "reticles", "unlimited_profiles"] as const;
export type Feature = (typeof PRO_FEATURES)[number];

const KEY = "bge_license";

function b64urlToBytes(s: string): Uint8Array<ArrayBuffer> {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad);
  const out = new Uint8Array(new ArrayBuffer(bin.length));
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export async function verifyToken(token: string): Promise<License | null> {
  try {
    const [p, s] = token.split(".");
    if (!p || !s || !PUBLIC_KEY_B64URL) return null;
    const key = await crypto.subtle.importKey("raw", b64urlToBytes(PUBLIC_KEY_B64URL), { name: "Ed25519" }, false, ["verify"]);
    const msg = new TextEncoder().encode(p);
    const ok = await crypto.subtle.verify({ name: "Ed25519" }, key, b64urlToBytes(s), msg.buffer.slice(msg.byteOffset, msg.byteOffset + msg.byteLength) as ArrayBuffer);
    if (!ok) return null;
    const lic = JSON.parse(new TextDecoder().decode(b64urlToBytes(p))) as License;
    return lic;
  } catch {
    return null;
  }
}

export function storedLicense(): License | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as License) : null;
  } catch {
    return null;
  }
}

export function storeLicense(lic: License | null) {
  try {
    if (lic) localStorage.setItem(KEY, JSON.stringify(lic));
    else localStorage.removeItem(KEY);
  } catch { /* ignore */ }
}

/** Is the plan active, including the offline grace window after expiry? */
export function isActive(lic: License | null, now = Date.now() / 1000): boolean {
  if (!lic) return false;
  return now <= lic.exp + (lic.grace ?? 0) * 86400;
}

export function hasFeature(_f: Feature, lic: License | null = storedLicense()): boolean {
  if (EVERYTHING_FREE) return true;
  return lic?.plan === "pro" && isActive(lic);
}
