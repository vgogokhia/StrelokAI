<script lang="ts">
  import { t } from "../lib/i18n.svelte";
  import { store } from "../lib/store.svelte";
  import { compressImage, sendFeedback } from "../lib/feedback";

  let { onsent = undefined as (() => void) | undefined, page = "" } = $props();
  const s = $derived(store.settings);
  const version = __APP_VERSION__;
  const KINDS = ["🐞 Bug", "✨ Feature request", "💬 Other"]; // stored in English; shown translated

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
    catch { note = { kind: "err", text: t("Could not read the image.") }; }
  }
  function clearShot() { shot = null; if (fileEl) fileEl.value = ""; }

  async function submit() {
    if (msg.trim().length < 5) { note = { kind: "warn", text: t("Please describe it in a few words.") }; return; }
    busy = true; note = null;
    const r = await sendFeedback({ kind, message: msg, contact, screenshot: shot,
      meta: { version, page, units: s.units, angular: s.angular, rifle: `${store.rifle.name} (${store.rifle.chambering})`, ammo: store.ammoSel.name,
        range: store.cond.targetRangeM, screen: `${screen.width}x${screen.height}`, standalone: matchMedia("(display-mode: standalone)").matches, lang: navigator.language } });
    busy = false;
    if (r.ok) {
      note = { kind: "ok", text: r.queued ? t("You're offline — saved, will send when you're back online.") : t("Thanks, received!") };
      msg = ""; contact = ""; clearShot();
      if (onsent) setTimeout(onsent, 1200);
    } else {
      note = { kind: "err", text: r.error === "wait_a_minute" ? t("Please wait a minute before sending again.") : `${t("Could not send:")} ${r.error}` };
    }
  }
</script>

<div class="muted" style="margin-bottom:8px">{t("Found a bug or want a feature? Describe it and attach a screenshot if it helps.")}</div>
<div class="seg" style="margin-bottom:8px">
  {#each KINDS as k}<button class:on={kind === k} onclick={() => (kind = k)}>{t(k)}</button>{/each}
</div>
<textarea aria-label={t("Message")} bind:value={msg} rows="4" maxlength="4000"
  placeholder={kind.includes("Bug") ? t("What happened, what you expected, which load/range…") : kind.includes("Feature") ? t("What should the app do, and why would it help you?") : t("Write here…")}
  style="width:100%;background:var(--panel2);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:10px;font:inherit"></textarea>
<div class="grid2" style="margin-top:8px">
  <div><label class="f" for="fb-contact">{t("Contact (optional)")}</label><input id="fb-contact" type="text" bind:value={contact} placeholder={t("email / Facebook / phone")} /></div>
  <div><span class="f">{t("Screenshot")}</span>
    <button type="button" style="width:100%" onclick={() => fileEl?.click()}>📷 {shot ? t("Change") : t("Attach")}</button>
    <input bind:this={fileEl} aria-label={t("Screenshot")} type="file" accept="image/*" onchange={pickShot} style="display:none" />
  </div>
</div>
{#if shot}
  <div class="row" style="margin-top:8px;align-items:center;gap:8px">
    <img src={shot} alt="screenshot" style="max-height:120px;max-width:60%;border-radius:8px;border:1px solid var(--border)" />
    <button type="button" onclick={clearShot}>✕ {t("Remove")}</button>
  </div>
{/if}
<button class="primary" style="width:100%;margin-top:8px" disabled={busy} onclick={submit}>{busy ? t("Sending…") : `📨 ${t("Send")}`}</button>
{#if note}<div class="note {note.kind}">{note.text}</div>{/if}
