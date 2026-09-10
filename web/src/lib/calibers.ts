/** Chamberings and bullet-diameter compatibility (port of ballistics/calibers.py). */
export const CHAMBERINGS: Record<string, number | null> = {
  ".22 LR": 0.224,
  ".223 Rem / 5.56": 0.224,
  ".22-250": 0.224,
  ".243 Win": 0.243,
  "6mm Creedmoor": 0.243,
  "6.5 Creedmoor": 0.264,
  "6.5x55": 0.264,
  ".260 Rem": 0.264,
  ".270 Win": 0.277,
  "7mm-08": 0.284,
  "7mm Rem Mag": 0.284,
  ".300 BLK": 0.308,
  ".308 Win / 7.62": 0.308,
  ".30-06": 0.308,
  ".300 Win Mag": 0.308,
  ".300 PRC": 0.308,
  ".338 Lapua": 0.338,
  ".50 BMG": 0.510,
  Other: null,
};

export const LIBRARY_CALIBER_TO_CHAMBERING: Record<string, string> = {
  ".22 LR": ".22 LR",
  ".223 Rem": ".223 Rem / 5.56",
  ".243 Win": ".243 Win",
  "6.5 Creedmoor": "6.5 Creedmoor",
  ".270 Win": ".270 Win",
  "7mm": "7mm Rem Mag",
  "7mm Rem Mag": "7mm Rem Mag",
  ".300 BLK": ".300 BLK",
  ".308 Win": ".308 Win / 7.62",
  ".300 Win Mag": ".300 Win Mag",
  ".338 Lapua": ".338 Lapua",
  ".50 BMG": ".50 BMG",
};

export const CHAMBERING_NAMES = Object.keys(CHAMBERINGS);

export function isCompatible(chambering: string, diameterIn: number | null | undefined, cartridge?: string): boolean {
  const bore = CHAMBERINGS[chambering] ?? null;
  if (bore === null) return true;
  if (cartridge && cartridge === chambering) return true;
  if (diameterIn == null) return false;
  return Math.abs(diameterIn - bore) <= 0.003;
}
