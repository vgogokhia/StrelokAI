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
fi
exec streamlit run app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.enableCORS false \
  --server.enableXsrfProtection true
