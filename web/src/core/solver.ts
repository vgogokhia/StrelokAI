/**
 * Point-mass ballistic solver — TypeScript port of ballistics/solver.py.
 *
 * Physics: RK4 (adaptive step), drag a = (π/8)·Cd(M)·ρ·v²/BC_si, velocity-
 * stepped BCs, Miller stability (+Litz correction), Litz spin drift and
 * aerodynamic jump, inclination (rotated gravity), cant (post rotation),
 * Coriolis (horizontal + Eötvös vertical), zeroing atmosphere.
 *
 * Coordinates: x downrange, y up, z right. drop_m negative = below line
 * of sight. windage_m = impact offset, negative = left. Wind direction is
 * where the wind blows FROM relative to the shooter (0 headwind, 90 from
 * the right).
 *
 * Every number here must match the Python engine — see tests/reference.
 */
import { airDensity, speedOfSound, type AtmosphericConditions } from "./atmosphere";
import { curveToDragTable, dragCoefficient, tableFor, type DragTable, type DragCurve, type DragModel } from "./drag";

export const BC_LBIN2_TO_KGM2 = 703.0696;
export const DRAG_FACTOR = Math.PI / 8.0;
const GRAVITY = 9.80665;
const EARTH_ROTATION_RAD_S = 7.2921159e-5;
const GRAIN_KG = 0.0000647989;

export interface Projectile {
  massGrains: number;
  diameterIn: number;
  bcG1?: number | null;
  bcG7?: number | null;
  lengthIn?: number;
  /** [velocityFloorFps, bc] pairs, any order. */
  bcSegments?: ReadonlyArray<readonly [number, number]> | null;
  dragCurve?: DragCurve | null;
}

export interface Rifle {
  muzzleVelocityMps: number;
  zeroRangeM?: number;
  sightHeightMm?: number;
  twistRateIn?: number;
  twistDirection?: "right" | "left";
}

export interface Wind {
  speedMps: number;
  /** FROM direction relative to the shooter, degrees. */
  directionDeg: number;
}

export interface SolveOptions {
  projectile: Projectile;
  rifle: Rifle;
  atmosphere: AtmosphericConditions;
  wind?: Wind;
  latitudeDeg?: number;
  azimuthDeg?: number;
  elevationAngleDeg?: number;
  cantAngleDeg?: number;
  zeroAtmosphere?: AtmosphericConditions | null;
  targetRangeM: number;
  stepM?: number;
}

export interface TrajectoryPoint {
  timeS: number;
  rangeM: number;
  dropM: number;
  windageM: number;
  velocityMps: number;
  energyJ: number;
  mach: number;
}

export interface BallisticSolution {
  trajectory: TrajectoryPoint[];
  zeroAngleMrad: number;
  spinDriftM: number;
  coriolisVerticalM: number;
  coriolisHorizontalM: number;
  stabilityFactor: number;
  aeroJumpMrad: number;
}

export const MRAD_TO_MOA = 3.43775;
export const dropMrad = (p: TrajectoryPoint): number => (p.rangeM === 0 ? 0 : (p.dropM / p.rangeM) * 1000);
export const windageMrad = (p: TrajectoryPoint): number => (p.rangeM === 0 ? 0 : (p.windageM / p.rangeM) * 1000);
export const dropMoa = (p: TrajectoryPoint): number => dropMrad(p) * MRAD_TO_MOA;
export const windageMoa = (p: TrajectoryPoint): number => windageMrad(p) * MRAD_TO_MOA;

/** Linear interpolation of the trajectory at a range. */
export function atRange(sol: BallisticSolution, rangeM: number): TrajectoryPoint | null {
  const tr = sol.trajectory;
  if (tr.length === 0) return null;
  if (rangeM <= tr[0].rangeM) return tr[0];
  for (let i = 0; i < tr.length - 1; i++) {
    const a = tr[i];
    const b = tr[i + 1];
    if (a.rangeM <= rangeM && rangeM <= b.rangeM) {
      const span = b.rangeM - a.rangeM;
      const t = span === 0 ? 0 : (rangeM - a.rangeM) / span;
      return {
        timeS: a.timeS + t * (b.timeS - a.timeS),
        rangeM,
        dropM: a.dropM + t * (b.dropM - a.dropM),
        windageM: a.windageM + t * (b.windageM - a.windageM),
        velocityMps: a.velocityMps + t * (b.velocityMps - a.velocityMps),
        energyJ: a.energyJ + t * (b.energyJ - a.energyJ),
        mach: a.mach + t * (b.mach - a.mach),
      };
    }
  }
  return tr[tr.length - 1];
}

