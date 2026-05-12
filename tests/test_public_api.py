"""Tests for the unauthenticated public preview-lesson endpoints.

These tests use an in-memory SQLite database and create real Lesson rows so
the public endpoints are exercised against the same DB query path used in
production.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import lesson as _lesson_module  # noqa: F401 – registers Lesson
from app.models import user as _user_module  # noqa: F401 – registers User (FK dep)
from app.models.lesson import Lesson

# ---------------------------------------------------------------------------
# In-memory SQLite test database
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

client = TestClient(app)

BASE = "/api/public"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_FLASHCARDS_JSON = {
    "lessonId": "1",
    "lessonTitle": "Test Lesson",
    "cards": [
        {
            "id": "fc-1-1",
            "type": "word",
            "expression": "안녕하세요",
            "meaning": "Hello",
            "exampleSentence": "안녕하세요, 반갑습니다.",
            "exampleTranslation": "Hello, nice to meet you.",
            "video": {"youtubeId": "abc123", "startSec": 0, "endSec": 5},
            "relatedVideos": [],
            "dailyConversation": [
                {"text": "안녕하세요!", "isQuestion": True},
                {"text": "네, 안녕하세요!", "isQuestion": False},
            ],
        }
    ],
}

_SUBTITLES_JSON = {
    "youtubeId": "abc123",
    "durationSec": 120,
    "lines": [
        {
            "id": "s1",
            "startSec": 0,
            "endSec": 5,
            "korean": "안녕하세요!",
            "english": "Hello!",
        }
    ],
}

_WATCH_VOCAB_JSON = {
    "안녕하세요": {
        "meaning": "Hello",
        "cardId": "fc-1-1",
        "lessonId": "1",
        "expression": "안녕하세요",
        "exampleSentence": "안녕하세요, 반갑습니다.",
        "exampleTranslation": "Hello, nice to meet you.",
    }
}

_CULTURAL_NOTES_JSON = [
    {
        "id": "culture-1-1",
        "subtitleId": "s1",
        "title": "안녕하세요",
        "keyword": "Formal greeting",
        "explanation": "The standard formal greeting in Korean.",
    }
]

_UNSET = object()


def _make_lesson(
    db: Session,
    *,
    is_preview: bool = True,
    generation_status: str = "ready",
    flashcards_json: dict | None | object = _UNSET,
    subtitles_json: dict | None | object = _UNSET,
    watch_vocab_json: dict | None | object = _UNSET,
    cultural_notes_json: list | None | object = _UNSET,
) -> Lesson:
    lesson = Lesson(
        user_id=1,
        youtube_url="https://youtube.com/watch?v=abc123",
        youtube_video_id="abc123",
        title="Test Lesson",
        channel_title="Test Channel",
        thumbnail_url="https://img.youtube.com/vi/abc123/hqdefault.jpg",
        duration_seconds=120,
        generation_status=generation_status,
        is_preview=is_preview,
        transcript_status="ready",
        flashcards_json=_FLASHCARDS_JSON if flashcards_json is _UNSET else flashcards_json,
        subtitles_json=_SUBTITLES_JSON if subtitles_json is _UNSET else subtitles_json,
        watch_vocab_json=_WATCH_VOCAB_JSON if watch_vocab_json is _UNSET else watch_vocab_json,
        cultural_notes_json=_CULTURAL_NOTES_JSON if cultural_notes_json is _UNSET else cultural_notes_json,
        raw_youtube_metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


# ---------------------------------------------------------------------------
# GET /api/public/preview-lessons
# ---------------------------------------------------------------------------


def test_list_preview_lessons_empty_db():
    response = client.get(f"{BASE}/preview-lessons")
    assert response.status_code == 200
    assert response.json() == []


def test_list_preview_lessons_returns_preview_only():
    with TestingSessionLocal() as db:
        preview = _make_lesson(db, is_preview=True)
        _make_lesson(db, is_preview=False)  # should NOT appear

    data = client.get(f"{BASE}/preview-lessons").json()
    assert len(data) == 1
    assert data[0]["id"] == str(preview.id)


def test_list_preview_lessons_excludes_non_ready():
    with TestingSessionLocal() as db:
        _make_lesson(db, is_preview=True, generation_status="generating")

    data = client.get(f"{BASE}/preview-lessons").json()
    assert data == []


def test_list_preview_lessons_item_shape():
    with TestingSessionLocal() as db:
        _make_lesson(db)

    data = client.get(f"{BASE}/preview-lessons").json()
    item = data[0]
    required = {"id", "title", "channelName", "duration", "date", "generationStatus"}
    assert required.issubset(item.keys())


def test_list_preview_lessons_no_auth_required():
    response = client.get(f"{BASE}/preview-lessons", headers={})
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/public/lessons/{id}/flashcards
# ---------------------------------------------------------------------------


def test_get_preview_flashcards_success():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    response = client.get(f"{BASE}/lessons/{lesson.id}/flashcards")
    assert response.status_code == 200


def test_get_preview_flashcards_schema():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    data = client.get(f"{BASE}/lessons/{lesson.id}/flashcards").json()
    assert "lessonId" in data
    assert "lessonTitle" in data
    assert isinstance(data["cards"], list)
    assert len(data["cards"]) > 0


def test_get_preview_flashcards_non_preview_lesson_404():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db, is_preview=False)

    response = client.get(f"{BASE}/lessons/{lesson.id}/flashcards")
    assert response.status_code == 404


def test_get_preview_flashcards_unknown_id_404():
    response = client.get(f"{BASE}/lessons/9999/flashcards")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "lesson_not_found"


def test_get_preview_flashcards_still_generating_409():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db, generation_status="generating")

    response = client.get(f"{BASE}/lessons/{lesson.id}/flashcards")
    assert response.status_code == 409


def test_get_preview_flashcards_no_auth_required():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    response = client.get(f"{BASE}/lessons/{lesson.id}/flashcards", headers={})
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/public/lessons/{id}/subtitles
# ---------------------------------------------------------------------------


def test_get_preview_subtitles_success():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    response = client.get(f"{BASE}/lessons/{lesson.id}/subtitles")
    assert response.status_code == 200


def test_get_preview_subtitles_schema():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    data = client.get(f"{BASE}/lessons/{lesson.id}/subtitles").json()
    assert "youtubeId" in data
    assert "durationSec" in data
    assert isinstance(data["lines"], list)
    assert isinstance(data["vocabMap"], dict)
    assert isinstance(data["culturalNotes"], list)


def test_get_preview_subtitles_lines_shape():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    data = client.get(f"{BASE}/lessons/{lesson.id}/subtitles").json()
    for line in data["lines"]:
        assert {"id", "startSec", "endSec", "korean", "english"}.issubset(line.keys())


def test_get_preview_subtitles_vocab_map_shape():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    data = client.get(f"{BASE}/lessons/{lesson.id}/subtitles").json()
    for entry in data["vocabMap"].values():
        assert {"meaning", "expression", "exampleSentence", "exampleTranslation"}.issubset(
            entry.keys()
        )


def test_get_preview_subtitles_cultural_notes_shape():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    data = client.get(f"{BASE}/lessons/{lesson.id}/subtitles").json()
    for note in data["culturalNotes"]:
        assert {"id", "subtitleId", "title", "keyword", "explanation"}.issubset(note.keys())


def test_get_preview_subtitles_non_preview_lesson_404():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db, is_preview=False)

    response = client.get(f"{BASE}/lessons/{lesson.id}/subtitles")
    assert response.status_code == 404


def test_get_preview_subtitles_unknown_id_404():
    response = client.get(f"{BASE}/lessons/9999/subtitles")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "lesson_not_found"


def test_get_preview_subtitles_no_auth_required():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db)

    response = client.get(f"{BASE}/lessons/{lesson.id}/subtitles", headers={})
    assert response.status_code == 200


def test_get_preview_subtitles_empty_vocab_and_notes_when_null():
    with TestingSessionLocal() as db:
        lesson = _make_lesson(db, watch_vocab_json=None, cultural_notes_json=None)

    data = client.get(f"{BASE}/lessons/{lesson.id}/subtitles").json()
    assert data["vocabMap"] == {}
    assert data["culturalNotes"] == []
