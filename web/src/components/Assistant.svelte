<script lang="ts">
  import { snapshotState, runTool, previewTool, takeUndo, applyUndo, READ_ONLY } from "../lib/assistant";
  import { billing } from "../lib/billing.svelte";

  type Block = { type: string; text?: string; id?: string; name?: string; input?: Record<string, unknown>; tool_use_id?: string; content?: string };
  type Msg = { role: "user" | "assistant"; content: string | Block[] };
  type Line = { who: "me" | "ai" | "sys" | "ask"; text: string; undo?: string; items?: string[]; decide?: (ok: boolean) => void; decided?: string };

  let history = $state<Msg[]>([]);
  let lines = $state<Line[]>([]);
  let text = $state("");
  let busy = $state(false);
  let remaining = $state<number | null>(null);
  let listEl = $state<HTMLDivElement | null>(null);
  const EXAMPLES = ["AR-10 მაქვს .308, ტყვია Fiocchi HPBT 175 გრ — დამიმატე", "600 მ-ზე აპის მიხედვით დავაყენე და 15 სმ-ით დაბლა მოხვდა", "ქარი 3 საათიდან, 4 მ/წმ, 450 მეტრი", "ჩემი სკოუპი Vortex Viper PST 5-25, EBR-7C, FFP"];

  $effect(() => { lines.length; queueMicrotask(() => listEl?.scrollTo({ top: listEl.scrollHeight, behavior: "smooth" })); });

  async function call(): Promise<{ content: Block[]; stop_reason: string; remaining?: number }> {
    const r = await fetch("/api/assistant", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ messages: $state.snapshot(history), state: snapshotState() }) });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(r.status === 401 ? "signin" : j.error === "daily_limit" ? "limit" : j.error === "assistant_disabled" ? "disabled" : "net");
    return j;
  }

  async function send(q = text) {
    q = q.trim(); if (!q || busy) return;
    text = ""; busy = true;
    lines.push({ who: "me", text: q });
    history.push({ role: "user", content: q });
    const undo = takeUndo(); let changedAny = false;
    try {
      for (let step = 0; step < 4; step++) {
        const res = await call();
        if (res.remaining != null) remaining = res.remaining;
        history.push({ role: "assistant", content: res.content });
        const say = res.content.filter((b) => b.type === "text").map((b) => b.text).join("\n").trim();
        const uses = res.content.filter((b) => b.type === "tool_use");
        if (!uses.length) { if (say) lines.push({ who: "ai", text: say, undo: changedAny ? undo : undefined }); break; }
        if (say) lines.push({ who: "ai", text: say });
        const results: Block[] = [];
        const pending: { u: Block; changed: string[] }[] = [];
        for (const u of uses) {
          if (READ_ONLY.has(u.name!)) { results.push({ type: "tool_result", tool_use_id: u.id, content: await runTool(u.name!, (u.input ?? {}) as Record<string, unknown>) }); continue; }
          const pv = await previewTool(u.name!, (u.input ?? {}) as Record<string, unknown>);
          if (pv.error || !pv.changed.length) { results.push({ type: "tool_result", tool_use_id: u.id, content: pv.raw }); continue; }
          pending.push({ u, changed: pv.changed });
        }
        if (pending.length) {
          const ok = await new Promise<boolean>((resolve) => lines.push({ who: "ask", text: "Apply these changes?", items: pending.flatMap((p) => p.changed), decide: resolve }));
          for (const p of pending) {
            if (!ok) { results.push({ type: "tool_result", tool_use_id: p.u.id, content: JSON.stringify({ declined: true, note: "The user did not approve this change. Nothing was changed." }) }); continue; }
            const out = await runTool(p.u.name!, (p.u.input ?? {}) as Record<string, unknown>);
            try { if (JSON.parse(out).changed?.length) changedAny = true; } catch { /* ignore */ }
            results.push({ type: "tool_result", tool_use_id: p.u.id, content: out });
          }
        }
        history.push({ role: "user", content: results });
      }
    } catch (e) {
      const m = (e as Error).message;
      lines.push({ who: "sys", text: m === "signin" ? "Sign in with Google (More → My account) to use the assistant." : m === "limit" ? "Daily assistant limit reached — try again tomorrow." : m === "disabled" ? "The assistant is not enabled on this server yet." : "No connection — the assistant needs internet. The calculator itself still works offline." });
      history = history.filter((h) => !(h.role === "user" && h.content === q)); // allow resend
    } finally { busy = false; }
  }
  function undo(l: Line) { if (!l.undo) return; applyUndo(l.undo); lines.push({ who: "sys", text: "↩️ Changes undone." }); l.undo = undefined; }
  function reset() { history = []; lines = []; }
</script>

<div class="muted" style="margin-bottom:8px">Tell me what happened or what to set — I'll change the calculator for you. Every change can be undone.</div>
<div bind:this={listEl} class="chat">
  {#if !lines.length}
    <div class="chips" style="flex-wrap:wrap">{#each EXAMPLES as ex}<button class="ex" onclick={() => send(ex)}>{ex}</button>{/each}</div>
  {/if}
  {#each lines as l}
    {#if l.who === "ask"}
      <div class="msg ask">
        <b>{l.text}</b>
        <ul>{#each l.items ?? [] as it}<li>{it}</li>{/each}</ul>
        {#if l.decided}<div class="muted">{l.decided}</div>
        {:else}<div class="row" style="gap:6px"><button class="primary" style="flex:1" onclick={() => { l.decided = "✅ Applied"; l.decide?.(true); }}>✅ Apply</button><button style="flex:1" onclick={() => { l.decided = "✖ Cancelled"; l.decide?.(false); }}>✖ Cancel</button></div>{/if}
      </div>
    {:else}
      <div class="msg {l.who}">{l.text}{#if l.undo}<div><button class="small" onclick={() => undo(l)}>↩️ Undo</button></div>{/if}</div>
    {/if}
  {/each}
  {#if busy}<div class="msg ai muted">…</div>{/if}
</div>
{#if !billing.user}<div class="note warn" style="margin-top:8px">Sign in with Google (More → My account) to use the assistant.</div>{/if}
<div class="row" style="gap:6px;margin-top:8px">
  <input type="text" style="flex:1" bind:value={text} placeholder="e.g. hit 10 cm low at 500 m" onkeydown={(e) => { if (e.key === "Enter") send(); }} disabled={busy} />
  <button class="primary" onclick={() => send()} disabled={busy || !text.trim()}>➤</button>
</div>
<div class="muted" style="margin-top:6px;display:flex;justify-content:space-between"><span>AI can be wrong — confirm big changes on paper.{#if remaining != null} · {remaining} left today{/if}</span>{#if lines.length}<button class="small" onclick={reset}>New chat</button>{/if}</div>

<style>
  .chat { max-height: 50vh; min-height: 120px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
  .msg { padding: 8px 10px; border-radius: 10px; max-width: 88%; white-space: pre-wrap; line-height: 1.35; }
  .msg.me { align-self: flex-end; background: var(--green); color: #000; }
  .msg.ai { align-self: flex-start; background: var(--panel2); border: 1px solid var(--border); }
  .msg.ask { align-self: stretch; max-width: 100%; background: var(--panel2); border: 1px solid var(--green); }
  .msg.ask ul { margin: 6px 0 8px 18px; padding: 0; }
  .msg.sys { align-self: center; font-size: .85rem; color: var(--muted); text-align: center; max-width: 100%; }
  .ex { flex: 1 1 45%; text-align: left; font-size: .85rem; padding: 8px; }
</style>
