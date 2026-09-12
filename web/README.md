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
Railway builds the root `Dockerfile` (Node build stage → Node account service) on every push to
`main` and serves `dist/` on `$PORT`. `robots.txt` / `sitemap.xml` live in `public/`.

Profiles are cached locally and synced to the signed-in account. Conditions and settings stay in `localStorage`. See `../server/README.md` for Google sign-in setup.
Weather uses Open-Meteo directly from the browser. `src/lib/license.ts` holds the license
token skeleton (`EVERYTHING_FREE = true` for now).
