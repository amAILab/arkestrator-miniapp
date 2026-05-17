#!/usr/bin/env python3
"""Локальный обновитель прогресса Arkestrator Mini App.

Примеры:
  scripts/progress_update.py --task task-miniapp-mvp --progress 72 --note "проверяю интерфейс" --status active
  scripts/progress_update.py --create "Деплой сайта" --executor hermes --progress 10 --note "начал публикацию"

Токен берётся из data/internal_token или переменной ARKESTRATOR_INTERNAL_TOKEN.
URL берётся из logs/current_url.txt, ARKESTRATOR_URL или http://127.0.0.1:8791.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "data" / "internal_token"
URL_FILE = ROOT / "logs" / "current_url.txt"


def get_url() -> str:
    if os.getenv("ARKESTRATOR_URL"):
        return os.environ["ARKESTRATOR_URL"].strip().rstrip("/")
    if URL_FILE.exists():
        return URL_FILE.read_text(encoding="utf-8").strip().rstrip("/")
    return "http://127.0.0.1:8791"


def get_token() -> str:
    token = os.getenv("ARKESTRATOR_INTERNAL_TOKEN", "").strip()
    if token:
        return token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit("Нет data/internal_token. Запусти backend один раз или задай ARKESTRATOR_INTERNAL_TOKEN.")


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        get_url() + path,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Arkestrator-Internal-Token": get_token(),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Обновить живой прогресс задачи в Arkestrator Mini App")
    ap.add_argument("--task", help="ID существующей задачи")
    ap.add_argument("--create", help="создать новую задачу с таким названием")
    ap.add_argument("--executor", default="hermes", help="исполнитель: hermes, kleshna, site, 3d")
    ap.add_argument("--progress", type=int, default=0, help="процент 0..100")
    ap.add_argument("--status", default="active", help="active, paused, blocked, done, waiting")
    ap.add_argument("--note", default="прогресс обновлён", help="краткое событие")
    ap.add_argument("--source", help="источник события: hermes, kleshna, deploy, site, 3d")
    args = ap.parse_args()

    if args.create:
        result = post("/api/tasks", {
            "title": args.create,
            "executor": args.executor,
            "progress": args.progress,
            "body": args.note,
            "source": args.source or args.executor,
        })
        task = result["task"]
        if args.note or args.progress:
            result = post("/api/tasks/progress", {
                "id": task["id"],
                "progress": args.progress,
                "status": args.status,
                "note": args.note,
                "source": args.source or args.executor,
            })
    elif args.task:
        result = post("/api/tasks/progress", {
            "id": args.task,
            "progress": args.progress,
            "status": args.status,
            "note": args.note,
            "source": args.source or args.executor,
        })
    else:
        ap.error("нужно --task или --create")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
