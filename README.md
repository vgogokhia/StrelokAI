# ballistics.ge — Ballistic Calculator

Offline-capable ballistic calculator for precision shooters: **https://ballistics.ge**

- `web/` — the app: TypeScript solver + Svelte 5 PWA (see `web/README.md`).
- `ballistics/`, `tests/` — the original Python physics engine, kept as the reference the
  TypeScript port is verified against (`pytest`, `web/tests/reference.test.ts`).
- `data/bullet_library.json` — bullet / factory-ammo library (bundled into the app).
- `Dockerfile`, `deploy/Caddyfile`, `railway.json` — Railway deployment (static, Caddy).
- `deploy/SEO.md` — Search Console checklist.

```bash
cd web && npm install && npm run dev     # app
pip install -r requirements.txt && pytest # reference engine tests
```
