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

## Deploy
Built inside the main `Dockerfile` (stage 1) and served by Caddy on Railway together with
the legacy Streamlit app: `ballistics.ge/` = PWA, `ballistics.ge/old/` = Streamlit.
No extra service needed — push to `main` and Railway rebuilds.

State (profiles, conditions, settings) lives in `localStorage`; nothing is sent to a server.
Weather uses Open-Meteo directly from the browser. `src/lib/license.ts` holds the license
token skeleton (`EVERYTHING_FREE = true` for now).
