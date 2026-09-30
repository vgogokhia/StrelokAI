// Computes every number quoted in the glossary with the app's own solver,
// so the articles and the calculator can never disagree.
import { createServer } from "vite";

const FPS = 0.3048;

export const LOADS = {
  "308": { name: ".308 Win, 175 gr Sierra MatchKing", short: ".308 175 gr", muzzleVelocityMps: 2600 * FPS, bcG7: 0.243, massGrains: 175, diameterIn: 0.308, bulletLengthIn: 1.24, twistRateIn: 11.25, sightHeightMm: 38, zeroYd: 100 },
  "65cm": { name: "6.5 Creedmoor, 140 gr Hornady ELD Match", short: "6.5 CM 140 gr", muzzleVelocityMps: 2710 * FPS, bcG7: 0.326, massGrains: 140, diameterIn: 0.264, bulletLengthIn: 1.40, twistRateIn: 8, sightHeightMm: 38, zeroYd: 100 },
  "223": { name: ".223 Rem, 55 gr FMJ", short: ".223 55 gr", muzzleVelocityMps: 3240 * FPS, bcG1: 0.243, massGrains: 55, diameterIn: 0.224, bulletLengthIn: 0.75, twistRateIn: 9, sightHeightMm: 66, zeroYd: 100 },
  "22lr": { name: ".22 LR, 40 gr standard velocity", short: ".22 LR 40 gr", muzzleVelocityMps: 1070 * FPS, bcG1: 0.138, massGrains: 40, diameterIn: 0.223, bulletLengthIn: 0.45, twistRateIn: 16, sightHeightMm: 38, zeroYd: 50 },
};

/**
 * metric=false: distances in yards, small lengths in inches, speeds in fps, energy in ft·lb, 10 mph wind.
 * metric=true:  distances in meters, small lengths in cm, speeds in m/s, energy in J, 5 m/s wind.
 * Field names (dropIn, windIn, fps, ftlb, yd) are kept for both; they hold the values in the chosen units.
 */
