from collections.abc import Generator
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import get_google_user
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.waitlist import WaitlistEntry
from app.services.google_auth import GoogleUserInfo


def test_create_waitlist_entry_stores_current_user_and_video_url():
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
            sub="google-waitlist",
            email="waitlist@example.com",
            name="Waitlist User",
            picture="https://example.com/waitlist.png",
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        client = TestClient(app)
        login = client.post("/api/auth/google", json={"id_token": "token"})
        token = login.json()["access_token"]

        response = client.post(
            "/api/waitlist",
            json={
                "youtubeUrl": "https://www.youtube.com/watch?v=abc123XYZ00",
                "source": "landing_early_access",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == "waitlist@example.com"
        assert body["name"] == "Waitlist User"
        assert body["youtube_url"] == "https://www.youtube.com/watch?v=abc123XYZ00"

        db = TestingSessionLocal()
        try:
            saved = db.scalar(select(WaitlistEntry))
            assert saved is not None
            assert saved.user_id == login.json()["user"]["id"]
            assert saved.email == "waitlist@example.com"
            assert saved.youtube_url == "https://www.youtube.com/watch?v=abc123XYZ00"
        finally:
            db.close()
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_create_waitlist_entry_requires_auth():
    client = TestClient(app)

    response = client.post(
        "/api/waitlist",
        json={"youtubeUrl": "https://www.youtube.com/watch?v=abc123XYZ00"},
    )

    assert response.status_code == 401


def test_create_waitlist_entry_notifies_discord_when_webhook_is_configured(monkeypatch):
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
            sub="google-waitlist",
            email="waitlist@example.com",
            name="Waitlist User",
            picture="https://example.com/waitlist.png",
        )

    mock_notify = Mock()
    monkeypatch.setattr("app.api.waitlist.notify_waitlist_signup", mock_notify)
    settings = get_settings()
    original_webhook_url = settings.discord_waitlist_webhook_url
    settings.discord_waitlist_webhook_url = "https://discord.com/api/webhooks/test"

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        client = TestClient(app)
        login = client.post("/api/auth/google", json={"id_token": "token"})
        token = login.json()["access_token"]

        response = client.post(
            "/api/waitlist",
            json={
                "youtubeUrl": "https://www.youtube.com/watch?v=abc123XYZ00",
                "source": "landing_early_access",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        mock_notify.assert_called_once()
        notified_entry = mock_notify.call_args.args[0]
        notified_webhook_url = mock_notify.call_args.args[1]
        assert notified_entry.email == "waitlist@example.com"
        assert notified_entry.youtube_url == "https://www.youtube.com/watch?v=abc123XYZ00"
        assert notified_webhook_url == "https://discord.com/api/webhooks/test"
    finally:
        settings.discord_waitlist_webhook_url = original_webhook_url
        app.dependency_overrides.clear()
        engine.dispose()


def test_create_waitlist_entry_succeeds_when_discord_notification_fails(monkeypatch):
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
            sub="google-waitlist",
            email="waitlist@example.com",
            name="Waitlist User",
            picture="https://example.com/waitlist.png",
        )

    def raise_notification_error(_entry: WaitlistEntry, _webhook_url: str) -> None:
        raise RuntimeError("discord unavailable")

    monkeypatch.setattr("app.api.waitlist.notify_waitlist_signup", raise_notification_error)
    settings = get_settings()
    original_webhook_url = settings.discord_waitlist_webhook_url
    settings.discord_waitlist_webhook_url = "https://discord.com/api/webhooks/test"

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        client = TestClient(app)
        login = client.post("/api/auth/google", json={"id_token": "token"})
        token = login.json()["access_token"]

        response = client.post(
            "/api/waitlist",
            json={
                "youtubeUrl": "https://www.youtube.com/watch?v=abc123XYZ00",
                "source": "landing_early_access",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        db = TestingSessionLocal()
        try:
            saved = db.scalar(select(WaitlistEntry))
            assert saved is not None
            assert saved.email == "waitlist@example.com"
        finally:
            db.close()
    finally:
        settings.discord_waitlist_webhook_url = original_webhook_url
        app.dependency_overrides.clear()
        engine.dispose()
