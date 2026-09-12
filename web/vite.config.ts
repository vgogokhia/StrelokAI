import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    svelte(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icons/ballistics-b-192.png", "icons/ballistics-b-512.png", "icons/ballistics-b-16.png", "icons/ballistics-b-32.png", "icons/ballistics-b-180.png", "brand/ballistics-logo.png", "robots.txt", "sitemap.xml"],
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
        navigateFallback: "/index.html",
        navigateFallbackDenylist: [/^\/blog(?:\/|$)/, /^\/(?:api|auth)(?:\/|$)/],
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