type State = [number, number, number, number, number, number]; // x y z vx vy vz

class Solver {
  private readonly proj: Projectile;
  private readonly rifle: Required<Rifle>;
  private readonly wind: Wind;
  private readonly opts: SolveOptions;
  private readonly table: DragTable;
  private readonly bc: number;
  private readonly useCdm: boolean;
  private rho: number;
  private sos: number;
  private readonly shootRho: number;
  private readonly shootSos: number;
  private readonly zeroRho: number;
  private readonly zeroSos: number;
  private readonly segments: Array<readonly [number, number]> | null;
  private sgCache: number | null = null;

  constructor(opts: SolveOptions) {
    this.opts = opts;
    this.proj = opts.projectile;
    this.rifle = {
      muzzleVelocityMps: opts.rifle.muzzleVelocityMps,
      zeroRangeM: opts.rifle.zeroRangeM ?? 100,
      sightHeightMm: opts.rifle.sightHeightMm ?? 40,
      twistRateIn: opts.rifle.twistRateIn ?? 10,
      twistDirection: opts.rifle.twistDirection ?? "right",
    };
    this.wind = opts.wind ?? { speedMps: 0, directionDeg: 0 };

    if (this.proj.dragCurve && this.proj.dragCurve.length) {
      this.table = curveToDragTable(this.proj.dragCurve);
      this.bc = 1;
      this.useCdm = true;
    } else if (this.proj.bcG7) {
      this.table = tableFor("G7");
      this.bc = this.proj.bcG7;
      this.useCdm = false;
    } else if (this.proj.bcG1) {
      this.table = tableFor("G1");
      this.bc = this.proj.bcG1;
      this.useCdm = false;
    } else {
      throw new Error("Projectile must have a drag curve, G7 BC or G1 BC");
    }
    this.segments = this.proj.bcSegments && this.proj.bcSegments.length
      ? [...this.proj.bcSegments].sort((a, b) => b[0] - a[0])
      : null;

    this.shootRho = airDensity(opts.atmosphere);
    this.shootSos = speedOfSound(opts.atmosphere);
    const z = opts.zeroAtmosphere ?? opts.atmosphere;
    this.zeroRho = airDensity(z);
    this.zeroSos = speedOfSound(z);
    this.rho = this.shootRho;
    this.sos = this.shootSos;
  }

  // --- helpers ---------------------------------------------------------
  private massKg(): number {
    return this.proj.massGrains * GRAIN_KG;
  }

  private activeBc(vMps: number): number {
    if (!this.segments) return this.bc;
    const vFps = vMps * 3.28084;
    for (const [floor, bc] of this.segments) if (vFps >= floor) return bc;
    return this.segments[this.segments.length - 1][1];
  }

  private dragAccel(vRel: number, mach: number): number {
    if (vRel <= 0) return 0;
    const cd = dragCoefficient(mach, this.table);
    if (this.useCdm) {
      const d = this.proj.diameterIn * 0.0254;
      const m = this.massKg();
      if (m <= 0) return 0;
      return (DRAG_FACTOR * cd * this.rho * vRel * vRel * (d * d)) / m;
    }
    const bcSi = this.activeBc(vRel) * BC_LBIN2_TO_KGM2;
    return (DRAG_FACTOR * cd * this.rho * vRel * vRel) / bcSi;
  }

  private crosswind(): number {
    return this.wind.speedMps * Math.sin((this.wind.directionDeg * Math.PI) / 180);
  }
  private headwind(): number {
    return this.wind.speedMps * Math.cos((this.wind.directionDeg * Math.PI) / 180);
  }

  millerStability(): number {
    if (this.sgCache !== null) return this.sgCache;
    const d = this.proj.diameterIn;
    if (d <= 0) return (this.sgCache = 0);
    const t = this.rifle.twistRateIn / d;
    const L = (this.proj.lengthIn ?? 1.0) / d;
    const m = this.proj.massGrains;
    const denom = t * t * Math.pow(d, 3) * L * (1 + L * L);
    if (denom <= 0) return (this.sgCache = 0);
    let sg = (30 * m) / denom;
    const vFps = this.rifle.muzzleVelocityMps * 3.28084;
    if (vFps > 0) sg *= Math.pow(vFps / 2800, 1 / 3);
    const a = this.opts.atmosphere;
    const TR = (a.temperatureC + 273.15) * 1.8;
    const PinHg = a.pressureMbar * 0.02953;
    if (TR > 0 && PinHg > 0) sg *= (TR / 519) * (29.92 / PinHg);
    return (this.sgCache = sg);
  }

