"""Разбор входящей заявки: страница и API поверх имитатора AI."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "index.html"


class AiTimeout(TimeoutError):
    """Имитатор не ответил вовремя."""


def simulate_ai(text: str) -> dict:
    """Учебный имитатор. Не ходит в сеть и специально ломается на метках."""
    lowered = text.casefold()
    if "таймаут" in lowered:
        raise AiTimeout("имитатор не ответил")
    if "битый" in lowered:
        return {"http": 200, "topic": "неизвестно", "draft": "   "}
    return {"http": 200, "topic": "оплата", "draft": f"Проверьте заявку: {text.strip()}"}


def review(text: str, ai=simulate_ai) -> tuple[int, dict]:
    """Пустой ввод, таймаут и пустой ответ модели не считаются готовым черновиком."""
    if text is None or not str(text).strip():
        return 422, _manual("empty_input")

    try:
        raw = ai(str(text))
    except AiTimeout:
        return 504, _manual("timeout")

    topic = str(raw.get("topic") or "").strip()
    draft = str(raw.get("draft") or "")
    if topic.casefold() in {"", "неизвестно", "unknown"} or not draft.strip():
        return 422, _manual("invalid_ai")

    return 200, {
        "ok": True,
        "manual": False,
        "reason": "",
        "topic": topic,
        "draft": draft.strip(),
    }


def apply_screen(previous_draft: str, status: int, body: dict) -> dict:
    """При сбое экран очищает старый черновик и оставляет заявку человеку."""
    if status != 200 or not body.get("ok"):
        return {"draft": "", "manual": True, "reason": body.get("reason", "")}
    return {"draft": body.get("draft", ""), "manual": False, "reason": ""}


def _manual(reason: str) -> dict:
    return {"ok": False, "manual": True, "reason": reason, "topic": "", "draft": ""}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in {"/", "/index.html"}:
            self.send_error(404)
            return
        payload = PAGE.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != "/api/review":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw or "{}")
        except json.JSONDecodeError:
            payload = {}
        status, body = review(payload.get("text", ""))
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt, *args):
        return


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
