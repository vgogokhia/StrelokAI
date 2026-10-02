import { defineConfig } from "vite";
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
const pkg = JSON.parse(readFileSync(new URL("./package.json", import.meta.url), "utf8"));
const sha = (process.env.RAILWAY_GIT_COMMIT_SHA || process.env.SOURCE_COMMIT || (() => { try { return execSync("git rev-parse HEAD").toString(); } catch { return "dev"; } })()).trim().slice(0, 7);
const APP_VERSION = `${pkg.version}+${sha}`;
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { VitePWA } from "vite-plugin-pwa";
import type { Plugin } from "vite";

/** Inline the (small) app stylesheet into index.html so it doesn't block the first paint as a separate request. */
const inlineCss = (): Plugin => ({
  name: "inline-css",
  apply: "build",
  enforce: "post",
  generateBundle(_, bundle) {
    const html = bundle["index.html"];
    if (!html || html.type !== "asset") return;
    let src = String(html.source);
    for (const [name, chunk] of Object.entries(bundle)) {
      if (chunk.type !== "asset" || !name.endsWith(".css") || chunk.source.length > 20000) continue;
      const tag = new RegExp(`<link rel="stylesheet"[^>]*href="/${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"[^>]*>`);
      if (!tag.test(src)) continue;
      src = src.replace(tag, () => `<style>${String(chunk.source)}</style>`);
      delete bundle[name];
    }
    html.source = src;
  },
});

export default defineConfig({
  define: { __APP_VERSION__: JSON.stringify(APP_VERSION) },
  plugins: [
    inlineCss(),
    svelte(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/ballistics-b-192.png", "icons/ballistics-b-512.png", "icons/ballistics-b-16.png", "icons/ballistics-b-32.png", "icons/ballistics-b-180.png", "brand/ballistics-logo-480.webp", "brand/ballistics-logo-960.webp", "robots.txt", "sitemap.xml"],
      manifest: {
        name: "ballistics.ge — Ballistic Calculator",
        short_name: "ballistics.ge",
        description: "Elevation and windage in MRAD/MOA for any cartridge. Works offline.",
        theme_color: "#121212",
        background_color: "#121212",
        display: "standalone",
        orientation: "portrait",
        start_url: "/",
        lang: "en",
        icons: [
          { src: "icons/ballistics-b-192.png", sizes: "192x192", type: "image/png" },
          { src: "icons/ballistics-b-512.png", sizes: "512x512", type: "image/png", purpose: "any maskable" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,png,svg,json,woff2}"],
        globIgnores: ["brand/og-*.png", "brand/ballistics-logo.png", "ballistics/**", "glossary/**", "ka/**", "pricing/**", "terms/**", "privacy/**", "refunds/**"],
        navigateFallback: "/index.html",
        // The app shell answers only "/" (with any query). Every other page is a real static file.
        navigateFallbackAllowlist: [/^\/(?:index\.html)?(?:\?.*)?$/],
        navigateFallbackDenylist: [/^\/admin/, /^\/(?:api|auth)(?:\/|$)/],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.open-meteo\.com\/.*/i,
            handler: "NetworkFirst",
            options: { cacheName: "weather", expiration: { maxEntries: 10, maxAgeSeconds: 3600 } },
          },
        ],
      },
    }),
  ],
  server: { proxy: { "/api": "http://localhost:8080", "/auth": "http://localhost:8080" } },
  build: { target: "es2020", sourcemap: false },
  test: { globals: true, include: ["tests/**/*.test.ts"] },
});