  private spinDriftM(tofS: number): number {
    if (tofS <= 0) return 0;
    const sg = this.millerStability();
    let sd = 1.25 * (sg + 1.2) * Math.pow(tofS, 1.83) * 0.0254;
    if (this.rifle.twistDirection === "left") sd = -sd;
    return sd;
  }

  private aeroJumpMrad(): number {
    const sg = this.millerStability();
    const crossMph = this.crosswind() * 2.23694;
    let aj = (0.01 * sg * crossMph) / MRAD_TO_MOA;
    if (this.rifle.twistDirection === "left") aj = -aj;
    return aj;
  }

  private coriolis(tofS: number, rangeM: number): [number, number] {
    const lat = ((this.opts.latitudeDeg ?? 41.7) * Math.PI) / 180;
    const az = ((this.opts.azimuthDeg ?? 0) * Math.PI) / 180;
    const horiz = EARTH_ROTATION_RAD_S * rangeM * Math.sin(lat) * tofS;
    const vert = EARTH_ROTATION_RAD_S * rangeM * Math.cos(lat) * Math.sin(az) * tofS;
    return [vert, horiz];
  }

  // --- integrator ------------------------------------------------------
  private derivatives(s: State, wx: number, wz: number, gx: number, gy: number): State {
    const [, , , vx, vy, vz] = s;
    const rx = vx - wx;
    const rz = vz - wz;
    const vRel = Math.sqrt(rx * rx + vy * vy + rz * rz);
    const mach = this.sos > 0 ? vRel / this.sos : 0;
    if (vRel > 0) {
      const a = this.dragAccel(vRel, mach);
      return [vx, vy, vz, (-a * rx) / vRel + gx, (-a * vy) / vRel + gy, (-a * rz) / vRel];
    }
    return [vx, vy, vz, gx, gy, 0];
  }

