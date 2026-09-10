/**
 * Atmospheric model (port of ballistics/atmosphere.py).
 * ICAO standard atmosphere reference; humidity-corrected density.
 */
export interface AtmosphericConditions {
  temperatureC: number;
  pressureMbar: number; // station pressure, hPa
  humidityPct: number; // 0-100
  altitudeM: number;
}

export const STD_TEMP_C = 15.0;
export const STD_PRESSURE_MBAR = 1013.25;
export const STD_DENSITY = 1.225;
const LAPSE_RATE = 0.0065;
const GAS_CONSTANT = 287.05;
const GRAVITY = 9.80665;

export const STANDARD_ATMOSPHERE: AtmosphericConditions = {
  temperatureC: 15.0,
  pressureMbar: 1013.25,
  humidityPct: 0.0,
  altitudeM: 0.0,
};

/** Air density in kg/m³ (ideal gas with vapour-pressure correction). */
export function airDensity(c: AtmosphericConditions): number {
  const T = c.temperatureC + 273.15;
  const P = c.pressureMbar * 100;
  const es = 6.1078 * Math.pow(10, (7.5 * c.temperatureC) / (c.temperatureC + 237.3));
  const e = es * (c.humidityPct / 100);
  const Pd = P - e * 100;
  const Rd = 287.05;
  const Rv = 461.495;
  return Pd / (Rd * T) + (e * 100) / (Rv * T);
}

export function densityRatio(c: AtmosphericConditions): number {
  return airDensity(c) / STD_DENSITY;
}

/** Density altitude in metres (inverse barometric formula). */
export function densityAltitudeM(c: AtmosphericConditions): number {
  const rho = airDensity(c);
  const T0 = 288.15;
  const L = LAPSE_RATE;
  const da = (T0 / L) * (1 - Math.pow(rho / STD_DENSITY, (L * GAS_CONSTANT) / GRAVITY));
  return Number.isFinite(da) ? da : c.altitudeM;
}

export function densityAltitudeFt(c: AtmosphericConditions): number {
  return densityAltitudeM(c) * 3.28084;
}

/** Speed of sound in m/s (depends on temperature only). */
export function speedOfSound(c: AtmosphericConditions): number {
  const gamma = 1.4;
  return Math.sqrt(gamma * GAS_CONSTANT * (c.temperatureC + 273.15));
}

/** Pressure (mbar) at an altitude in the standard atmosphere. */
export function pressureAtAltitude(altitudeM: number): number {
  const P0 = STD_PRESSURE_MBAR * 100;
  const T0 = 288.15;
  const P = P0 * Math.pow(1 - (LAPSE_RATE * altitudeM) / T0, GRAVITY / (LAPSE_RATE * GAS_CONSTANT));
  return P / 100;
}
