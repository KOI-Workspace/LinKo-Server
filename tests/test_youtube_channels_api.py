from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.youtube as youtube_api
from app.api.auth import get_google_user
from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.models.user import User
from app.models.youtube_channel import UserYoutubeChannel, YoutubeChannel
from app.services.google_auth import GoogleUserInfo


def channel_item(
    channel_id: str,
    title: str,
    *,
    country: str | None = None,
    language: str | None = None,
) -> dict:
    snippet = {
        "title": title,
        "thumbnails": {"high": {"url": f"https://example.com/{channel_id}.jpg"}},
    }
    if language is not None:
        snippet["defaultLanguage"] = language

    branding_channel = {}
    if country is not None:
        branding_channel["country"] = country

    return {
        "id": channel_id,
        "snippet": snippet,
        "brandingSettings": {"channel": branding_channel},
    }


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

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def auth_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/api/auth/google", json={"id_token": "token"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_channel_sync_requires_auth(client: TestClient):
    response = client.post("/api/youtube/channels/sync", json={"access_token": "google-token"})

    assert response.status_code == 401


def test_channel_sync_requires_google_access_token(client: TestClient):
    response = client.post("/api/youtube/channels/sync", json={}, headers=auth_headers(client))

    assert response.status_code == 422


def test_channel_sync_maps_youtube_token_rejection(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def reject_access_token(access_token: str) -> list[str]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_youtube_access_token",
                "message": "Invalid YouTube access token",
            },
        )

    monkeypatch.setattr(youtube_api, "fetch_user_subscription_channel_ids", reject_access_token)

    response = client.post(
        "/api/youtube/channels/sync",
        json={"access_token": "bad-google-token"},
        headers=auth_headers(client),
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_youtube_access_token"


def test_channel_sync_stores_only_korean_channels(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        youtube_api,
        "fetch_user_subscription_channel_ids",
        lambda access_token: ["channel-kr", "channel-en"],
    )
    monkeypatch.setattr(
        youtube_api,
        "fetch_youtube_channels",
        lambda channel_ids: [
            channel_item("channel-kr", "Korean Channel", country="KR"),
            channel_item("channel-en", "English Channel", country="US", language="en"),
        ],
    )

    response = client.post(
        "/api/youtube/channels/sync",
        json={"access_token": "google-youtube-token"},
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    assert response.json()["channels"] == [
        {
            "youtube_channel_id": "channel-kr",
            "title": "Korean Channel",
            "thumbnail_url": "https://example.com/channel-kr.jpg",
            "country": "KR",
            "default_language": None,
            "added_at": response.json()["channels"][0]["added_at"],
        }
    ]


def test_channel_sync_updates_existing_channel_without_duplicate_link(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        youtube_api,
        "fetch_user_subscription_channel_ids",
        lambda access_token: ["channel-kr"],
    )
    titles = iter(["Original Title", "Updated Title"])
    monkeypatch.setattr(
        youtube_api,
        "fetch_youtube_channels",
        lambda channel_ids: [channel_item("channel-kr", next(titles), language="ko")],
    )
    headers = auth_headers(client)

    first = client.post(
        "/api/youtube/channels/sync",
        json={"access_token": "google-youtube-token"},
        headers=headers,
    )
    second = client.post(
        "/api/youtube/channels/sync",
        json={"access_token": "google-youtube-token"},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["channels"][0]["title"] == "Updated Title"
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.scalar(select(func.count()).select_from(UserYoutubeChannel)) == 1


def test_channel_list_sorts_newest_first(client: TestClient):
    headers = auth_headers(client)
    with next(app.dependency_overrides[get_db]()) as db:
        user = db.scalar(select(User).where(User.email == "person@example.com"))
        older = YoutubeChannel(
            youtube_channel_id="older",
            title="Older",
            thumbnail_url=None,
            country="KR",
            default_language=None,
            raw_youtube_response={},
        )
        newer = YoutubeChannel(
            youtube_channel_id="newer",
            title="Newer",
            thumbnail_url=None,
            country="KR",
            default_language=None,
            raw_youtube_response={},
        )
        db.add_all([older, newer])
        db.flush()
        db.add_all(
            [
                UserYoutubeChannel(
                    user_id=user.id,
                    youtube_channel_id=older.id,
                    created_at=datetime.now(UTC) - timedelta(days=1),
                ),
                UserYoutubeChannel(
                    user_id=user.id,
                    youtube_channel_id=newer.id,
                    created_at=datetime.now(UTC),
                ),
            ]
        )
        db.commit()

    response = client.get("/api/youtube/channels", headers=headers)

    assert response.status_code == 200
    assert [channel["youtube_channel_id"] for channel in response.json()["channels"]] == [
        "newer",
        "older",
    ]