  private rk4(s: State, dt: number, wx: number, wz: number, gx: number, gy: number): State {
    const k1 = this.derivatives(s, wx, wz, gx, gy);
    const s2 = s.map((v, i) => v + 0.5 * dt * k1[i]) as State;
    const k2 = this.derivatives(s2, wx, wz, gx, gy);
    const s3 = s.map((v, i) => v + 0.5 * dt * k2[i]) as State;
    const k3 = this.derivatives(s3, wx, wz, gx, gy);
    const s4 = s.map((v, i) => v + dt * k3[i]) as State;
    const k4 = this.derivatives(s4, wx, wz, gx, gy);
    return s.map((v, i) => v + (dt / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i])) as State;
  }

  private integrate(boreAngle: number, maxRangeM: number, stepM: number): TrajectoryPoint[] {
    const v0 = this.rifle.muzzleVelocityMps;
    const theta = ((this.opts.elevationAngleDeg ?? 0) * Math.PI) / 180;
    const gx = -GRAVITY * Math.sin(theta);
    const gy = -GRAVITY * Math.cos(theta);
    // Air velocity: headwind moves air toward -x; wind FROM the right moves air toward -z.
    const wx = -this.headwind();
    const wz = -this.crosswind();
    const massKg = this.massKg();

    let state: State = [0, -this.rifle.sightHeightMm / 1000, 0, v0 * Math.cos(boreAngle), v0 * Math.sin(boreAngle), 0];
    let t = 0;
    let nextRecord = stepM;
    const out: TrajectoryPoint[] = [];
    const maxTime = 10;

    while (state[0] < maxRangeM && t < maxTime) {
      const rx = state[3] - wx;
      const rz = state[5] - wz;
      const vRel = Math.sqrt(rx * rx + state[4] * state[4] + rz * rz);
      const mach = this.sos > 0 ? vRel / this.sos : 0;
      const dt = Math.abs(mach - 1) < 0.2 ? 0.00015 : mach > 1.5 ? 0.0003 : 0.0005;

      const prev = state;
      const prevT = t;
      state = this.rk4(state, dt, wx, wz, gx, gy);
      t += dt;

      while (state[0] >= nextRecord && nextRecord <= maxRangeM) {
        const dx = state[0] - prev[0];
        if (dx <= 0) break;
        const u = (nextRecord - prev[0]) / dx;
        const rec = prev.map((v, i) => v + u * (state[i] - v)) as State;
        const recT = prevT + u * (t - prevT);
        const vTot = Math.sqrt(rec[3] * rec[3] + rec[4] * rec[4] + rec[5] * rec[5]);
        const rrx = rec[3] - wx;
        const rrz = rec[5] - wz;
        const rvRel = Math.sqrt(rrx * rrx + rec[4] * rec[4] + rrz * rrz);
        out.push({
          timeS: recT,
          rangeM: nextRecord,
          dropM: rec[1],
          windageM: rec[2],
          velocityMps: vTot,
          energyJ: 0.5 * massKg * vTot * vTot,
          mach: this.sos > 0 ? rvRel / this.sos : 0,
        });
        nextRecord += stepM;
      }
    }
    return out;
  }

  private findZeroAngle(zeroRangeM: number): number {
    const sightH = this.rifle.sightHeightMm / 1000;
    const v0 = this.rifle.muzzleVelocityMps;
    this.rho = this.zeroRho;
    this.sos = this.zeroSos;
    const tFlight = zeroRangeM / v0;
    const dropSimple = 0.5 * GRAVITY * tFlight * tFlight;
    let angle = Math.atan((dropSimple + sightH) / zeroRangeM);
    for (let i = 0; i < 12; i++) {
      const traj = this.integrate(angle, zeroRangeM + 20, 5);
      let dropAtZero: number | null = null;
      for (const pt of traj) {
        if (pt.rangeM >= zeroRangeM) {
          dropAtZero = pt.dropM;
          break;
        }
      }
      if (dropAtZero === null) {
        if (traj.length) dropAtZero = traj[traj.length - 1].dropM;
        else break;
      }
      const error = -dropAtZero;
      angle += Math.atan(error / zeroRangeM) * 0.7;
      if (Math.abs(error) < 0.0001) break;
    }
    this.rho = this.shootRho;
    this.sos = this.shootSos;
    return angle;
  }

  solve(): BallisticSolution {
    const targetRangeM = this.opts.targetRangeM;
    const stepM = this.opts.stepM ?? 10;
    const zeroRange = this.rifle.zeroRangeM;
    const zeroAngle = this.findZeroAngle(zeroRange);
    const maxRange = Math.max(targetRangeM + 50, zeroRange + 50);
    const trajectory = this.integrate(zeroAngle, maxRange, stepM);

    let spinDrift = 0;
    let cv = 0;
    let ch = 0;
    const target = trajectory.find((p) => p.rangeM >= targetRangeM);
    if (target) {
      spinDrift = this.spinDriftM(target.timeS);
      [cv, ch] = this.coriolis(target.timeS, targetRangeM);
    }
    const sg = this.millerStability();
    const aj = this.aeroJumpMrad();

    for (const pt of trajectory) {
      const sd = this.spinDriftM(pt.timeS);
      const [pv, ph] = this.coriolis(pt.timeS, pt.rangeM);
      pt.windageM += sd + ph;
      pt.dropM += pv + (aj / 1000) * pt.rangeM;
    }

    const phi = ((this.opts.cantAngleDeg ?? 0) * Math.PI) / 180;
    if (phi !== 0) {
      const c = Math.cos(phi);
      const s = Math.sin(phi);
      for (const pt of trajectory) {
        const d = pt.dropM;
        const w = pt.windageM;
        pt.dropM = d * c - w * s;
        pt.windageM = d * s + w * c;
      }
    }

    return {
      trajectory,
      zeroAngleMrad: zeroAngle * 1000,
      spinDriftM: spinDrift,
      coriolisVerticalM: cv,
      coriolisHorizontalM: ch,
      stabilityFactor: sg,
      aeroJumpMrad: aj,
    };
  }
}

export function solve(opts: SolveOptions): BallisticSolution {
  return new Solver(opts).solve();
}

/** Flat-argument convenience wrapper mirroring Python's calculate_solution. */
export interface CalcInputs {
  muzzleVelocityMps: number;
  bcG7?: number | null;
  bcG1?: number | null;
  dragModel?: DragModel;
  massGrains: number;
  diameterIn: number;
  zeroRangeM: number;
  targetRangeM: number;
  temperatureC?: number;
  pressureMbar?: number;
  humidityPct?: number;
  altitudeM?: number;
  windSpeedMps?: number;
  windDirectionDeg?: number;
  latitudeDeg?: number;
  azimuthDeg?: number;
  bulletLengthIn?: number;
  twistRateIn?: number;
  twistDirection?: "right" | "left";
  sightHeightMm?: number;
  elevationAngleDeg?: number;
  cantAngleDeg?: number;
  bcSegments?: ReadonlyArray<readonly [number, number]> | null;
  dragCurve?: DragCurve | null;
  zeroTemperatureC?: number | null;
  zeroPressureMbar?: number | null;
  zeroHumidityPct?: number | null;
  zeroAltitudeM?: number | null;
}

