/**
 * Tiny i18n: English text is the key; Georgian lives in ./i18n-ka.ts, French in ./i18n-fr.ts.
 * `t()` reads reactive state, so templates re-render when the language changes.
 * Missing translations fall back to English.
 */
import { KA } from "./i18n-ka";
import { FR } from "./i18n-fr";

export type Lang = "en" | "ka" | "fr";
const DICTS: Record<Lang, Record<string, string> | null> = { en: null, ka: KA, fr: FR };
/** Languages offered in the UI, with their own names. */
export const LANGS: Array<{ code: Lang; label: string; short: string }> = [
  { code: "en", label: "English", short: "EN" },
  { code: "ka", label: "ქართული", short: "ქარ" },
  { code: "fr", label: "Français", short: "FR" },
];

const isLang = (v: unknown): v is Lang => v === "en" || v === "ka" || v === "fr";

function initial(): Lang {
  // A link like ballistics.ge/fr (redirected to /?lang=fr) or /?lang=fr picks the language and remembers it.
  try {
    const q = new URLSearchParams(location.search);
    const wanted = q.get("lang")?.toLowerCase();
    if (q.has("lang")) {
      q.delete("lang");
      history.replaceState(null, "", location.pathname + (q.size ? `?${q}` : "") + location.hash);
    }
    if (isLang(wanted)) { try { localStorage.setItem("bge_lang", wanted); } catch { /* ignore */ } return wanted; }
  } catch { /* no window */ }
  try {
    const saved = localStorage.getItem("bge_lang");
    if (isLang(saved)) return saved;
  } catch { /* storage blocked */ }
  const nav = (navigator.languages ?? [navigator.language]).map((l) => l?.toLowerCase() ?? "");
  if (nav.some((l) => l.startsWith("ka"))) return "ka";
  if (nav[0]?.startsWith("fr")) return "fr";
  try { if (Intl.DateTimeFormat().resolvedOptions().timeZone === "Asia/Tbilisi") return "ka"; } catch { /* ignore */ }
  return "en";
}

export const i18n = $state({ lang: initial() });
if (typeof document !== "undefined") { document.documentElement.lang = i18n.lang; document.documentElement.setAttribute("translate", "no"); }

export function setLang(lang: Lang) {
  i18n.lang = lang;
  try { localStorage.setItem("bge_lang", lang); } catch { /* ignore */ }
  document.documentElement.lang = lang;
}

/** Translate `en`, then fill `{name}` placeholders from `vars`. */
export function t(en: string, vars?: Record<string, string | number>): string {
  let s = DICTS[i18n.lang]?.[en] ?? en;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k: string) => (k in vars ? String(vars[k]) : m));
  return s;
}
