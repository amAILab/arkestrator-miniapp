#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PORT="${ARKESTRATOR_PORT:-8791}"
OWNER_ID="${ARKESTRATOR_OWNER_ID:-7260915527}"
ENV_FILE="${HERMES_ENV:-/home/nikita/.hermes/.env}"
CLOUDFLARED="${CLOUDFLARED:-/home/nikita/.local/bin/cloudflared}"
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && [ -z "${ARKESTRATOR_BOT_TOKEN:-}" ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN или ARKESTRATOR_BOT_TOKEN не найден в $ENV_FILE" >&2
  exit 1
fi
export ARKESTRATOR_BOT_TOKEN="${ARKESTRATOR_BOT_TOKEN:-$TELEGRAM_BOT_TOKEN}"
export ARKESTRATOR_OWNER_ID="$OWNER_ID"
export ARKESTRATOR_PORT="$PORT"

# Stop old local app/cloudflared for this port only.
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "cloudflared tunnel --url http://127.0.0.1:$PORT" 2>/dev/null || true
sleep 1

python3 -m py_compile app.py
nohup python3 app.py > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

python3 - <<PY
import time, urllib.request, sys
url='http://127.0.0.1:$PORT/api/status'
for _ in range(40):
    try:
        with urllib.request.urlopen(url, timeout=1.5) as r:
            if r.status == 200:
                print('backend_ok')
                sys.exit(0)
    except Exception:
        time.sleep(0.5)
print('backend_failed')
sys.exit(1)
PY

if [ ! -x "$CLOUDFLARED" ]; then
  echo "ERROR: cloudflared не найден: $CLOUDFLARED" >&2
  exit 1
fi

nohup "$CLOUDFLARED" tunnel --url "http://127.0.0.1:$PORT" --no-autoupdate > "$LOG_DIR/cloudflared.log" 2>&1 &
TUNNEL_PID=$!

URL=""
for i in $(seq 1 80); do
  URL=$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG_DIR/cloudflared.log" | tail -1 || true)
  if [ -n "$URL" ]; then break; fi
  sleep 0.5
done

if [ -z "$URL" ]; then
  echo "ERROR: не удалось получить Cloudflare URL. Лог: $LOG_DIR/cloudflared.log" >&2
  exit 1
fi
URL="${URL%/}/"
printf '%s\n' "$URL" > "$LOG_DIR/current_url.txt"

APP_URL="$URL" OWNER_ID="$OWNER_ID" python3 - <<'PY'
import json, os, urllib.parse, urllib.request
url=os.environ['APP_URL']
token=os.environ.get('ARKESTRATOR_BOT_TOKEN')
owner=os.environ['OWNER_ID']
base=f'https://api.telegram.org/bot{token}'
button=json.dumps({'type':'web_app','text':'Аркестратор','web_app':{'url':url}}, ensure_ascii=False)
def post(method, payload):
    req=urllib.request.Request(base+'/'+method, data=urllib.parse.urlencode(payload).encode())
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())
for payload in [{'chat_id': owner, 'menu_button': button}, {'menu_button': button}]:
    res=post('setChatMenuButton', payload)
    if not res.get('ok'):
        raise SystemExit(res)
print('telegram_menu_updated')
PY

cat <<EOF
OK: Arkestrator Mini App запущен
URL: $URL
backend_pid: $BACKEND_PID
tunnel_pid: $TUNNEL_PID
logs: $(pwd)/$LOG_DIR
EOF
