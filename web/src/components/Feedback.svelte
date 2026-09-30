<script lang="ts">
  import { store } from "../lib/store.svelte";
  import { compressImage, sendFeedback } from "../lib/feedback";

  let { onsent = undefined as (() => void) | undefined, page = "" } = $props();
  const s = $derived(store.settings);
  const version = __APP_VERSION__;
  const KINDS = ["🐞 Bug", "✨ Feature request", "💬 Other"];

  let kind = $state(KINDS[0]);
  let msg = $state("");
  let contact = $state("");
  let shot = $state<string | null>(null);
  let busy = $state(false);
  let note = $state<{ kind: string; text: string } | null>(null);
  let fileEl = $state<HTMLInputElement | null>(null);

  async function pickShot(e: Event) {
    const f = (e.target as HTMLInputElement).files?.[0];
    if (!f) { shot = null; return; }
    try { shot = await compressImage(f); note = null; }
    catch { note = { kind: "err", text: "Could not read the image." }; }
  }
  function clearShot() { shot = null; if (fileEl) fileEl.value = ""; }

  async function submit() {
    if (msg.trim().length < 5) { note = { kind: "warn", text: "Please describe it in a few words." }; return; }
    busy = true; note = null;
    const r = await sendFeedback({ kind, message: msg, contact, screenshot: shot,
      meta: { version, page, units: s.units, angular: s.angular, rifle: `${store.rifle.name} (${store.rifle.chambering})`, ammo: store.ammoSel.name,
        range: store.cond.targetRangeM, screen: `${screen.width}x${screen.height}`, standalone: matchMedia("(display-mode: standalone)").matches, lang: navigator.language } });
    busy = false;
    if (r.ok) {
      note = { kind: "ok", text: r.queued ? "You're offline — saved, will send when you're back online." : "Thanks, received! / მადლობა, მივიღე." };
      msg = ""; contact = ""; clearShot();
      if (onsent) setTimeout(onsent, 1200);
    } else {
      note = { kind: "err", text: r.error === "wait_a_minute" ? "Please wait a minute before sending again." : `Could not send: ${r.error}` };
    }
  }
</script>

<div class="muted" style="margin-bottom:8px">Found a bug or want a feature? Describe it and attach a screenshot if it helps.</div>
<div class="seg" style="margin-bottom:8px">
  {#each KINDS as k}<button class:on={kind === k} onclick={() => (kind = k)}>{k}</button>{/each}
</div>
<textarea bind:value={msg} rows="4" maxlength="4000"
  placeholder={kind.includes("Bug") ? "What happened, what you expected, which load/range…" : kind.includes("Feature") ? "What should the app do, and why would it help you?" : "Write here…"}
  style="width:100%;background:var(--panel2);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px;font:inherit"></textarea>
<div class="grid2" style="margin-top:8px">
  <div><label class="f">Contact (optional)</label><input type="text" bind:value={contact} placeholder="email / Facebook / phone" /></div>
  <div><label class="f">Screenshot</label>
    <button type="button" style="width:100%" onclick={() => fileEl?.click()}>📷 {shot ? "Change" : "Attach"}</button>
    <input bind:this={fileEl} type="file" accept="image/*" onchange={pickShot} style="display:none" />
  </div>
</div>
{#if shot}
  <div class="row" style="margin-top:8px;align-items:center;gap:8px">
    <img src={shot} alt="screenshot" style="max-height:120px;max-width:60%;border-radius:8px;border:1px solid var(--border)" />
    <button type="button" onclick={clearShot}>✕ Remove</button>
  </div>
{/if}
<button class="primary" style="width:100%;margin-top:8px" disabled={busy} onclick={submit}>{busy ? "Sending…" : "📨 Send"}</button>
{#if note}<div class="note {note.kind}">{note.text}</div>{/if}
