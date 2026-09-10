/** Open-Meteo current conditions (free, CORS-enabled, no key). */
export interface Weather {
  temperatureC: number;
  pressureMbar: number; // surface (station) pressure
  humidityPct: number;
  windSpeedMps: number;
  windDirectionDeg: number; // FROM
  elevationM: number;
}

export async function fetchWeather(lat: number, lon: number): Promise<Weather> {
  const url = new URL("https://api.open-meteo.com/v1/forecast");
  url.searchParams.set("latitude", String(lat));
  url.searchParams.set("longitude", String(lon));
  url.searchParams.set("current", "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m");
  url.searchParams.set("wind_speed_unit", "ms");
  const r = await fetch(url.toString(), { signal: AbortSignal.timeout(10000) });
  if (!r.ok) throw new Error(`weather ${r.status}`);
  const j = await r.json();
  const c = j.current ?? {};
  if (c.temperature_2m == null) throw new Error("no data");
  return {
    temperatureC: +c.temperature_2m,
    pressureMbar: +c.surface_pressure,
    humidityPct: +c.relative_humidity_2m,
    windSpeedMps: +c.wind_speed_10m,
    windDirectionDeg: +c.wind_direction_10m,
    elevationM: +(j.elevation ?? 0),
  };
}

export function locate(): Promise<{ lat: number; lon: number; alt: number | null }> {
  return new Promise((res, rej) => {
    if (!navigator.geolocation) return rej(new Error("no geolocation"));
    navigator.geolocation.getCurrentPosition(
      (p) => res({ lat: p.coords.latitude, lon: p.coords.longitude, alt: p.coords.altitude }),
      (e) => rej(e),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  });
}
