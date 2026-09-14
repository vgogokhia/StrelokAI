# ballistics.ge on Railway: static PWA + feedback API in one small Node server.
FROM node:22-alpine AS webbuild
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY data/bullet_library.json ../data/bullet_library.json
RUN npm run sync-data && npm run build

FROM node:22-alpine
WORKDIR /app
COPY server/ ./server/
COPY --from=webbuild /web/dist ./web/dist
ENV PORT=8080 DATA_DIR=/data NODE_ENV=production
EXPOSE 8080
CMD ["node", "server/server.mjs"]
