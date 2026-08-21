from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


def _post_json(url: str, payload: dict[str, object]) -> None:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(request, timeout=20):
        pass


def notify(message: str) -> list[str]:
    delivered: list[str] = []
    lark = os.environ.get("LARK_WEBHOOK_URL")
    if lark:
        _post_json(lark, {"msg_type": "text", "content": {"text": message}})
        delivered.append("lark")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        _post_json(url, {"chat_id": chat_id, "text": message})
        delivered.append("telegram")
    return delivered
