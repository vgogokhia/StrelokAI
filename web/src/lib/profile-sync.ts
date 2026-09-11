export interface RecordProfile { id: string; name: string; [key: string]: unknown }
export interface ProfileData { rifles: RecordProfile[]; ammo: RecordProfile[] }
export const emptyProfiles = (): ProfileData => ({ rifles: [], ammo: [] });
const equal = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);
/** Three-way record merge. Preserve concurrent edits as separate profiles; do not lose data. */
export function mergeProfiles(base: ProfileData, local: ProfileData, remote: ProfileData): ProfileData {
  const result = emptyProfiles();
  for (const kind of ['rifles', 'ammo'] as const) {
    const b = new Map(base[kind].map(p => [p.id, p]));
    const l = new Map(local[kind].map(p => [p.id, p]));
    const r = new Map(remote[kind].map(p => [p.id, p]));
    for (const id of new Set([...l.keys(), ...r.keys()])) {
      const before = b.get(id), left = l.get(id), right = r.get(id);
      if (equal(left, right)) { if (left) result[kind].push(left); }
      else if (equal(left, before)) { if (right) result[kind].push(right); }
      else if (equal(right, before)) { if (left) result[kind].push(left); }
      else {
        if (right) result[kind].push(right);
        if (left) result[kind].push(right ? { ...left, id: crypto.randomUUID(), name: `${left.name.slice(0,260)} (სხვა ვერსია)` } : left);
      }
    }
  }
  return result;
}
