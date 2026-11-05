"""Tiny .env loader (no extra dependency).

Reads KEY=VALUE lines from backend/.env and the repo-root .env. Variables that are
already set in the real environment are never overridden. Set SKIP_DOTENV=1 to disable.
"""
from __future__ import annotations

import os
from pathlib import Path


def parse_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        return None
    if line.startswith("export "):
        line = line[len("export "):]
    key, _, value = line.partition("=")
    key, value = key.strip(), value.strip()
    if not key:
        return None
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    else:
        value = value.split(" #", 1)[0].strip()
    return key, value


def load_dotenv(paths: list[Path] | None = None) -> list[str]:
    """Load the files in order; the first file that defines a key wins. Returns keys set."""
    if os.getenv("SKIP_DOTENV") == "1":
        return []
    if paths is None:
        backend = Path(__file__).resolve().parent.parent
        paths = [backend / ".env", backend.parent / ".env"]
    loaded: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            parsed = parse_line(raw)
            if parsed is None:
                continue
            key, value = parsed
            if key not in os.environ:
                os.environ[key] = value
                loaded.append(key)
    return loaded
