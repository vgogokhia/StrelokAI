/** Parametric reticle library (port of components/reticle_lib.py). */
export interface ReticleSpec {
  name: string;
  unit: "MRAD" | "MOA";
  view: number;
  major: number;
  minor?: number;
  dots?: boolean;
  labelsEvery?: number;
  treeRows?: number;
  treeCols?: number;
  treeWidthPerUnit?: number;
  gridFull?: boolean;
  note?: string;
}

export const RETICLES: ReticleSpec[] = [
  { name: "MIL-Dot", unit: "MRAD", view: 10, major: 1, dots: true, labelsEvery: 5, note: "Classic 1-mil dots." },
  { name: "TMR / Mil hash", unit: "MRAD", view: 10, major: 1, minor: 0.5, labelsEvery: 5, note: "Leupold TMR, Vortex EBR-1, Athlon APMR." },
  { name: "Vortex EBR-7C (MRAD)", unit: "MRAD", view: 10, major: 1, minor: 0.2, labelsEvery: 2, treeRows: 1, treeCols: 0.2, treeWidthPerUnit: 0.5, note: "Razor Gen II/III, Viper PST Gen II." },
  { name: "Mil-C / Mil-R", unit: "MRAD", view: 10, major: 1, minor: 0.5, labelsEvery: 2, treeRows: 1, treeCols: 0.5, treeWidthPerUnit: 0.4, note: "Nightforce Mil-C / Mil-R." },
  { name: "Horus-style grid (H59/TREMOR)", unit: "MRAD", view: 10, major: 1, minor: 0.2, labelsEvery: 1, treeRows: 1, treeCols: 1, gridFull: true, note: "Full 1-mil grid below centre." },
  { name: "MSR / P4 fine (MRAD)", unit: "MRAD", view: 10, major: 1, minor: 0.2, labelsEvery: 1, note: "S&B MSR/P4F, Kahles SKMR." },
  { name: "MOA hash (MOAR / EBR-2C MOA)", unit: "MOA", view: 30, major: 5, minor: 1, labelsEvery: 10, note: "Nightforce MOAR, Vortex EBR-2C MOA." },
  { name: "MOA tree (EBR-7C MOA / TMOA)", unit: "MOA", view: 30, major: 5, minor: 1, labelsEvery: 10, treeRows: 5, treeCols: 1, treeWidthPerUnit: 0.5, note: "Vortex EBR-7C MOA, Leupold TMOA." },
  { name: "Duplex / plain crosshair", unit: "MRAD", view: 10, major: 0, note: "No marks — hold shown as a red dot only." },
];

const MRAD_TO_MOA = 3.43775;

export function holdUnits(holdMrad: number, spec: ReticleSpec, sfpScale = 1): number {
  return holdMrad * (spec.unit === "MOA" ? MRAD_TO_MOA : 1) * sfpScale;
}

