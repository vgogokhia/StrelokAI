# ballistics.ge on Railway: one container serves the PWA (web/dist) at /
# and the legacy Streamlit app at /old, both behind Caddy on $PORT.

# --- stage 1: build the PWA -------------------------------------------------
FROM node:22-alpine AS webbuild
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY data/bullet_library.json ../data/bullet_library.json
RUN npm run sync-data && npm run build

# --- stage 2: runtime --------------------------------------------------------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
COPY --from=caddy:2 /usr/bin/caddy /usr/bin/caddy
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
COPY --from=webbuild /web/dist /app/web/dist
ENV PORT=8501
EXPOSE 8501
RUN chmod +x /app/deploy/start.sh
CMD ["/app/deploy/start.sh"]
