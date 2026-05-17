FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ARKESTRATOR_PORT=8791

WORKDIR /app
COPY app.py index.html manifest.webmanifest sw.js icon.svg README.md ./

RUN mkdir -p /app/data
EXPOSE 8791
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python - <<'PY'
import os, urllib.request
port=os.getenv('ARKESTRATOR_PORT','8791')
urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz', timeout=3).read()
PY

CMD ["python", "app.py"]
