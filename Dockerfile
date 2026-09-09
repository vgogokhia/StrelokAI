# StrelokAI on Railway / any Docker host.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Railway injects $PORT; default for local docker run.
ENV PORT=8501
EXPOSE 8501

RUN chmod +x /app/deploy/start.sh
CMD ["/app/deploy/start.sh"]