export function renderSvg(spec: ReticleSpec, xU: number, yU: number, size = 480, ring: number | null = null): string {
  const c = size / 2;
  const k = (size / 2 - 12) / spec.view;
  const X = (u: number) => c + u * k;
  const Y = (u: number) => c + u * k;
  const col = "#9c9", dim = "#575", lab = "#6a6";
  const p: string[] = [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" style="width:100%;height:auto;display:block;background:#0a0a0a;border-radius:50%">`,
    `<circle cx="${c}" cy="${c}" r="${size / 2 - 2}" fill="none" stroke="#1a1a1a" stroke-width="2"/>`,
    `<line x1="8" y1="${c}" x2="${size - 8}" y2="${c}" stroke="${col}" stroke-width="1.2"/>`,
    `<line x1="${c}" y1="8" x2="${c}" y2="${size - 8}" stroke="${col}" stroke-width="1.2"/>`,
  ];
  const hashes = (step: number, len: number, w: number) => {
    if (step <= 0) return;
    const n = Math.floor(spec.view / step);
    for (let i = -n; i <= n; i++) {
      const u = i * step;
      if (Math.abs(u) < 1e-9) continue;
      p.push(`<line x1="${X(u)}" y1="${c - len}" x2="${X(u)}" y2="${c + len}" stroke="${col}" stroke-width="${w}"/>`);
      p.push(`<line x1="${c - len}" y1="${Y(u)}" x2="${c + len}" y2="${Y(u)}" stroke="${col}" stroke-width="${w}"/>`);
    }
  };
  if (spec.minor) hashes(spec.minor, 3, 1);
  if (spec.major) {
    if (spec.dots) {
      const n = Math.floor(spec.view / spec.major);
      for (let i = -n; i <= n; i++) {
        const u = i * spec.major;
        if (Math.abs(u) < 1e-9) continue;
        p.push(`<circle cx="${X(u)}" cy="${c}" r="2.6" fill="${col}"/>`);
        p.push(`<circle cx="${c}" cy="${Y(u)}" r="2.6" fill="${col}"/>`);
      }
    } else hashes(spec.major, 7, 1.4);
  }
  if (spec.labelsEvery && spec.major) {
    const n = Math.floor(spec.view / spec.labelsEvery);
    for (let i = 1; i <= n; i++) {
      const u = i * spec.labelsEvery;
      const t = `${u}`;
      p.push(`<text x="${X(u) + 3}" y="${c - 9}" fill="${lab}" font-size="10" font-family="monospace">${t}</text>`);
      p.push(`<text x="${X(-u) + 3}" y="${c - 9}" fill="${lab}" font-size="10" font-family="monospace">${t}</text>`);
      p.push(`<text x="${c + 8}" y="${Y(u) + 4}" fill="${lab}" font-size="10" font-family="monospace">${t}</text>`);
      p.push(`<text x="${c + 8}" y="${Y(-u) + 4}" fill="${lab}" font-size="10" font-family="monospace">${t}</text>`);
    }
  }
  if (spec.treeRows && spec.treeCols) {
    const rows = Math.floor(spec.view / spec.treeRows);
    for (let r = 1; r <= rows; r++) {
      const u = r * spec.treeRows;
      const half = spec.gridFull ? spec.view : Math.min(spec.view, u * (spec.treeWidthPerUnit ?? 0) + spec.treeCols);
      const ncol = Math.floor(half / spec.treeCols);
      for (let j = -ncol; j <= ncol; j++) {
        const x = j * spec.treeCols;
        if (Math.abs(x) < 1e-9) continue;
        const big = spec.major ? Math.abs(x - Math.round(x / spec.major) * spec.major) < 1e-6 : false;
        if (spec.gridFull) p.push(`<circle cx="${X(x)}" cy="${Y(u)}" r="${big ? 1.6 : 1}" fill="${dim}"/>`);
        else {
          const ln = big ? 4 : 2.2;
          p.push(`<line x1="${X(x)}" y1="${Y(u) - ln}" x2="${X(x)}" y2="${Y(u) + ln}" stroke="${dim}" stroke-width="1"/>`);
        }
      }
      if (!spec.gridFull) p.push(`<line x1="${X(-half)}" y1="${Y(u)}" x2="${X(half)}" y2="${Y(u)}" stroke="${dim}" stroke-width="0.6"/>`);
    }
  }
  if (ring) p.push(`<circle cx="${X(xU)}" cy="${Y(yU)}" r="${(ring * k) / 2}" fill="none" stroke="#fa4" stroke-width="1" stroke-dasharray="3,3"/>`);
  const xv = Math.max(-spec.view, Math.min(spec.view, xU));
  const yv = Math.max(-spec.view, Math.min(spec.view, yU));
  const off = Math.abs(xU) > spec.view || Math.abs(yU) > spec.view;
  p.push(`<circle cx="${X(xv)}" cy="${Y(yv)}" r="6" fill="#ff3030" stroke="#fff" stroke-width="1.5"${off ? ' opacity="0.5"' : ""}/>`);
  p.push(`<line x1="${X(xv) - 10}" y1="${Y(yv)}" x2="${X(xv) + 10}" y2="${Y(yv)}" stroke="#ff3030" stroke-width="1"/>`);
  p.push(`<line x1="${X(xv)}" y1="${Y(yv) - 10}" x2="${X(xv)}" y2="${Y(yv) + 10}" stroke="#ff3030" stroke-width="1"/>`);
  p.push("</svg>");
  return p.join("");
}
