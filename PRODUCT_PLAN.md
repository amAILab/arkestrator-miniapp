# Аркестратор — продуктовый план до идеала

Цель: сделать Telegram Mini App не демкой, а главным AI-пультом Никиты: уровень ощущения — Linear/Raycast/Notion/ChatGPT mobile, но под STEP 3D Lab.

## Что значит «идеальное приложение»

1. **Один главный экран** — задача, быстрые сценарии, статусы агентов, approvals, результаты.
2. **Никакого терминального шума** — только понятные карточки: что делаем, кто делает, что нужно подтвердить.
3. **Голос-first** — голос → текст → карточка задачи → выбран исполнитель.
4. **Безопасность** — удаление, deploy, публикации, отправка клиентам, деньги и credentials только через Approval Center.
5. **Результат с артефактами** — ссылка, файл, скрин, commit, message id, deploy status.
6. **Постоянный backend** — не временный tunnel, а домен/VPS/Railway.

## Архитектура v1

- Telegram bot: точка входа, Menu Button/Web App.
- Mini App frontend: `index.html`, PWA shell, Telegram WebApp SDK.
- Backend: `app.py` или будущий FastAPI сервис.
- State: JSON сейчас, SQLite/Postgres потом.
- Workers:
  - Hermes/Геркулес: диспетчер, память, статусы.
  - OpenClaw/Клешня: сайт, код, деплой, 3D/STL.
  - Home Assistant/Алиса: озвучка и умный дом.

## Деплой как надо

### Временный режим

`./start_public.sh` поднимает backend + Cloudflare quick tunnel + обновляет Telegram кнопку.

### Постоянный режим

1. GitHub repo — источник кода.
2. Railway/Fly.io/VPS — backend 24/7.
3. Переменные окружения секретами:
   - `ARKESTRATOR_BOT_TOKEN`
   - `ARKESTRATOR_OWNER_ID`
   - OpenClaw routing env
4. Домен:
   - `arkestrator.step3d.ai` или аналог.
5. BotFather / Telegram API — Menu Button на постоянный URL.

## Следующие продуктовые итерации

- [ ] SQLite вместо JSON.
- [ ] Реальная очередь задач с `queued/running/blocked/done`.
- [ ] Фоновый worker для долгих задач, чтобы UI не зависал.
- [ ] Push/status notifications в Telegram.
- [ ] Голосовая кнопка/микрофон внутри Mini App.
- [ ] Files hub: STEP/STL/PDF/screenshots/deploy URLs.
- [ ] Approval Center с аудит-логом.
- [ ] Роли и permissions.
- [ ] Красивый onboarding «Никита → Аркестратор → Клешня».
