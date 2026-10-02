<script lang="ts">
  /** "Share this rifle and load": link in the URL fragment, QR code, native share sheet, copy. */
  import { store } from "../lib/store.svelte";
  import { encodeShare } from "../lib/share";
  import { t } from "../lib/i18n.svelte";

  let open = $state(false);
  let url = $state("");
  let svg = $state("");
  let note = $state("");
  const canShare = typeof navigator !== "undefined" && typeof navigator.share === "function";

  async function show() {
    url = await encodeShare($state.snapshot(store.rifle), $state.snapshot(store.ammoSel));
    const { default: qrcode } = await import("qrcode-generator"); // loaded only when someone shares
    const q = qrcode(0, "L");
    q.addData(url);
    q.make();
    svg = q.createSvgTag({ cellSize: 4, margin: 2, scalable: true });
    note = "";
    open = true;
  }
  async function nativeShare() {
    try { await navigator.share({ title: `${store.rifle.name} · ${store.ammoSel.name}`, text: t("My rifle and load for the ballistics.ge calculator"), url }); }
    catch { /* cancelled */ }
  }
  async function copy() {
    try { await navigator.clipboard.writeText(url); note = t("Link copied."); }
    catch { note = t("Select the link above and copy it."); }
  }
</script>

<button style="width:100%;margin-top:8px" onclick={show}>🔗 {t("Share this rifle and load")}</button>

{#if open}
  <div class="modal-bg" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) open = false; }}>
    <div class="modal" role="dialog" aria-modal="true" aria-label={t("Share")}>
      <div class="row" style="justify-content:space-between;align-items:center;margin-bottom:8px">
        <h2 style="margin:0">🔗 {t("Share")}</h2>
        <button type="button" aria-label={t("Close")} onclick={() => (open = false)}>✕</button>
      </div>
      <p class="muted" style="margin-top:0">{store.rifle.name} · {store.ammoSel.name}. {t("Anyone who opens the link can add this rifle and load to their calculator. Nothing is uploaded: the data is inside the link.")}</p>
      <div class="qr">{@html svg}</div>
      <p class="muted" style="text-align:center;margin:4px 0 10px">{t("Scan with a phone camera")}</p>
      <input type="text" readonly value={url} onfocus={(e) => (e.target as HTMLInputElement).select()} aria-label={t("Share link")} />
      <div class="row" style="margin-top:8px">
        {#if canShare}<button class="primary" style="flex:1" onclick={nativeShare}>📤 {t("Share…")}</button>{/if}
        <button style="flex:1" onclick={copy}>📋 {t("Copy link")}</button>
      </div>
      {#if note}<div class="note ok">{note}</div>{/if}
    </div>
  </div>
{/if}

<style>
  .qr { background: #fff; border-radius: 12px; padding: 8px; width: min(260px, 70vw); margin: 0 auto; }
  .qr :global(svg) { display: block; width: 100%; height: auto; }
</style>
