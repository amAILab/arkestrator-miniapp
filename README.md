# Arkestrator Mini App

Telegram Mini App / AI-пульт Никиты для связки Hermes ↔ OpenClaw/Клешня ↔ Home Assistant/Алиса ↔ STEP 3D Lab.

## Что это

Это не «ещё один чат», а операционный пульт:

- поставить задачу обычным языком;
- выбрать быстрый сценарий: заявки, сайт, 3D/STL, пост;
- видеть исполнителей: Геркулес, Клешня, Дом/Алиса;
- подтверждать рискованные действия в Approval Center;
- получать результаты: ссылки, файлы, скрины, commit/deploy status.

## Текущее состояние

- `index.html` — максимально простой Mini App: один экран «Что требует решения?», короткий перечень и кнопка «Подтвердить».
- `ROADMAP_50.md` — дорожная карта из 50 задач до сильного рабочего приложения.
- `PROGRESS_INTEGRATION.md` — как Hermes, Клешня, деплой и 3D-процессы пишут живой прогресс в нижний пульт.
- `scripts/progress_update.py` — локальный инструмент для создания задач и обновления процентов/событий.
- `app.py` — backend на Python stdlib без внешних зависимостей.
- `manifest.webmanifest`, `sw.js`, `icon.svg` — PWA shell.
- `start_public.sh` — локальный production-like запуск: backend + Cloudflare tunnel + автообновление Telegram Web App кнопки.
- `Dockerfile`, `railway.json`, `Procfile` — основа для деплоя на Railway/VPS/Fly.io.
- `PRODUCT_PLAN.md` — продуктовый план до идеальной версии.

## API

- `GET /healthz` — health-check для хостинга.
- `GET /api/status` — статус агентов и конфиг.
- `GET /api/tasks` — список задач.
- `POST /api/tasks` — создать задачу.
- `POST /api/route/openclaw` — передать задачу Клешне через `openclaw agent`.
- `GET /api/approvals` — pending approvals.
- `POST /api/approvals/resolve` — allow/deny.
- `GET /api/results` — лента результатов.

## Быстрый локальный запуск

```bash
cd /home/nikita/.hermes/team-ui-prototype
python3 app.py
```

Открыть:

```text
http://127.0.0.1:8791/
```

## Публичный временный запуск для Telegram

```bash
cd /home/nikita/.hermes/team-ui-prototype
./start_public.sh
```

Скрипт:

1. читает `/home/nikita/.hermes/.env`;
2. запускает backend;
3. запускает Cloudflare quick tunnel;
4. получает HTTPS URL;
5. обновляет кнопку **Аркестратор** в Telegram-боте;
6. сохраняет ссылку в `logs/current_url.txt`.

## Production env

```bash
ARKESTRATOR_PORT=8791
ARKESTRATOR_OWNER_ID=7260915527
ARKESTRATOR_OPENCLAW_SESSION_ID=3bd4f308-8e30-4bed-b9bb-04135e9f20a8
ARKESTRATOR_OPENCLAW_GROUP_ID=-1003920075284
ARKESTRATOR_BOT_TOKEN=...
```

Реальный `ARKESTRATOR_BOT_TOKEN` задавать только секретом хостинга, не коммитить.

## Как деплоить «как надо»

Лучший путь:

1. GitHub repo хранит код.
2. Railway/Fly.io/VPS запускает backend 24/7 из `Dockerfile`.
3. На хостинге заданы env/secrets.
4. На постоянный URL вешается Telegram Menu Button.
5. Позже JSON-хранилище заменить на SQLite/Postgres и добавить фонового worker.

## Безопасность

- Токены не лежат во frontend.
- POST-операции требуют Telegram `initData` при заданном `ARKESTRATOR_BOT_TOKEN`.
- OpenClaw получает ASCII-only payload, чтобы не ловить `Confusable Unicode characters`.
- Рискованные действия должны проходить через Approval Center.
