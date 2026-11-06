"""Admin alerts. Telegram if configured, otherwise logged and marked as not sent.

Pang Zai Jie's implementation:
  - Rich HTML-formatted Telegram messages with severity emojis.
  - Sends plain text as a fallback if the HTML call is rejected.
  - Plug in a custom sender for other channels:
        from app import notifier
        notifier.set_sender(my_send_alert)   # takes a Notification, returns True if delivered
"""
from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Optional

from . import models as m
from .config import get_settings

log = logging.getLogger("notifier")

_sender: Optional[Callable[[m.Notification], bool]] = None

# Severity emoji map used in the formatted Telegram message.
_SEVERITY_EMOJI = {"high": "🚨", "medium": "⚠️", "low": "ℹ️"}
# Root-cause labels with emoji
_CAUSE_LABEL = {
    "ap_hardware_failure": "📡 AP Hardware Failure",
    "isp_uplink_outage":   "🌐 ISP / Uplink Outage",
    "congestion":          "📶 Wi-Fi Congestion",
    "iot_device_fault":    "🔌 IoT Device Fault",
    "unknown":             "❓ Unknown Issue",
}


# ------------------------------------------------------------------ public API
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


# -------------------------------------------------------- Telegram internals
def _escape_html(s: str) -> str:
    """Minimal HTML escaping required by Telegram's HTML parse mode."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_html(n: m.Notification) -> Optional[str]:
    """Build a nicely formatted HTML message from the notification.

    Returns None when parsing fails so the caller falls back to plain text.
    """
    text = n.text

    # Recovery messages have the shape:
    #   "T-0001 [RESOLVED] Block B: uplink outage cleared."
    if "[RESOLVED]" in text:
        parts = text.split(None, 1)
        ticket_id = parts[0] if parts else n.notification_id
        rest = text.split("[RESOLVED]", 1)[-1].strip()
        return (
            "✅ <b>[RESOLVED] Smart Lab Alert</b>\n"
            f"🎉 {_escape_html(rest)}\n"
            f"📋 <b>Ticket:</b> <code>{_escape_html(ticket_id)}</code>"
        )

    # Incident messages have the shape:
    #   "T-0001 [HIGH] Block B: AP hardware failure (ap-b-02). Action: reboot or replace ap-b-02."
    try:
        first, _, remainder = text.partition(" ")
        ticket_id = first
        sev_tag, _, body = remainder.partition("] ")
        severity = sev_tag.lstrip("[").lower()   # e.g. "high"
        if not re.fullmatch(r"T-\d+", ticket_id) or severity not in _SEVERITY_EMOJI:
            return None  # not an incident message: send the original text as it is
        emoji = _SEVERITY_EMOJI.get(severity, "⚠️")

        location_part, _, action_part = body.partition(". Action: ")
        location_name, _, cause_and_devices = location_part.partition(": ")

        if "(" in cause_and_devices and cause_and_devices.endswith(")"):
            cause_raw, _, devices_raw = cause_and_devices.partition("(")
            cause_raw = cause_raw.strip()
            devices_raw = devices_raw.rstrip(")")
        else:
            cause_raw = cause_and_devices
            devices_raw = ""

        # Look up friendly label (fall back to raw string).
        cause_label = next(
            (v for k, v in _CAUSE_LABEL.items() if k in cause_raw.lower().replace(" ", "_")),
            f"⚠️ {cause_raw}",
        )

        lines = [
            f"{emoji} <b>[{severity.upper()}] Smart Lab Alert</b>",
            f"📍 <b>Location:</b> {_escape_html(location_name.strip())}",
            f"🔎 <b>Issue:</b> {cause_label}",
        ]
        if devices_raw.strip():
            lines.append(f"🖥️ <b>Affected:</b> <code>{_escape_html(devices_raw.strip())}</code>")
        if action_part.strip():
            lines.append(f"🔧 <b>Action:</b> {_escape_html(action_part.strip())}")
        lines.append(f"📋 <b>Ticket:</b> <code>{_escape_html(ticket_id)}</code>")
        return "\n".join(lines)
    except Exception:
        return None   # fall back to plain text


def _send_raw(url: str, params: dict, timeout: float = 5.0) -> dict:
    """POST url-encoded params; returns the parsed JSON body."""
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _telegram(n: m.Notification) -> tuple[bool, Optional[str]]:
    s = get_settings()
    if not (s.telegram_bot_token and s.telegram_chat_id):
        log.info("[not sent, Telegram not configured] %s", n.text)
        return False, "telegram_not_configured"

    # Never log the URL because it contains the bot token.
    api_base = f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
    base_params = {"chat_id": s.telegram_chat_id}

    try:
        # 1. Try a rich HTML message.
        html = _build_html(n)
        if html:
            try:
                data = _send_raw(api_base, {**base_params, "text": html, "parse_mode": "HTML"})
                if data.get("ok"):
                    return True, None
            except urllib.error.HTTPError as exc:  # e.g. 400 "can't parse entities": use plain text
                log.warning("Telegram rejected the formatted message (HTTP %s), sending plain text", exc.code)

        # 2. Fall back to the original plain text.
        data = _send_raw(api_base, {**base_params, "text": n.text})
        ok = bool(data.get("ok"))
        return ok, None if ok else "telegram_rejected"

    except Exception as exc:   # never log the URL: it contains the bot token
        log.warning("Telegram send failed (%s)", type(exc).__name__)
        return False, type(exc).__name__
