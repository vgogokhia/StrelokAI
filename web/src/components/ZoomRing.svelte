<script lang="ts">
  /** Rotary magnification ring: drag around it like the power ring on a scope. Tap the centre to snap back to the "true at" power. */
  interface Props { value: number; min: number; max: number; trueAt: number; onchange: (v: number) => void }
  let { value, min, max, trueAt, onchange }: Props = $props();
  const SWEEP = 300; // degrees of travel from min to max
  const R = 110, C = 130;
  const frac = $derived(max > min ? Math.min(1, Math.max(0, (value - min) / (max - min))) : 0);
  const ang = $derived(-SWEEP / 2 + frac * SWEEP); // 0° = straight up
  const tp = $derived(pos(trueAng, R));
  const kp = $derived(pos(ang, R));
  const trueAng = $derived(-SWEEP / 2 + Math.min(1, Math.max(0, (trueAt - min) / (max - min))) * SWEEP);
  const pos = (a: number, r: number) => ({ x: C + r * Math.sin((a * Math.PI) / 180), y: C - r * Math.cos((a * Math.PI) / 180) });
  const arc = (a0: number, a1: number, r: number) => { const p0 = pos(a0, r), p1 = pos(a1, r); return `M${p0.x},${p0.y} A${r},${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${p1.x},${p1.y}`; };
  const ticks = $derived.by(() => { const out: { a: number; big: boolean; label?: string }[] = []; const n = Math.round(max - min);
    for (let i = 0; i <= n; i++) { const m = min + i; const a = -SWEEP / 2 + ((m - min) / (max - min)) * SWEEP; const big = n <= 12 || i % Math.ceil(n / 12) === 0; out.push({ a, big, label: big ? String(m) : undefined }); }
    return out; });

  let svgEl = $state<SVGSVGElement | null>(null);
  let last: number | null = null, acc = 0, dragged = false;
  function angleOf(e: PointerEvent) { const b = svgEl!.getBoundingClientRect(); const x = e.clientX - (b.left + b.width / 2), y = e.clientY - (b.top + b.height / 2); return (Math.atan2(x, -y) * 180) / Math.PI; }
  function down(e: PointerEvent) { svgEl!.setPointerCapture(e.pointerId); last = angleOf(e); acc = value; dragged = false; }
  function move(e: PointerEvent) {
    if (last == null) return;
    let d = angleOf(e) - last; if (d > 180) d -= 360; if (d < -180) d += 360; // relative rotation, so the finger can start anywhere
    last += d; dragged = dragged || Math.abs(d) > 1;
    acc = Math.min(max, Math.max(min, acc + (d / SWEEP) * (max - min)));
    const snapped = Math.round(acc * 4) / 4; if (snapped !== value) onchange(snapped);
    e.preventDefault();
  }
  function up(e: PointerEvent) { if (last != null && !dragged) { const b = svgEl!.getBoundingClientRect(); const dx = e.clientX - (b.left + b.width / 2), dy = e.clientY - (b.top + b.height / 2); if (Math.hypot(dx, dy) < b.width * 0.25) onchange(trueAt); } last = null; }
</script>

<svg bind:this={svgEl} viewBox="0 0 260 260" style="width:min(260px,70vw);display:block;margin:0 auto;touch-action:none;user-select:none" role="slider" aria-label="Magnification" aria-valuemin={min} aria-valuemax={max} aria-valuenow={value}
  onpointerdown={down} onpointermove={move} onpointerup={up} onpointercancel={up}>
  <circle cx={C} cy={C} r={R + 14} fill="var(--panel2)" stroke="var(--border)" />
  <path d={arc(-SWEEP / 2, SWEEP / 2, R)} fill="none" stroke="var(--border)" stroke-width="6" stroke-linecap="round" />
  <path d={arc(-SWEEP / 2, ang, R)} fill="none" stroke="var(--green)" stroke-width="6" stroke-linecap="round" />
  {#each ticks as t}{@const a = pos(t.a, R - 12)}{@const b = pos(t.a, R - (t.big ? 24 : 18))}
    <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="var(--muted)" stroke-width={t.big ? 2 : 1} />
    {#if t.label}{@const l = pos(t.a, R - 36)}<text x={l.x} y={l.y} fill="var(--muted)" font-size="11" text-anchor="middle" dominant-baseline="middle">{t.label}</text>{/if}
  {/each}
  <circle cx={tp.x} cy={tp.y} r="4" fill="none" stroke="var(--text)" stroke-width="1.5" />
  <circle cx={kp.x} cy={kp.y} r="11" fill="var(--green)" stroke="#000" stroke-width="2" />
  <text x={C} y={C - 6} fill="var(--text)" font-size="34" font-weight="700" text-anchor="middle" dominant-baseline="middle">{value}×</text>
  <text x={C} y={C + 24} fill="var(--muted)" font-size="11" text-anchor="middle">{value === trueAt ? "reticle true" : "tap to reset"}</text>
</svg>
