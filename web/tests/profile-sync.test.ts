import { describe, it, expect } from 'vitest';
import { mergeProfiles, emptyProfiles, type ProfileData } from '../src/lib/profile-sync';
const data = (name: string): ProfileData => ({ rifles: [{ id: 'one', name }], ammo: [] });
describe('profile synchronization', () => {
  it('restores another device without introducing default profiles', () => expect(mergeProfiles(emptyProfiles(), emptyProfiles(), data('cloud'))).toEqual(data('cloud')));
  it('imports guest profiles alongside cloud profiles', () => {
    const guest = { rifles: [{ id: 'guest', name: 'Guest' }], ammo: [] };
    expect(mergeProfiles(emptyProfiles(), guest, data('Cloud')).rifles).toHaveLength(2);
  });
  it('preserves both concurrent edits', () => {
    const result = mergeProfiles(data('base'), data('local'), data('remote'));
    expect(result.rifles.map(p=>p.name)).toEqual(['remote','local (სხვა ვერსია)']);
    expect(new Set(result.rifles.map(p=>p.id)).size).toBe(2);
  });
  it('propagates deletion when the other device has not edited', () => expect(mergeProfiles(data('base'), emptyProfiles(), data('base'))).toEqual(emptyProfiles()));
  it('preserves edits conflicting with a deletion', () => expect(mergeProfiles(data('base'), data('edit'), emptyProfiles())).toEqual(data('edit')));
  it('applies an offline edit over an unchanged remote snapshot', () => expect(mergeProfiles(data('base'), data('offline'), data('base'))).toEqual(data('offline')));
});
