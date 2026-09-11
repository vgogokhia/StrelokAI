# Accounts and profile sync

Node 24 service with Google OpenID Connect and SQLite on a persistent volume.
The existing static PWA and blog are served by the same service. No passwords or
Google refresh/access tokens are stored. Sessions last 30 days in HttpOnly cookies.
Only profile collections are synced; live conditions and device preferences stay local.

## Production configuration (required before merging/deploying)

1. Attach a Railway persistent volume to **StrelokAI** at `/data`, with one replica.
   Enable volume backups. The service deliberately refuses production startup without
   a volume so user accounts cannot be stored on an ephemeral container filesystem.
2. Set `PUBLIC_ORIGIN=https://ballistics.ge` and
   `ACCOUNT_DB_PATH=/data/accounts.sqlite`. Railway supplies `RAILWAY_VOLUME_MOUNT_PATH`.
3. In Google Cloud create an OAuth client of type **Web application**, configure the
   consent screen, and add the exact authorized redirect URI:
   `https://ballistics.ge/auth/google/callback`.
   Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` as Railway service variables.
   Never put the secret in the frontend, repository, chat, or logs. Publish the consent
   screen for public users (a testing consent screen only allows listed test users).
4. Deploy this commit. Verify a real Google login in two independent browser profiles,
   edit a profile, check the second device, sign out/in, then test an offline edit and
   reconnect. Verify volume persistence across redeployment before selling accounts.

Google documentation: https://developers.google.com/identity/openid-connect/openid-connect

## Local development

`npm ci` in this directory, `npm ci && npm run build` in `web`, then `npm start`
from this directory. Defaults: port 8080, localhost origin, local `data/accounts.sqlite`.
For real local Google login register `http://localhost:8080/auth/google/callback`.
When using Vite's proxy, set `PUBLIC_ORIGIN=http://localhost:5173` and register that
callback instead. `npm test` uses an isolated in-memory database and a mock Google
adapter. No production data or Google credentials are used in tests.

## Data guarantees and limits

- The authenticated Google subject owns every database row; requests must also name
  the expected account to prevent a tab from uploading to a newly switched session.
- Writes require the exact origin and a revision match. Concurrent changes merge on
  the client against its last synchronized snapshot. Conflicting edits keep both
  records, with the local copy marked `(სხვა ვერსია)`. An edit wins over a concurrent
  deletion, while an uncontested deletion propagates.
- The original guest snapshot stays on the device and is imported into the first
  account once. Account caches use separate storage keys. Logout revokes the session
  and restores guest profiles. Local unsent account changes survive logout/re-login.
- Sync runs after edits, every 15 seconds, on focus, and on reconnect while the app is
  open. The service worker never intercepts authentication or API routes.
- A maximum of 500 records per collection, 16 KB per record, and 1 MB per request is
  accepted. A full Google login and device/browser end-to-end test still requires the
  production OAuth setup above; mock tests do not establish that live consent works.
- Paid billing and entitlement enforcement are separate work; this change does not
  enable charging users or change the current free-feature flag.
