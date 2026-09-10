# ballistics.ge — PWA (web/)

Offline-capable ballistic calculator. TypeScript port of the Python engine in `../ballistics`
(`src/core`, verified against it by `tests/reference.test.ts`), Svelte 5 UI, vite-plugin-pwa.

```bash
npm install
npm run dev        # http://localhost:5173
npm test           # core vs Python reference (17 tests)
npm run check      # svelte-check
npm run build      # dist/  (static; deploy anywhere)
npm run sync-data  # refresh src/data/bullets.json from ../data/bullet_library.json
```

## Deploy (Cloudflare Pages, free)
1. Cloudflare → Workers & Pages → Create → Pages → Connect to Git → `vgogokhia/StrelokAI`.
2. Build settings: **Root directory** `web`, **Build command** `npm ci && npm run build`,
   **Build output** `dist`, branch `main`. Environment variable `NODE_VERSION=22`.
3. Custom domain: `app.ballistics.ge` first (CNAME to the pages.dev host, Cloudflare adds it
   automatically). When it replaces the Streamlit app, move `ballistics.ge` here and put
   the Streamlit app on `old.ballistics.ge`.

State (profiles, conditions, settings) lives in `localStorage`; nothing is sent to a server.
Weather uses Open-Meteo directly from the browser. `src/lib/license.ts` holds the license
token skeleton (`EVERYTHING_FREE = true` for now).
