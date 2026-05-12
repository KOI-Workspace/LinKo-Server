from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.videos as videos_api
from app.api.auth import get_google_user
from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.services.google_auth import GoogleUserInfo


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_google() -> GoogleUserInfo:
        return GoogleUserInfo("google-123", "person@example.com", "Person", None)

    def override_youtube(video_id: str) -> dict:
        assert video_id == "abc123XYZ00"
        return {
            "id": "abc123XYZ00",
            "snippet": {
                "title": "Example video",
                "publishedAt": "2026-05-08T00:00:00Z",
                "channelTitle": "Example Channel",
                "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
            },
            "contentDetails": {"duration": "PT12M34S"},
        }

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(videos_api, "fetch_youtube_video_item", override_youtube)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        yield TestClient(app)
    finally:
        monkeypatch.undo()
        app.dependency_overrides.clear()
        engine.dispose()


def test_video_metadata_requires_auth(client: TestClient):
    response = client.get("/api/videos/metadata?url=https://youtu.be/abc123XYZ00")

    assert response.status_code == 401


def test_video_metadata_returns_frontend_ready_data(client: TestClient):
    login = client.post("/api/auth/google", json={"id_token": "token"})
    token = login.json()["access_token"]

    response = client.get(
        "/api/videos/metadata?url=https://youtu.be/abc123XYZ00",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "video_id": "abc123XYZ00",
        "title": "Example video",
        "published_at": "2026-05-08T00:00:00Z",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "channel_title": "Example Channel",
        "duration_seconds": 754,
        "duration_text": "12:34",
        "url": "https://youtu.be/abc123XYZ00",
    }
