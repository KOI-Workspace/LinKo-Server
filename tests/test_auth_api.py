from collections.abc import Generator
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import get_google_user
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.google_auth import GoogleUserInfo


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_google() -> GoogleUserInfo:
        return GoogleUserInfo(
            sub="google-123",
            email="person@example.com",
            name="Person",
            picture="https://example.com/pic.png",
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_google_login_creates_user_and_returns_access_token(client: TestClient):
    response = client.post("/api/auth/google", json={"id_token": "valid-google-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "person@example.com"


def test_me_returns_current_user_profile(client: TestClient):
    login = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
    token = login.json()["access_token"]

    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "person@example.com",
        "name": "Person",
        "picture": "https://example.com/pic.png",
    }


def test_me_rejects_missing_token(client: TestClient):
    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "missing_token"


def test_me_rejects_malformed_bearer_token(client: TestClient):
    response = client.get(
        "/api/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_token"


def test_google_login_notifies_discord_for_new_users_only(client: TestClient, monkeypatch):
    mock_notify = Mock()
    monkeypatch.setattr("app.api.auth.notify_new_user_signup", mock_notify)
    settings = get_settings()
    original_webhook_url = settings.discord_new_user_webhook_url
    settings.discord_new_user_webhook_url = "https://discord.com/api/webhooks/test"

    try:
        first_response = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
        second_response = client.post("/api/auth/google", json={"id_token": "valid-google-token"})

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        mock_notify.assert_called_once()
        notified_user = mock_notify.call_args.args[0]
        notified_webhook_url = mock_notify.call_args.args[1]
        assert notified_user.email == "person@example.com"
        assert notified_webhook_url == "https://discord.com/api/webhooks/test"
    finally:
        settings.discord_new_user_webhook_url = original_webhook_url


def test_google_login_succeeds_when_new_user_discord_notification_fails(
    client: TestClient, monkeypatch
):
    def raise_notification_error(*_args) -> None:
        raise RuntimeError("discord unavailable")

    monkeypatch.setattr("app.api.auth.notify_new_user_signup", raise_notification_error)
    settings = get_settings()
    original_webhook_url = settings.discord_new_user_webhook_url
    settings.discord_new_user_webhook_url = "https://discord.com/api/webhooks/test"

    try:
        response = client.post("/api/auth/google", json={"id_token": "valid-google-token"})

        assert response.status_code == 200
        assert response.json()["user"]["email"] == "person@example.com"
    finally:
        settings.discord_new_user_webhook_url = original_webhook_url