export function calculateSolution(i: CalcInputs): BallisticSolution {
  const atmosphere: AtmosphericConditions = {
    temperatureC: i.temperatureC ?? 15,
    pressureMbar: i.pressureMbar ?? 1013.25,
    humidityPct: i.humidityPct ?? 50,
    altitudeM: i.altitudeM ?? 0,
  };
  const zeroDiffers = [i.zeroTemperatureC, i.zeroPressureMbar, i.zeroHumidityPct, i.zeroAltitudeM].some(
    (v) => v !== undefined && v !== null,
  );
  const zeroAtmosphere: AtmosphericConditions | null = zeroDiffers
    ? {
        temperatureC: i.zeroTemperatureC ?? atmosphere.temperatureC,
        pressureMbar: i.zeroPressureMbar ?? atmosphere.pressureMbar,
        humidityPct: i.zeroHumidityPct ?? atmosphere.humidityPct,
        altitudeM: i.zeroAltitudeM ?? atmosphere.altitudeM,
      }
    : null;
  let bcG7 = i.bcG7 ?? null;
  let bcG1 = i.bcG1 ?? null;
  if (i.dragModel === "G1" && bcG7 && !bcG1) {
    bcG1 = bcG7;
    bcG7 = null;
  }
  return solve({
    projectile: {
      massGrains: i.massGrains,
      diameterIn: i.diameterIn,
      bcG7,
      bcG1,
      lengthIn: i.bulletLengthIn ?? 1.0,
      bcSegments: i.bcSegments ?? null,
      dragCurve: i.dragCurve ?? null,
    },
    rifle: {
      muzzleVelocityMps: i.muzzleVelocityMps,
      zeroRangeM: i.zeroRangeM,
      sightHeightMm: i.sightHeightMm ?? 40,
      twistRateIn: i.twistRateIn ?? 10,
      twistDirection: i.twistDirection ?? "right",
    },
    atmosphere,
    wind: { speedMps: i.windSpeedMps ?? 0, directionDeg: i.windDirectionDeg ?? 90 },
    latitudeDeg: i.latitudeDeg ?? 41.7,
    azimuthDeg: i.azimuthDeg ?? 0,
    elevationAngleDeg: i.elevationAngleDeg ?? 0,
    cantAngleDeg: i.cantAngleDeg ?? 0,
    zeroAtmosphere,
    targetRangeM: i.targetRangeM,
  });
}

/** Shift a solution for a POI offset at the zero range (cm, + high / + right). */
export function applyZeroOffset(sol: BallisticSolution, zeroRangeM: number, vCm: number, hCm: number): BallisticSolution {
  if ((!vCm && !hCm) || zeroRangeM <= 0) return sol;
  const kv = vCm / 100 / zeroRangeM;
  const kh = hCm / 100 / zeroRangeM;
  for (const p of sol.trajectory) {
    p.dropM += kv * p.rangeM;
    p.windageM += kh * p.rangeM;
  }
  return sol;
}

/** Powder-temperature compensated MV (port of ballistics/mv_curve.py). */
export function applyMvCurve(
  baseMv: number,
  baseTempC: number,
  currentTempC: number,
  sensitivityPctPerC: number,
  curve?: ReadonlyArray<readonly [number, number]> | null,
): number {
  if (curve && curve.length) {
    const pts = [...curve].sort((a, b) => a[0] - b[0]);
    if (currentTempC <= pts[0][0]) return pts[0][1];
    if (currentTempC >= pts[pts.length - 1][0]) return pts[pts.length - 1][1];
    for (let k = 0; k < pts.length - 1; k++) {
      const [t0, v0] = pts[k];
      const [t1, v1] = pts[k + 1];
      if (t0 <= currentTempC && currentTempC <= t1) {
        const f = t1 === t0 ? 0 : (currentTempC - t0) / (t1 - t0);
        return v0 + f * (v1 - v0);
      }
    }
  }
  return baseMv * (1 + (sensitivityPctPerC / 100) * (currentTempC - baseTempC));
}
