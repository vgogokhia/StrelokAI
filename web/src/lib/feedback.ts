/** Feedback client: compresses an optional screenshot and POSTs to /api/feedback. */
export async function compressImage(file: File, maxPx = 1280, quality = 0.8): Promise<string> {
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, maxPx / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale);
  c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", quality);
}

export async function sendFeedback(payload: {
  kind: string; message: string; contact: string; meta: Record<string, unknown>; screenshot?: string | null;
}): Promise<{ ok: boolean; error?: string }> {
  try {
    const r = await fetch("/api/feedback", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
    if (r.ok) return { ok: true };
    const j = await r.json().catch(() => ({}));
    return { ok: false, error: j.error || `HTTP ${r.status}` };
  } catch {
    return { ok: false, error: "offline" };
  }
}
