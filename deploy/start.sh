#!/bin/sh
# Streamlit reads secrets only from .streamlit/secrets.toml. On Railway we
# keep the whole TOML in one variable (STREAMLIT_SECRETS_TOML) and write it
# out at start-up, so nothing secret is baked into the image.
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"
mkdir -p .streamlit
if [ -n "$STREAMLIT_SECRETS_TOML" ]; then
  printf '%s\n' "$STREAMLIT_SECRETS_TOML" > .streamlit/secrets.toml
  echo "secrets: wrote .streamlit/secrets.toml ($(wc -l < .streamlit/secrets.toml) lines, sections: $(grep -c '^\[' .streamlit/secrets.toml))"
else
  echo "secrets: STREAMLIT_SECRETS_TOML is not set - running without secrets"
fi

# Streamlit on an internal port under /old; Caddy fronts everything on $PORT.
streamlit run app.py \
  --server.port 8501 --server.address 127.0.0.1 --server.baseUrlPath old \
  --server.headless true --server.enableCORS false --server.enableXsrfProtection true &

exec caddy run --config "$APP_DIR/deploy/Caddyfile" --adapter caddyfile
