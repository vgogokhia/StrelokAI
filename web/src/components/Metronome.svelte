<script lang="ts">
  /** Breathing / trigger-cadence metronome. Web Audio click, optional vibration, runs until stopped. */
  let bpm = $state(60);
  let running = $state(false);
  let beat = $state(0);
  let ctx: AudioContext | null = null, timer: number | null = null, next = 0;
  const PRESETS = [40, 50, 60, 72];
  function click(at: number, accent: boolean) {
    if (!ctx) return;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "square"; o.frequency.value = accent ? 1400 : 1000;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(0.5, at + 0.002); g.gain.exponentialRampToValueAtTime(0.0001, at + 0.05);
    o.connect(g).connect(ctx.destination); o.start(at); o.stop(at + 0.06);
  }
  function schedule() {
    if (!ctx) return;
    while (next < ctx.currentTime + 0.25) {
      const b = beat; click(next, b % 4 === 0);
      const delay = Math.max(0, (next - ctx.currentTime) * 1000);
      setTimeout(() => { beat = b + 1; if (b % 4 === 0) navigator.vibrate?.(20); }, delay);
      next += 60 / bpm;
    }
  }
  function start() { ctx ??= new AudioContext(); ctx.resume(); next = ctx.currentTime + 0.1; beat = 0; running = true; timer = window.setInterval(schedule, 100); }
  function stop() { running = false; if (timer) clearInterval(timer); timer = null; }
  $effect(() => () => stop());
</script>

<div class="row" style="align-items:center;gap:8px">
  <button class="small" onclick={() => (bpm = Math.max(30, bpm - 2))}>−</button>
  <div style="flex:1;text-align:center"><b style="font-size:1.6rem">{bpm}</b> <span class="muted">bpm</span></div>
  <button class="small" onclick={() => (bpm = Math.min(160, bpm + 2))}>+</button>
</div>
<div class="chips" style="margin:8px 0">{#each PRESETS as p}<button class:active={bpm === p} onclick={() => (bpm = p)}>{p}</button>{/each}</div>
<button class="primary" style="width:100%" onclick={() => (running ? stop() : start())}>{running ? `⏹ Stop · beat ${(beat % 4) + 1}` : "▶ Start"}</button>
<div class="muted" style="margin-top:6px">Breathe out on the accent, break the shot on the pause. 60 bpm ≈ resting pulse. Works with the screen on.</div>
