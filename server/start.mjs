import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { app, database } from './app.mjs';
const production = process.env.NODE_ENV === 'production';
const origin = process.env.PUBLIC_ORIGIN || 'http://localhost:8080';
const path = process.env.ACCOUNT_DB_PATH || './data/accounts.sqlite';
if (production && (!process.env.ACCOUNT_DB_PATH || !origin.startsWith('https://') || !process.env.RAILWAY_VOLUME_MOUNT_PATH)) {
  throw new Error('Production requires PUBLIC_ORIGIN (HTTPS), ACCOUNT_DB_PATH and a persistent Railway volume.');
}
if (production && !resolve(path).startsWith(resolve(process.env.RAILWAY_VOLUME_MOUNT_PATH) + '/')) throw new Error('Account database must be inside the persistent volume.');
mkdirSync(dirname(path), { recursive: true });
const db = database(path);
const server = app({ db, origin, clientId: process.env.GOOGLE_CLIENT_ID, clientSecret: process.env.GOOGLE_CLIENT_SECRET, webRoot: process.env.WEB_ROOT || '../web/dist' });
server.listen(Number(process.env.PORT || 8080), '0.0.0.0');
process.on('SIGTERM', () => server.close(() => { db.close(); process.exit(0); }));
