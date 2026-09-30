/**
 * Tiny i18n: English text is the key, Georgian lives in ./i18n-ka.ts.
 * `t()` reads reactive state, so templates re-render when the language changes.
 * Missing translations fall back to English.
 */
import { KA } from "./i18n-ka";

export type Lang = "en" | "ka";

function initial(): Lang {
  try {
    const saved = localStorage.getItem("bge_lang");
    if (saved === "en" || saved === "ka") return saved;
  } catch { /* storage blocked */ }
  const nav = (navigator.languages ?? [navigator.language]).map((l) => l?.toLowerCase() ?? "");
  if (nav.some((l) => l.startsWith("ka"))) return "ka";
  try { if (Intl.DateTimeFormat().resolvedOptions().timeZone === "Asia/Tbilisi") return "ka"; } catch { /* ignore */ }
  return "en";
}

export const i18n = $state({ lang: initial() });
if (typeof document !== "undefined") document.documentElement.lang = i18n.lang;

export function setLang(lang: Lang) {
  i18n.lang = lang;
  try { localStorage.setItem("bge_lang", lang); } catch { /* ignore */ }
  document.documentElement.lang = lang;
}

/** Translate `en`, then fill `{name}` placeholders from `vars`. */
export function t(en: string, vars?: Record<string, string | number>): string {
  let s = i18n.lang === "ka" ? KA[en] ?? en : en;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
  return s;
}
