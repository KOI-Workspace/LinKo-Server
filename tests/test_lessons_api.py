from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.lessons as lessons_api
from app.api.auth import get_google_user
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.models.lesson import Lesson
from app.models.user import User
from app.services.google_auth import GoogleUserInfo
from app.services.transcripts import TranscriptResult, TranscriptSegment


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
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
        return GoogleUserInfo("google-lessons", "lessons@example.com", "Lesson User", None)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    monkeypatch.setattr(lessons_api, "SessionLocal", TestingSessionLocal)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def auth_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/api/auth/google", json={"id_token": "token"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_lesson_requires_auth(client: TestClient):
    response = client.post(
        "/api/lessons",
        json={"youtubeUrl": "https://youtu.be/abc123XYZ00"},
    )

    assert response.status_code == 401


def test_create_lesson_schedules_generation_and_returns_generating(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    scheduled: list[int] = []

    def fake_generate(lesson_id: int) -> None:
        scheduled.append(lesson_id)

    monkeypatch.setattr(lessons_api, "generate_lesson_artifacts_task", fake_generate)
    monkeypatch.setattr(
        lessons_api,
        "fetch_youtube_video_item",
        lambda video_id: {
            "id": video_id,
            "snippet": {
                "title": "Generated Lesson",
                "channelTitle": "Korean Channel",
                "publishedAt": "2026-05-11T00:00:00Z",
                "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
            },
            "contentDetails": {"duration": "PT1M"},
        },
    )

    response = client.post(
        "/api/lessons",
        json={"youtubeUrl": "https://youtu.be/abc123XYZ00"},
        headers=auth_headers(client),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["generationStatus"] == "generating"
    assert scheduled == [int(body["lessonId"])]


def test_ready_lesson_flashcards_and_subtitles_are_returned(client: TestClient):
    headers = auth_headers(client)
    db = next(app.dependency_overrides[get_db]())
    try:
        user_id = db.scalar(select(User.id).where(User.email == "lessons@example.com"))
        lesson = Lesson(
            user_id=user_id,
            youtube_url="https://youtu.be/ready123",
            youtube_video_id="ready123",
            title="Ready Lesson",
            channel_title="Channel",
            thumbnail_url=None,
            duration_seconds=60,
            generation_status="ready",
            transcript_status="ready",
            transcript_source="youtube_caption",
            transcript_text="안녕하세요.",
            flashcards_json={"lessonId": "1", "lessonTitle": "Ready Lesson", "cards": []},
            subtitles_json={"youtubeId": "ready123", "durationSec": 60, "lines": []},
            watch_vocab_json={},
            cultural_notes_json=[],
            raw_youtube_metadata={},
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        lesson_id = lesson.id
    finally:
        db.close()

    response = client.get(f"/api/lessons/{lesson_id}/flashcards", headers=headers)
    assert response.status_code == 200
    assert response.json()["lessonTitle"] == "Ready Lesson"

    response = client.get(f"/api/lessons/{lesson_id}/subtitles", headers=headers)
    assert response.status_code == 200
    assert response.json()["youtubeId"] == "ready123"


def test_lesson_artifact_endpoints_return_status_specific_errors(client: TestClient):
    headers = auth_headers(client)
    db = next(app.dependency_overrides[get_db]())
    try:
        user_id = db.scalar(select(User.id).where(User.email == "lessons@example.com"))
        generating = Lesson(
            user_id=user_id,
            youtube_url="https://youtu.be/generating",
            youtube_video_id="generating",
            title="Generating",
            channel_title="Channel",
            thumbnail_url=None,
            duration_seconds=60,
            generation_status="generating",
            transcript_status="pending",
            raw_youtube_metadata={},
        )
        failed = Lesson(
            user_id=user_id,
            youtube_url="https://youtu.be/failed",
            youtube_video_id="failed",
            title="Failed",
            channel_title="Channel",
            thumbnail_url=None,
            duration_seconds=60,
            generation_status="failed",
            transcript_status="unavailable",
            raw_youtube_metadata={},
            error_code="transcript_unavailable",
            error_message="Korean captions are not available.",
        )
        db.add_all([generating, failed])
        db.commit()
        db.refresh(generating)
        db.refresh(failed)
        generating_id = generating.id
        failed_id = failed.id
    finally:
        db.close()

    response = client.get(f"/api/lessons/{generating_id}/flashcards", headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "lesson_not_ready"

    response = client.get(f"/api/lessons/{failed_id}/subtitles", headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "lesson_generation_failed"


def test_background_task_generates_and_stores_artifacts(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()
    headers = auth_headers(client)
    db = next(app.dependency_overrides[get_db]())
    try:
        user_id = db.scalar(select(User.id).where(User.email == "lessons@example.com"))
        lesson = Lesson(
            user_id=user_id,
            youtube_url="https://youtu.be/abc123XYZ00",
            youtube_video_id="abc123XYZ00",
            title="Background Lesson",
            channel_title="Channel",
            thumbnail_url=None,
            duration_seconds=10,
            generation_status="generating",
            transcript_status="pending",
            raw_youtube_metadata={},
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        lesson_id = lesson.id
    finally:
        db.close()

    def fake_download(*args, **kwargs):
        if kwargs["lang"] == "en":
            return TranscriptResult(
                source="youtube_caption",
                text="Hello. Today we study Korean.",
                lang="en",
                segments=[
                    TranscriptSegment(
                        start_sec=0,
                        end_sec=5,
                        text="Hello. Today we study Korean.",
                    )
                ],
            )
        return TranscriptResult(
            source="youtube_caption",
            text="안녕하세요. 오늘은 한국어를 공부해요.",
            lang="ko",
            segments=[
                TranscriptSegment(
                    start_sec=0,
                    end_sec=5,
                    text="안녕하세요. 오늘은 한국어를 공부해요.",
                )
            ],
        )

    monkeypatch.setattr(lessons_api, "download_youtube_captions", fake_download)

    lessons_api.generate_lesson_artifacts_task(lesson_id)

    response = client.get(f"/api/lessons/{lesson_id}/flashcards", headers=headers)
    assert response.status_code == 200
    assert response.json()["lessonId"] == str(lesson_id)

    response = client.get(f"/api/lessons/{lesson_id}/subtitles", headers=headers)
    assert response.status_code == 200
    assert response.json()["youtubeId"] == "abc123XYZ00"
    assert response.json()["lines"][0]["english"] == "Hello. Today we study Korean."
    get_settings.cache_clear()


def test_background_task_keeps_watch_ready_when_flashcard_generation_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    headers = auth_headers(client)
    db = next(app.dependency_overrides[get_db]())
    try:
        user_id = db.scalar(select(User.id).where(User.email == "lessons@example.com"))
        lesson = Lesson(
            user_id=user_id,
            youtube_url="https://youtu.be/abc123XYZ00",
            youtube_video_id="abc123XYZ00",
            title="Subtitle Only Lesson",
            channel_title="Channel",
            thumbnail_url=None,
            duration_seconds=900,
            generation_status="generating",
            transcript_status="pending",
            raw_youtube_metadata={},
        )
        db.add(lesson)
        db.commit()
        db.refresh(lesson)
        lesson_id = lesson.id
    finally:
        db.close()

    requested_ranges: list[tuple[int, int]] = []

    def fake_download(*args, **kwargs):
        requested_ranges.append((kwargs["start_sec"], kwargs["end_sec"]))
        if kwargs["lang"] == "en":
            return None
        return TranscriptResult(
            source="youtube_caption",
            text="안녕하세요. 오늘은 한국어를 공부해요.",
            segments=[
                TranscriptSegment(
                    start_sec=0,
                    end_sec=5,
                    text="안녕하세요. 오늘은 한국어를 공부해요.",
                )
            ],
        )

    monkeypatch.setattr(lessons_api, "download_youtube_captions", fake_download)
    monkeypatch.setattr(
        lessons_api,
        "generate_lesson_artifacts_from_transcript",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Gemini unavailable")),
    )

    lessons_api.generate_lesson_artifacts_task(lesson_id)

    assert requested_ranges == [(0, 900), (0, 900)]

    response = client.get(f"/api/lessons/{lesson_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["generationStatus"] == "ready"
    assert response.json()["subtitleDone"] is True
    assert response.json()["flashcardDone"] is False
    assert response.json()["errorCode"] == "flashcard_generation_failed"

    response = client.get(f"/api/lessons/{lesson_id}/subtitles", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["youtubeId"] == "abc123XYZ00"
    assert body["lines"][0]["korean"].startswith("안녕하세요")
    assert body["lines"][0]["english"] == ""

    response = client.get(f"/api/lessons/{lesson_id}/flashcards", headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "flashcard_generation_failed"
