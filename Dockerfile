# ballistics.ge on Railway: static PWA served by Caddy.
FROM node:22-alpine AS webbuild
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY data/bullet_library.json ../data/bullet_library.json
RUN npm run sync-data && npm run build

FROM caddy:2-alpine
COPY --from=webbuild /web/dist /srv
COPY deploy/Caddyfile /etc/caddy/Caddyfile
ENV PORT=8080
EXPOSE 8080
