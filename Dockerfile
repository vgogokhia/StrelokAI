FROM node:24-alpine AS webbuild
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY data/bullet_library.json ../data/bullet_library.json
RUN npm run sync-data && npm run build

FROM node:24-alpine
WORKDIR /app/server
COPY server/package.json server/package-lock.json ./
RUN npm ci --omit=dev
COPY server/ ./
COPY --from=webbuild /web/dist /app/web/dist
ENV NODE_ENV=production PORT=8080 WEB_ROOT=/app/web/dist
EXPOSE 8080
CMD ["node", "start.mjs"]
