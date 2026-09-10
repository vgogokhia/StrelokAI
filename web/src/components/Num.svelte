<script lang="ts">
  /**
   * Numeric field that edits a metric value through a display unit.
   * `get`/`set` convert display<->stored; the stored value only changes
   * when the user actually edits (no round-trip drift).
   */
  interface Props {
    label: string;
    value: number;
    onchange: (v: number) => void;
    from?: (v: number) => number;
    to?: (v: number) => number;
    step?: number;
    min?: number;
    max?: number;
    digits?: number;
  }
  let { label, value, onchange, from = (v) => v, to = (v) => v, step = 1, min, max, digits = 1 }: Props = $props();
  let text = $state("");
  let focused = $state(false);
  const shown = $derived(Number(from(value).toFixed(digits)));
  $effect(() => {
    if (!focused) text = String(shown);
  });
  function commit() {
    const v = parseFloat(text.replace(",", "."));
    if (!Number.isFinite(v)) { text = String(shown); return; }
    let d = v;
    if (min != null) d = Math.max(min, d);
    if (max != null) d = Math.min(max, d);
    if (d !== shown) onchange(to(d));
    text = String(Number(d.toFixed(digits)));
  }
  function bump(dir: number) {
    const v = Number((shown + dir * step).toFixed(digits));
    let d = v;
    if (min != null) d = Math.max(min, d);
    if (max != null) d = Math.min(max, d);
    onchange(to(d));
  }
</script>

<div>
  <label class="f">{label}</label>
  <div class="row" style="gap:4px;flex-wrap:nowrap">
    <button class="small" style="min-width:40px" onclick={() => bump(-1)} aria-label="decrease">−</button>
    <input type="number" inputmode="decimal" style="flex:1;min-width:0;padding-left:6px;padding-right:2px" {step} bind:value={text}
      onfocus={() => (focused = true)} onblur={() => { focused = false; commit(); }}
      onkeydown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }} />
    <button class="small" style="min-width:40px" onclick={() => bump(1)} aria-label="increase">+</button>
  </div>
</div>
