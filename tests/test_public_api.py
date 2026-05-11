"""Tests for the unauthenticated public preview-lesson endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BASE = "/api/public"

# ---------------------------------------------------------------------------
# GET /api/public/preview-lessons
# ---------------------------------------------------------------------------


def test_list_preview_lessons_returns_200():
    response = client.get(f"{BASE}/preview-lessons")
    assert response.status_code == 200


def test_list_preview_lessons_returns_list():
    data = client.get(f"{BASE}/preview-lessons").json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_preview_lessons_item_shape():
    data = client.get(f"{BASE}/preview-lessons").json()
    item = data[0]
    required = {"id", "title", "channelName", "duration", "date", "generationStatus"}
    assert required.issubset(item.keys())


def test_list_preview_lessons_no_auth_required():
    """No Authorization header should still return 200."""
    response = client.get(f"{BASE}/preview-lessons", headers={})
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/public/lessons/{id}/flashcards
# ---------------------------------------------------------------------------


def test_get_preview_flashcards_known_lesson():
    response = client.get(f"{BASE}/lessons/3/flashcards")
    assert response.status_code == 200


def test_get_preview_flashcards_schema():
    data = client.get(f"{BASE}/lessons/3/flashcards").json()
    assert "lessonId" in data
    assert "lessonTitle" in data
    assert isinstance(data["cards"], list)
    assert len(data["cards"]) > 0


def test_get_preview_flashcards_cards_have_required_fields():
    data = client.get(f"{BASE}/lessons/3/flashcards").json()
    for card in data["cards"]:
        assert "id" in card
        assert "type" in card
        assert card["type"] in {"word", "ending"}


def test_get_preview_flashcards_unknown_lesson_404():
    response = client.get(f"{BASE}/lessons/9999/flashcards")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["code"] == "flashcards_not_found"


def test_get_preview_flashcards_no_auth_required():
    response = client.get(f"{BASE}/lessons/3/flashcards", headers={})
    assert response.status_code == 200


@pytest.mark.parametrize("lesson_id", ["3", "4", "5"])
def test_get_preview_flashcards_all_fixture_lessons(lesson_id: str):
    response = client.get(f"{BASE}/lessons/{lesson_id}/flashcards")
    assert response.status_code == 200
    data = response.json()
    assert data["lessonId"] == lesson_id


# ---------------------------------------------------------------------------
# GET /api/public/lessons/{id}/subtitles
# ---------------------------------------------------------------------------


def test_get_preview_subtitles_known_lesson():
    response = client.get(f"{BASE}/lessons/3/subtitles")
    assert response.status_code == 200


def test_get_preview_subtitles_schema():
    data = client.get(f"{BASE}/lessons/3/subtitles").json()
    assert "youtubeId" in data
    assert "durationSec" in data
    assert isinstance(data["lines"], list)
    assert isinstance(data["vocabMap"], dict)
    assert isinstance(data["culturalNotes"], list)


def test_get_preview_subtitles_lines_have_required_fields():
    data = client.get(f"{BASE}/lessons/3/subtitles").json()
    for line in data["lines"]:
        assert "id" in line
        assert "startSec" in line
        assert "endSec" in line
        assert "korean" in line
        assert "english" in line


def test_get_preview_subtitles_vocab_map_entry_shape():
    data = client.get(f"{BASE}/lessons/3/subtitles").json()
    for _key, entry in data["vocabMap"].items():
        assert "meaning" in entry
        assert "expression" in entry
        assert "exampleSentence" in entry
        assert "exampleTranslation" in entry


def test_get_preview_subtitles_cultural_notes_shape():
    data = client.get(f"{BASE}/lessons/3/subtitles").json()
    for note in data["culturalNotes"]:
        assert "id" in note
        assert "subtitleId" in note
        assert "title" in note
        assert "keyword" in note
        assert "explanation" in note


def test_get_preview_subtitles_unknown_lesson_404():
    response = client.get(f"{BASE}/lessons/9999/subtitles")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["code"] == "subtitles_not_found"


def test_get_preview_subtitles_no_auth_required():
    response = client.get(f"{BASE}/lessons/3/subtitles", headers={})
    assert response.status_code == 200


@pytest.mark.parametrize("lesson_id", ["3", "4", "5"])
def test_get_preview_subtitles_all_fixture_lessons(lesson_id: str):
    response = client.get(f"{BASE}/lessons/{lesson_id}/subtitles")
    assert response.status_code == 200
