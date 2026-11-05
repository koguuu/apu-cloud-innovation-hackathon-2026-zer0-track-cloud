"""Admin alerts. Telegram if configured, otherwise logged and marked as not sent.

Pang Zai Jie can replace the default with his own function:
    from app import notifier
    notifier.set_sender(my_send_alert)   # takes a Notification, returns True if delivered
"""
from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Callable, Optional

from . import models as m
from .config import get_settings

log = logging.getLogger("notifier")

_sender: Optional[Callable[[m.Notification], bool]] = None


def set_sender(fn: Optional[Callable[[m.Notification], bool]]) -> None:
    global _sender
    _sender = fn


def send_notification(n: m.Notification) -> tuple[bool, Optional[str]]:
    """Returns (sent, error)."""
    if _sender is not None:
        try:
            return bool(_sender(n)), None
        except Exception as exc:
            log.warning("custom sender failed (%s)", type(exc).__name__)
            return False, type(exc).__name__
    return _telegram(n)


def _telegram(n: m.Notification) -> tuple[bool, Optional[str]]:
    s = get_settings()
    if not (s.telegram_bot_token and s.telegram_chat_id):
        log.info("[not sent, Telegram not configured] %s", n.text)
        return False, "telegram_not_configured"
    url = f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": s.telegram_chat_id, "text": n.text}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=5) as resp:
            ok = bool(json.load(resp).get("ok"))
        return ok, None if ok else "telegram_rejected"
    except Exception as exc:  # never log the URL: it contains the bot token
        log.warning("Telegram send failed (%s)", type(exc).__name__)
        return False, type(exc).__name__
