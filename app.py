#!/usr/bin/env python3
"""Arkestrator Mini App MVP backend.

Local-first backend for Telegram Mini App prototype:
- serves static UI;
- stores tasks/approvals/results in JSON;
- verifies Telegram WebApp initData when ARKESTRATOR_BOT_TOKEN is set;
- can route safe ASCII-only payloads to the known OpenClaw group session.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shlex
import subprocess
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "index.html"
STATIC_FILES = {
    "/manifest.webmanifest": (ROOT / "manifest.webmanifest", "application/manifest+json; charset=utf-8"),
    "/sw.js": (ROOT / "sw.js", "application/javascript; charset=utf-8"),
    "/icon.svg": (ROOT / "icon.svg", "image/svg+xml; charset=utf-8"),
}
DATA_DIR = ROOT / "data"
STATE_FILE = DATA_DIR / "state.json"
OPENCLAW_SESSION_ID = os.getenv("ARKESTRATOR_OPENCLAW_SESSION_ID", "3bd4f308-8e30-4bed-b9bb-04135e9f20a8")
OPENCLAW_GROUP_ID = os.getenv("ARKESTRATOR_OPENCLAW_GROUP_ID", "-1003920075284")
OWNER_ID = os.getenv("ARKESTRATOR_OWNER_ID", "7260915527")
BOT_TOKEN = os.getenv("ARKESTRATOR_BOT_TOKEN", "")
PORT = int(os.getenv("ARKESTRATOR_PORT", "8791"))

DEFAULT_STATE: dict[str, Any] = {
    "tasks": [
        {
            "id": "task-arkestrator-visible-replies",
            "title": "Починить видимые ответы Аркестратора",
            "body": "automatic mode · проверено сообщением #208",
            "executor": "kleshna",
            "status": "done",
            "createdAt": int(time.time()),
        },
        {
            "id": "task-miniapp-mvp",
            "title": "Mini App: AI-пульт для Никиты",
            "body": "Локальный backend + API + UI",
            "executor": "hermes",
            "status": "active",
            "createdAt": int(time.time()),
        },
    ],
    "approvals": [
        {
            "id": "approval-demo-deploy",
            "title": "Демо: подтверждение опасного действия",
            "risk": "deploy / публикация / удаление требуют явного OK",
            "status": "pending",
            "createdAt": int(time.time()),
        }
    ],
    "results": [
        {"id": "result-ui", "title": "Прототип UI создан", "url": "/", "kind": "file", "createdAt": int(time.time())}
    ],
}


def now() -> int:
    return int(time.time())


def read_state() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        write_state(DEFAULT_STATE)
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        backup = STATE_FILE.with_suffix(f".broken-{now()}.json")
        STATE_FILE.rename(backup)
        write_state(DEFAULT_STATE)
        return dict(DEFAULT_STATE)


def write_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(STATE_FILE)


def json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def text_response(handler: BaseHTTPRequestHandler, text: str, status: int = 200, ctype: str = "text/plain; charset=utf-8") -> None:
    raw = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def verify_init_data(init_data: str) -> tuple[bool, str]:
    """Verify Telegram Mini App initData if bot token is configured.

    In local dev without ARKESTRATOR_BOT_TOKEN we allow access, but expose authMode=dev.
    """
    if not BOT_TOKEN:
        return True, "dev-no-token"
    parsed = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
    data = dict(parsed)
    received_hash = data.pop("hash", "")
    if not received_hash:
        return False, "missing-hash"
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        return False, "bad-hash"
    user_raw = data.get("user", "{}")
    try:
        user = json.loads(user_raw)
        if OWNER_ID and str(user.get("id")) != OWNER_ID:
            return False, "not-owner"
    except Exception:
        return False, "bad-user"
    return True, "telegram-verified"


def require_auth(handler: BaseHTTPRequestHandler) -> tuple[bool, str]:
    init_data = handler.headers.get("X-Telegram-Init-Data", "")
    ok, reason = verify_init_data(init_data)
    if not ok:
        json_response(handler, {"ok": False, "error": "unauthorized", "reason": reason}, 401)
    return ok, reason


def safe_ascii_payload(text: str) -> str:
    """Keep shell payload ASCII-only to avoid OpenClaw confusable-Unicode approval warnings."""
    text = text.strip()
    translit = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z",
        "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    out = []
    for ch in text:
        low = ch.lower()
        val = translit.get(low)
        if val is not None:
            out.append(val.upper() if ch.isupper() else val)
        elif ord(ch) < 128 and ch not in "`$\\\x00\n\r":
            out.append(ch)
        elif ch in "\n\r":
            out.append(" ")
        else:
            out.append("?")
    clean = re.sub(r"\s+", " ", "".join(out)).strip()
    return clean[:1200]


def route_openclaw(message: str) -> dict[str, Any]:
    payload = f"[Hercules to Kleshna] {safe_ascii_payload(message)}"
    cmd = [
        "openclaw", "agent",
        "--session-id", OPENCLAW_SESSION_ID,
        "--message", payload,
        "--deliver",
        "--reply-channel", "telegram",
        "--reply-to", OPENCLAW_GROUP_ID,
        "--timeout", "240",
        "--json",
    ]
    started = time.time()
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=270)
    duration_ms = int((time.time() - started) * 1000)
    try:
        parsed = json.loads(proc.stdout) if proc.stdout.strip() else None
    except Exception:
        parsed = None
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "durationMs": duration_ms,
        "safePayload": payload,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-2000:],
        "json": parsed,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "ArkestratorMiniApp/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in ("/", "/index.html"):
            if not STATIC.exists():
                return text_response(self, "index.html not found", 404)
            html = STATIC.read_text(encoding="utf-8")
            return text_response(self, html, 200, "text/html; charset=utf-8")
        if path in STATIC_FILES:
            file_path, content_type = STATIC_FILES[path]
            if not file_path.exists():
                return text_response(self, "asset not found", 404)
            return text_response(self, file_path.read_text(encoding="utf-8"), 200, content_type)
        if path in ("/healthz", "/api/health"):
            return json_response(self, {"ok": True, "service": "arkestrator-miniapp", "time": now()})
        if path == "/api/status":
            ok, auth_mode = verify_init_data(self.headers.get("X-Telegram-Init-Data", ""))
            state = read_state()
            return json_response(self, {
                "ok": True,
                "auth": {"authorized": ok, "mode": auth_mode},
                "config": {
                    "ownerId": OWNER_ID,
                    "openclawGroupId": OPENCLAW_GROUP_ID,
                    "openclawSessionId": OPENCLAW_SESSION_ID,
                    "botTokenConfigured": bool(BOT_TOKEN),
                },
                "counts": {"tasks": len(state.get("tasks", [])), "approvals": len(state.get("approvals", [])), "results": len(state.get("results", []))},
                "agents": [
                    {"id": "hermes", "name": "Геркулес / Hermes", "status": "online", "role": "диспетчер, память, Telegram"},
                    {"id": "kleshna", "name": "Клешня / OpenClaw", "status": "online", "role": "код, деплой, 3D/STEP/STL"},
                    {"id": "home", "name": "Дом / Алиса", "status": "ready", "role": "озвучка и Home Assistant"},
                ],
            })
        if path == "/api/tasks":
            # Read endpoints stay visible for the dashboard shell and public preview.
            # Mutating endpoints below still require verified Telegram initData when a bot token is configured.
            return json_response(self, {"ok": True, "tasks": read_state().get("tasks", [])})
        if path == "/api/approvals":
            return json_response(self, {"ok": True, "approvals": read_state().get("approvals", [])})
        if path == "/api/results":
            return json_response(self, {"ok": True, "results": read_state().get("results", [])})
        return text_response(self, "Not found", 404)

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        ok, _ = require_auth(self)
        if not ok:
            return
        try:
            body = read_json_body(self)
        except Exception as exc:
            return json_response(self, {"ok": False, "error": "bad-json", "detail": str(exc)}, 400)

        state = read_state()
        if path == "/api/tasks":
            title = str(body.get("title") or body.get("message") or "").strip()
            executor = str(body.get("executor") or "hermes")
            if not title:
                return json_response(self, {"ok": False, "error": "empty-title"}, 400)
            task = {"id": f"task-{now()}", "title": title[:180], "body": str(body.get("body") or "Создано из Mini App")[:500], "executor": executor, "status": "active", "createdAt": now()}
            state.setdefault("tasks", []).insert(0, task)
            state.setdefault("results", []).insert(0, {"id": f"result-{now()}", "title": f"Задача создана: {task['title']}", "kind": "task", "createdAt": now()})
            write_state(state)
            return json_response(self, {"ok": True, "task": task})

        if path == "/api/route/openclaw":
            message = str(body.get("message") or "").strip()
            if not message:
                return json_response(self, {"ok": False, "error": "empty-message"}, 400)
            task = {"id": f"task-openclaw-{now()}", "title": message[:180], "body": "Передано Клешне через OpenClaw bridge", "executor": "kleshna", "status": "active", "createdAt": now()}
            state.setdefault("tasks", []).insert(0, task)
            write_state(state)
            result = route_openclaw(message)
            state = read_state()
            task["status"] = "done" if result.get("ok") else "blocked"
            for i, old in enumerate(state.get("tasks", [])):
                if old.get("id") == task["id"]:
                    state["tasks"][i] = task
            title = "Клешня ответила" if result.get("ok") else "Клешня: ошибка маршрута"
            state.setdefault("results", []).insert(0, {"id": f"result-openclaw-{now()}", "title": title, "kind": "openclaw", "createdAt": now(), "detail": result})
            write_state(state)
            return json_response(self, {"ok": bool(result.get("ok")), "task": task, "route": result})

        if path == "/api/approvals/resolve":
            approval_id = str(body.get("id") or "")
            action = str(body.get("action") or "")
            if action not in {"allow_once", "deny"}:
                return json_response(self, {"ok": False, "error": "bad-action"}, 400)
            found = None
            for approval in state.get("approvals", []):
                if approval.get("id") == approval_id:
                    approval["status"] = "allowed" if action == "allow_once" else "denied"
                    approval["resolvedAt"] = now()
                    found = approval
                    break
            if not found:
                return json_response(self, {"ok": False, "error": "not-found"}, 404)
            state.setdefault("results", []).insert(0, {"id": f"result-approval-{now()}", "title": f"Approval: {found['status']}", "kind": "approval", "createdAt": now()})
            write_state(state)
            return json_response(self, {"ok": True, "approval": found})

        return json_response(self, {"ok": False, "error": "not-found"}, 404)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    read_state()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Arkestrator Mini App MVP: http://127.0.0.1:{PORT}/")
    print(f"Static: {STATIC}")
    server.serve_forever()


if __name__ == "__main__":
    main()
