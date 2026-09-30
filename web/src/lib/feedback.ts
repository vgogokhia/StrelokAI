/** Feedback client: compresses an optional screenshot, POSTs to /api/feedback,
 *  and queues the message in localStorage when offline so it is sent later. */
export type FeedbackPayload = { kind: string; message: string; contact: string; meta: Record<string, unknown>; screenshot?: string | null };
const QUEUE_KEY = "bge_feedback_queue";

export async function compressImage(file: File, maxPx = 1280, quality = 0.8): Promise<string> {
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, maxPx / Math.max(bmp.width, bmp.height));
  const c = document.createElement("canvas");
  c.width = Math.round(bmp.width * scale); c.height = Math.round(bmp.height * scale);
  c.getContext("2d")!.drawImage(bmp, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", quality);
}

async function post(payload: FeedbackPayload) {
  const r = await fetch("/api/feedback", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
  if (r.ok) return { ok: true as const };
  const j = await r.json().catch(() => ({}));
  return { ok: false as const, error: (j as { error?: string }).error || `HTTP ${r.status}` };
}

export async function sendFeedback(payload: FeedbackPayload): Promise<{ ok: true; queued?: boolean } | { ok: false; error: string }> {
  if (typeof navigator !== "undefined" && navigator.onLine === false) { enqueue(payload); return { ok: true, queued: true }; }
  try { return await post(payload); }
  catch { enqueue(payload); return { ok: true, queued: true }; }
}

function readQueue(): FeedbackPayload[] {
  try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || "[]"); } catch { return []; }
}
function enqueue(p: FeedbackPayload) {
  const q = readQueue(); q.push(p);
  try { localStorage.setItem(QUEUE_KEY, JSON.stringify(q.slice(-10))); } catch { /* storage full — drop */ }
}
export function queuedCount() { return readQueue().length; }

/** Try to deliver queued messages. Stops at the first network failure; rate-limited ones wait for the next flush. */
export async function flushFeedbackQueue() {
  const q = readQueue();
  if (!q.length) return;
  const rest: FeedbackPayload[] = [];
  for (let i = 0; i < q.length; i++) {
    try {
      const r = await post(q[i]);
      if (!r.ok && r.error === "wait_a_minute") { rest.push(...q.slice(i)); break; }
    } catch { rest.push(...q.slice(i)); break; }
  }
  try { rest.length ? localStorage.setItem(QUEUE_KEY, JSON.stringify(rest)) : localStorage.removeItem(QUEUE_KEY); } catch { /* ignore */ }
}

let installed = false;
export function installFeedbackFlusher() {
  if (installed || typeof window === "undefined") return;
  installed = true;
  window.addEventListener("online", () => void flushFeedbackQueue());
  setTimeout(() => void flushFeedbackQueue(), 3000);
}
