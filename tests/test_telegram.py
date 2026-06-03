import importlib
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://admin:adminadmin@localhost:5433/anonymous",
)
os.environ["INTERNAL_BOT_SECRET"] = "test-bot-secret"

import src.db.database as database

importlib.reload(database)
database.init_db()

from src.main import app

client = TestClient(app)
BOT_HEADERS = {"X-Bot-Secret": "test-bot-secret"}


def _register_and_login(username: str) -> str:
    client.post(
        "/auth/register",
        json={"username": username, "password": "secret123", "confirm_password": "secret123"},
    )
    login = client.post(
        "/auth/login",
        json={"username": username, "password": "secret123"},
    )
    return login.json()["token"]


def test_telegram_link_unlink_and_confirm():
    token = _register_and_login("tg_user_a")
    auth = {"Authorization": f"Bearer {token}"}

    status = client.get("/auth/telegram/status", headers=auth)
    assert status.status_code == 200
    assert status.json()["linked"] is False

    link_resp = client.post("/auth/telegram/link-token", headers=auth)
    assert link_resp.status_code == 200
    data = link_resp.json()
    assert "t.me/" in data["link_url"]
    assert "link_" in data["link_url"]
    code = data["link_url"].split("link_")[-1]

    confirm = client.post(
        "/internal/telegram/confirm",
        json={"code": code, "telegram_user_id": 111222333},
        headers=BOT_HEADERS,
    )
    assert confirm.status_code == 200
    assert confirm.json()["username"] == "tg_user_a"

    status_linked = client.get("/auth/telegram/status", headers=auth)
    assert status_linked.json()["linked"] is True

    unlink = client.delete("/auth/telegram/unlink", headers=auth)
    assert unlink.status_code == 204

    status_after = client.get("/auth/telegram/status", headers=auth)
    assert status_after.json()["linked"] is False


def test_telegram_relink_moves_account():
    token_a = _register_and_login("tg_user_b")
    token_b = _register_and_login("tg_user_c")

    link_a = client.post("/auth/telegram/link-token", headers={"Authorization": f"Bearer {token_a}"})
    code_a = link_a.json()["link_url"].split("link_")[-1]
    client.post(
        "/internal/telegram/confirm",
        json={"code": code_a, "telegram_user_id": 999888777},
        headers=BOT_HEADERS,
    )

    link_b = client.post("/auth/telegram/link-token", headers={"Authorization": f"Bearer {token_b}"})
    code_b = link_b.json()["link_url"].split("link_")[-1]
    confirm_b = client.post(
        "/internal/telegram/confirm",
        json={"code": code_b, "telegram_user_id": 999888777},
        headers=BOT_HEADERS,
    )
    assert confirm_b.status_code == 200
    assert confirm_b.json()["username"] == "tg_user_c"

    status_a = client.get("/auth/telegram/status", headers={"Authorization": f"Bearer {token_a}"})
    status_b = client.get("/auth/telegram/status", headers={"Authorization": f"Bearer {token_b}"})
    assert status_a.json()["linked"] is False
    assert status_b.json()["linked"] is True


@patch("src.services.telegram_notify_service._send_sync", return_value=True)
def test_feedback_triggers_notification_for_linked_user(mock_send):
    token = _register_and_login("tg_notify_user")
    auth = {"Authorization": f"Bearer {token}"}

    box = client.post("/box", headers=auth)
    box_uuid = box.json()["uuid"]

    link = client.post("/auth/telegram/link-token", headers=auth)
    code = link.json()["link_url"].split("link_")[-1]
    client.post(
        "/internal/telegram/confirm",
        json={"code": code, "telegram_user_id": 555444333},
        headers=BOT_HEADERS,
    )

    with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "fake-token"}):
        feedback = client.post(f"/box/{box_uuid}/feedback", json={"text": "hello from test"})
    assert feedback.status_code == 200

    mock_send.assert_called()
    args = mock_send.call_args[0]
    assert args[0] == 555444333
    assert "…" in args[1]
