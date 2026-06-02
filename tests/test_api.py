import importlib
import os

from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://admin:adminadmin@localhost:5433/anonymous",
)
import src.db.database as database

importlib.reload(database)
database.init_db()

from src.main import app

client = TestClient(app)


def test_full_box_lifecycle():
    response = client.post("/box")
    assert response.status_code == 200
    data = response.json()
    assert data["uuid"]
    assert data["owner_token"]

    uuid = data["uuid"]
    token = data["owner_token"]

    invalid_feedback = client.post(f"/box/{uuid}/feedback", json={"text": "badword content"})
    assert invalid_feedback.status_code == 400

    feedback = client.post(f"/box/{uuid}/feedback", json={"text": "Normal feedback text"})
    assert feedback.status_code == 200
    fb_data = feedback.json()
    assert fb_data["text"] == "Normal feedback text"
    assert fb_data["status"] == "approved"

    unauthorized = client.get(f"/box/{uuid}")
    assert unauthorized.status_code == 403

    owner_view = client.get(f"/box/{uuid}", params={"token": token})
    assert owner_view.status_code == 200
    assert len(owner_view.json()["feedbacks"]) == 1

    reply_fail = client.post(
        f"/feedback/{fb_data['id']}/reply", json={"text": "Owner reply"}, params={"token": "wrong"}
    )
    assert reply_fail.status_code == 403

    reply_ok = client.post(f"/feedback/{fb_data['id']}/reply", json={"text": "Owner reply"}, params={"token": token})
    assert reply_ok.status_code == 200

    owner_view_after = client.get(f"/box/{uuid}", params={"token": token})
    assert len(owner_view_after.json()["feedbacks"][0]["replies"]) == 1


def test_auth_register_and_login():
    register_resp = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "secret123", "confirm_password": "secret123"},
    )
    assert register_resp.status_code == 201
    register_data = register_resp.json()
    assert register_data["username"] == "testuser"
    assert register_data["token"]

    login_resp = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "secret123"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["username"] == "testuser"
    assert login_data["token"] == register_data["token"]

    invalid_login = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "wrongpass"},
    )
    assert invalid_login.status_code == 401

    duplicate_register = client.post(
        "/auth/register",
        json={"username": "testuser", "password": "secret123", "confirm_password": "secret123"},
    )
    assert duplicate_register.status_code == 400

    me_resp = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {register_data['token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "testuser"

    my_boxes_resp = client.get(
        "/auth/my-boxes",
        headers={"Authorization": f"Bearer {register_data['token']}"},
    )
    assert my_boxes_resp.status_code == 200
    assert my_boxes_resp.json()["boxes"] == []

    created_box = client.post("/box", headers={"Authorization": f"Bearer {register_data['token']}"})
    assert created_box.status_code == 200

    my_boxes_after = client.get(
        "/auth/my-boxes",
        headers={"Authorization": f"Bearer {register_data['token']}"},
    )
    assert my_boxes_after.status_code == 200
    assert len(my_boxes_after.json()["boxes"]) == 1

    my_feedbacks = client.get(
        "/auth/my-feedbacks",
        headers={"Authorization": f"Bearer {register_data['token']}"},
    )
    assert my_feedbacks.status_code == 200
    assert my_feedbacks.json()["feedbacks"] == []

    feedback_resp = client.post(
        f"/box/{created_box.json()['uuid']}/feedback",
        json={"text": "user feedback"},
    )
    assert feedback_resp.status_code == 200

    my_feedbacks_after = client.get(
        "/auth/my-feedbacks",
        headers={"Authorization": f"Bearer {register_data['token']}"},
    )
    assert my_feedbacks_after.status_code == 200
    assert len(my_feedbacks_after.json()["feedbacks"]) == 1
    assert my_feedbacks_after.json()["feedbacks"][0]["box_uuid"] == created_box.json()["uuid"]
