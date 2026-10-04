import { describe, it, expect } from "vitest";
import { KA } from "../src/lib/i18n-ka";
import { FR } from "../src/lib/i18n-fr";

const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
/** Every literal t("...") / t('...') key used by the app shell and components. */
function usedKeys(): string[] {
  const sources = import.meta.glob(["../src/components/*.svelte", "../src/app/App.svelte"], { query: "?raw", import: "default", eager: true }) as Record<string, string>;
  const keys = new Set<string>();
  for (const src of Object.values(sources)) {
    for (const m of src.matchAll(/\bt\(\s*"((?:[^"\\]|\\.)*)"/g)) keys.add(JSON.parse(`"${m[1]}"`));
    for (const m of src.matchAll(/\bt\(\s*'((?:[^'\\]|\\.)*)'/g)) keys.add(m[1].replace(/\\'/g, "'"));
  }
  return [...keys];
}

describe("translations", () => {
  for (const [name, dict] of [["Georgian", KA], ["French", FR]] as const) {
    it(`${name} covers every UI string`, () => {
      expect(usedKeys().filter((k) => !(k in dict))).toEqual([]);
    });
    it(`${name} keeps every {placeholder}`, () => {
      expect(Object.entries(dict).filter(([k, v]) => placeholders(k).join() !== placeholders(v).join()).map(([k]) => k)).toEqual([]);
    });
  }
  it("Georgian and French have the same keys", () => {
    expect(Object.keys(FR).sort()).toEqual(Object.keys(KA).sort());
  });
});
