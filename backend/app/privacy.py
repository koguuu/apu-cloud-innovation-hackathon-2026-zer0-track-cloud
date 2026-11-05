"""Privacy helpers: students are only ever identified by a salted hash."""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

# Keys that must never appear in an event (raw identifiers / personal data).
FORBIDDEN_KEYS = {
    "student_id", "studentid", "tp", "tp_number", "tpnumber", "name", "full_name",
    "email", "phone", "ic", "nric", "passport",
}


def find_pii_keys(obj: Any) -> list[str]:
    """Return any forbidden keys found anywhere in a JSON-like object."""
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and key.lower() in FORBIDDEN_KEYS:
                found.append(key)
            found.extend(find_pii_keys(value))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_pii_keys(item))
    return found


def hash_student_id(raw_id: str, salt: str | None = None) -> str:
    """Stable anonymous id for a student, e.g. 's_9f2c41ab77d0'. Needs HASH_SALT (keep it secret)."""
    salt = salt if salt is not None else os.getenv("HASH_SALT", "")
    if not salt:
        raise ValueError("HASH_SALT is not set")
    digest = hmac.new(salt.encode(), raw_id.strip().upper().encode(), hashlib.sha256).hexdigest()
    return "s_" + digest[:12]
