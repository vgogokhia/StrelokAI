/**
 * Drag coefficient lookup (port of ballistics/drag_models.py).
 */
import { G1_DRAG, G7_DRAG } from "./dragTables";

export type DragTable = ReadonlyArray<readonly [number, number]>;
export type DragModel = "G1" | "G7";

export { G1_DRAG, G7_DRAG };

export function tableFor(model: DragModel): DragTable {
  return model === "G1" ? G1_DRAG : G7_DRAG;
}

/** Linear interpolation of Cd at a Mach number. */
export function dragCoefficient(mach: number, table: DragTable): number {
  if (mach <= table[0][0]) return table[0][1];
  const last = table[table.length - 1];
  if (mach >= last[0]) return last[1];
  for (let i = 0; i < table.length - 1; i++) {
    const [m0, cd0] = table[i];
    const [m1, cd1] = table[i + 1];
    if (m0 <= mach && mach <= m1) {
      const t = (mach - m0) / (m1 - m0);
      return cd0 + t * (cd1 - cd0);
    }
  }
  return last[1];
}

/** A custom drag curve (Mach, Cd) referenced to the circular cross-section. */
export type DragCurve = ReadonlyArray<readonly [number, number]>;

export function curveToDragTable(curve: DragCurve): DragTable {
  return [...curve].sort((a, b) => a[0] - b[0]);
}
