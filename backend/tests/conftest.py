import pytest
from starlette.testclient import TestClient

from app import notifier
from app.main import create_app
from app.store import store

ENV_KEYS = [
    "APP_ENV", "INGEST_API_KEY", "DASHBOARD_API_KEY", "GEMINI_API_KEY",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "HASH_SALT",
]


@pytest.fixture(autouse=True)
def sent(monkeypatch):
    """Clean env + state for every test. Returns the list of notifications 'delivered'."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    store.reset()
    delivered = []
    notifier.set_sender(lambda n: delivered.append(n) or True)
    yield delivered
    notifier.set_sender(None)


@pytest.fixture
def client():
    return TestClient(create_app())
