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
Railway builds the root `Dockerfile` on every push to `main`: `server/server.mjs` (Node, no
dependencies) serves `dist/`, takes feedback at `POST /api/feedback` (with optional screenshot)
and shows the inbox at `/admin`. Set `ADMIN_TOKEN` in Railway variables to enable the inbox and
mount a Volume at `/data` so feedback survives redeploys. `robots.txt` / `sitemap.xml` live in `public/`.

State (profiles, conditions, settings) lives in `localStorage`; nothing is sent to a server.
Weather uses Open-Meteo directly from the browser. `src/lib/license.ts` holds the license
token skeleton (`EVERYTHING_FREE = true` for now).
