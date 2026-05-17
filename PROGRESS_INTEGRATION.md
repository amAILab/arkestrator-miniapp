# Живой прогресс задач Arkestrator Mini App

Этот файл описывает, как Hermes, Клешня, деплой сайта и 3D-процессы могут писать настоящий прогресс в нижний пульт Mini App.

## Что уже есть

- Внутренний токен хранится локально в `data/internal_token` и не коммитится.
- Backend принимает внутренние обновления через заголовок:
  - `X-Arkestrator-Internal-Token: <token>`
- Endpoint обновления прогресса:
  - `POST /api/tasks/progress`
- Локальный инструмент:
  - `scripts/progress_update.py`

## Примеры

Создать задачу и сразу показать её в нижнем пульте:

```bash
scripts/progress_update.py \
  --create "Деплой сайта" \
  --executor hermes \
  --source deploy \
  --progress 10 \
  --status active \
  --note "начал публикацию"
```

Обновить существующую задачу:

```bash
scripts/progress_update.py \
  --task task-miniapp-mvp \
  --source hermes \
  --progress 72 \
  --status active \
  --note "проверяю интерфейс и публичную ссылку"
```

Завершить задачу:

```bash
scripts/progress_update.py \
  --task task-miniapp-mvp \
  --source hermes \
  --progress 100 \
  --status done \
  --note "готово и проверено"
```

## Источники

Рекомендуемые значения `--source`:

- `hermes` — Геркулес / Hermes;
- `kleshna` — Клешня / OpenClaw;
- `deploy` — публикация сайта или сервиса;
- `site` — проверка сайта;
- `3d` — 3D/STEP/STL-процесс.

## Безопасность

- `data/internal_token` находится в `.gitignore`.
- Токен не нужно писать в чат, коммиты или README.
- Публичные кнопки управления через Telegram Mini App продолжают требовать Telegram `initData`.
- Внутренний токен нужен только локальным агентам/скриптам на машине Никиты.