export async function computeFacts({ metric = false } = {}) {
  const vite = await createServer({ configFile: false, root: new URL("../..", import.meta.url).pathname, server: { middlewareMode: true }, appType: "custom", logLevel: "silent" });
  const core = await vite.ssrLoadModule("/src/core/index.ts");
  await vite.close();
  const YD = metric ? 1 : 0.9144, IN = metric ? 0.01 : 0.0254, V = metric ? 1 : FPS, FTLB = metric ? 1 : 1.35582;
  const WIND = metric ? 5 : 10 * 0.44704;

  const solve = (key, extra = {}) => {
    const l = LOADS[key];
    const { name, short, zeroYd, ...inp } = l;
    return core.calculateSolution({ ...inp, zeroRangeM: zeroYd * YD, targetRangeM: 1100 * YD, windSpeedMps: WIND, windDirectionDeg: 90, ...extra });
  };
  const row = (sol, yd) => {
    const p = core.atRange(sol, yd * YD);
    return {
      yd, dropIn: p.dropM / IN, moa: core.dropMoa(p), mil: core.dropMrad(p), windIn: p.windageM / IN, windMil: core.windageMrad(p),
      fps: p.velocityMps / V, ftlb: p.energyJ / FTLB, mach: p.mach, tof: p.timeS,
    };
  };
  // Drop from a calm-air run; wind column is wind-only drift (windy minus calm), so spin drift is not mixed in.
  const table = (key, yards, extra = {}) => {
    const calm = solve(key, { ...extra, windSpeedMps: 0 }), windy = solve(key, extra);
    return yards.map((y) => { const c = row(calm, y), w = row(windy, y); return { ...c, windIn: Math.abs(w.windIn - c.windIn), windMil: Math.abs(w.windMil - c.windMil) }; });
  };

  const F = { loads: LOADS, tables: {}, metric };
  const long = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000];
  F.tables["308"] = table("308", long);
  F.tables["65cm"] = table("65cm", long);
  F.tables["223"] = table("223", [100, 200, 300, 400, 500, 600]);
  F.tables["22lr"] = table("22lr", metric ? [25, 50, 75, 100, 125, 150, 175, 200, 250] : [25, 50, 75, 100, 125, 150, 175, 200, 250, 300]);

  // Spin drift, stability, Coriolis for the .308 at 1000 yd (no wind, so drift is isolated).
  const calm = solve("308", { windSpeedMps: 0, targetRangeM: 1000 * YD, latitudeDeg: metric ? 42 : 40 });
  F.spin308In = calm.spinDriftM / IN;
  F.sg308 = calm.stabilityFactor;
  F.sg308_12 = solve("308", { twistRateIn: 12, windSpeedMps: 0 }).stabilityFactor;
  F.sg308_10 = solve("308", { twistRateIn: 10, windSpeedMps: 0 }).stabilityFactor;
  F.sg65 = solve("65cm", { windSpeedMps: 0 }).stabilityFactor;
  const cor = (az) => solve("308", { windSpeedMps: 0, targetRangeM: 1000 * YD, latitudeDeg: metric ? 42 : 40, azimuthDeg: az, twistRateIn: 11.25 });
  F.corNorthHIn = cor(0).coriolisHorizontalM / IN;
  F.corEastVIn = cor(90).coriolisVerticalM / IN;
  F.corWestVIn = cor(270).coriolisVerticalM / IN;
  F.corLat = [0, 20, 30, 42, 50, 60].map((lat) => ({ lat, h: solve("308", { windSpeedMps: 0, targetRangeM: 1000 * YD, latitudeDeg: lat, azimuthDeg: 0 }).coriolisHorizontalM / IN }));

  // Density altitude: .308 drop at 1000 yd, sea level 59°F vs 5000 ft 90°F.
  const at1000 = (extra) => row(solve("308", { windSpeedMps: 0, ...extra }), 1000);
  // Imperial example: 5000 ft, 90 °F. Metric example: 1500 m, 32 °C (station pressure ≈ 845 mbar).
  F.da = { sea: at1000({}), high: at1000(metric ? { altitudeM: 1500, pressureMbar: 845, temperatureC: 32 } : { altitudeM: 5000 * 0.3048, pressureMbar: 843, temperatureC: 32 }) };
  // Temperature: MV change of 1.5 fps/°F over 40 °F.
  F.mvTemp = { base: at1000({}), slow: at1000({ muzzleVelocityMps: (2600 - 60) * FPS }) }; // 60 fps ≈ 18 m/s slower
  // Incline: 30° uphill at 600 yd.
  F.incline = { flat: row(solve("308", { windSpeedMps: 0 }), 600), up30: row(solve("308", { windSpeedMps: 0, elevationAngleDeg: 30 }), 600) };
  // Sight height effect at 100 and 500 yd.
  F.sight = [38, 66].map((h) => ({ h, r: [50, 300, 600].map((y) => row(solve("308", { windSpeedMps: 0, sightHeightMm: h }), y)) }));
  // Zero distance: .308 100 yd vs 200 yd zero.
  F.zero200 = [100, 200, 300, 400, 500].map((y) => row(solve("308", { windSpeedMps: 0, zeroRangeM: 200 * YD }), y));
  // Transonic range (first yard where Mach < 1.2 and < 1.0) for .308 and 6.5.
  const transonic = (key) => { const s = solve(key, { windSpeedMps: 0, targetRangeM: 1600 * 0.9144 }); const f = (m) => { const p = s.trajectory.find((q) => q.mach < m); return p ? p.rangeM / YD : null; }; return { m12: f(1.2), m10: f(1.0) }; };
  F.trans = { "308": transonic("308"), "65cm": transonic("65cm") };
  return F;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const F = await computeFacts({ metric: process.argv[2] === "metric" });
  const r = (o) => JSON.stringify(o, (k, v) => (typeof v === "number" ? Math.round(v * 100) / 100 : v));
  for (const [k, t] of Object.entries(F.tables)) { console.log(k); for (const x of t) console.log(" ", r(x)); }
  const { tables, loads, ...rest } = F; console.log(r(rest));
}
