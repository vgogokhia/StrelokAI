import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { KA } from "../src/lib/i18n-ka";
import { FR } from "../src/lib/i18n-fr";

const placeholders = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
/** Every literal t("...") / t('...') key used by the app shell and components. */
function usedKeys(): string[] {
  const dir = new URL("../src/components/", import.meta.url);
  const files = [new URL("../src/app/App.svelte", import.meta.url), ...readdirSync(dir).map((f) => new URL(f, dir))];
  const keys = new Set<string>();
  for (const f of files) {
    const src = readFileSync(f, "utf8");
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
