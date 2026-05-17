# Arkestrator Mini App MVP

Локальный рабочий MVP Telegram Mini App / AI-пульта для связки Hermes ↔ OpenClaw/Клешня ↔ другие боты.

## Что уже есть

- `index.html` — mobile-first UI, похожий на Telegram Mini App.
- `app.py` — backend на Python stdlib без внешних зависимостей.
- API:
  - `GET /api/status` — статус агентов и конфиг.
  - `GET /api/tasks` — список задач.
  - `POST /api/tasks` — создать задачу.
  - `POST /api/route/openclaw` — передать задачу Клешне через `openclaw agent`.
  - `GET /api/approvals` — pending approvals.
  - `POST /api/approvals/resolve` — allow/deny.
  - `GET /api/results` — лента результатов.
- Локальное JSON-хранилище: `data/state.json`.
- Telegram Mini App auth-заготовка: если задан `ARKESTRATOR_BOT_TOKEN`, backend проверяет `initData` и owner id.

## Запуск локально

```bash
cd /home/nikita/.hermes/team-ui-prototype
python3 app.py
```

Открыть:

```text
http://127.0.0.1:8791/
```

## Env настройки

```bash
export ARKESTRATOR_OWNER_ID=7260915527
export ARKESTRATOR_OPENCLAW_SESSION_ID=3bd4f308-8e30-4bed-b9bb-04135e9f20a8
export ARKESTRATOR_OPENCLAW_GROUP_ID=-1003920075284
# Для настоящей Telegram Mini App проверки initData:
export ARKESTRATOR_BOT_TOKEN='...'
```

Без `ARKESTRATOR_BOT_TOKEN` backend работает в dev-режиме только на `127.0.0.1`.

## Безопасность

- Токены не лежат в frontend.
- Реальные действия идут через backend.
- `openclaw agent` получает ASCII-only payload, чтобы не ловить `Confusable Unicode characters`.
- Публичный доступ пока не включён. Для Telegram Mini App нужен HTTPS endpoint.

## Что нужно для публикации в Telegram

1. Поднять backend на HTTPS: VPS/Railway/Cloudflare Tunnel/локальный ПК + tunnel.
2. Задать `ARKESTRATOR_BOT_TOKEN` на сервере.
3. Через BotFather добавить кнопку Menu Button / Web App URL.
4. Проверить `initData` внутри Telegram WebView.
5. Добавить постоянное хранилище SQLite вместо JSON, если нагрузка вырастет.
