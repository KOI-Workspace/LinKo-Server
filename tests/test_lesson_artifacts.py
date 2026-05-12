import pytest

from app.services.lesson_artifacts import (
    ArtifactValidationError,
    generate_lesson_artifacts_from_transcript,
    _parse_gemini_json,
    validate_lesson_artifacts,
)
from app.services.transcripts import TranscriptResult, TranscriptSegment


def sample_transcript() -> TranscriptResult:
    return TranscriptResult(
        source="youtube_caption",
        text=(
            "안녕하세요. 오늘은 서울의 길거리 음식을 함께 즐겨볼게요.\n"
            "이 시장은 현지인도 자주 와서 맛있는 음식 가게로 가득해요."
        ),
        segments=[
            TranscriptSegment(
                start_sec=0,
                end_sec=5,
                text="안녕하세요. 오늘은 서울의 길거리 음식을 함께 즐겨볼게요.",
            ),
            TranscriptSegment(
                start_sec=5,
                end_sec=10,
                text="이 시장은 현지인도 자주 와서 맛있는 음식 가게로 가득해요.",
            ),
        ],
    )


def test_generate_lesson_artifacts_returns_frontend_contract(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")

    artifacts = generate_lesson_artifacts_from_transcript(
        lesson_id="42",
        lesson_title="Example Lesson",
        youtube_id="abc123XYZ00",
        duration_seconds=10,
        transcript=sample_transcript(),
    )

    assert artifacts.flashcards["lessonId"] == "42"
    assert artifacts.flashcards["lessonTitle"] == "Example Lesson"
    assert artifacts.flashcards["cards"][0]["type"] == "word"
    assert artifacts.flashcards["cards"][0]["video"] == {
        "youtubeId": "abc123XYZ00",
        "startSec": 0,
        "endSec": 5,
    }
    assert artifacts.subtitles["youtubeId"] == "abc123XYZ00"
    assert artifacts.subtitles["lines"][0]["korean"].startswith("안녕하세요")
    assert "안녕하세요" in artifacts.watch_vocab
    assert artifacts.cultural_notes[0]["subtitleId"] == "s1"


def test_validate_lesson_artifacts_rejects_missing_required_shapes():
    with pytest.raises(ArtifactValidationError, match="flashcards.cards"):
        validate_lesson_artifacts(
            {
                "flashcards": {"lessonId": "1", "lessonTitle": "Bad"},
                "subtitles": {"youtubeId": "abc", "durationSec": 1, "lines": []},
            }
        )

    with pytest.raises(ArtifactValidationError, match="subtitles.lines"):
        validate_lesson_artifacts(
            {
                "flashcards": {"lessonId": "1", "lessonTitle": "Bad", "cards": []},
                "subtitles": {"youtubeId": "abc", "durationSec": 1},
            }
        )


def test_parse_gemini_json_repairs_trailing_commas():
    payload = """
    {
      "flashcards": {
        "cards": [
          {"id": "1", "text": "comma, inside string is kept",}
        ],
      },
      "subtitles": {
        "lines": [],
      },
    }
    """

    parsed = _parse_gemini_json(payload)

    assert parsed["flashcards"]["cards"][0]["text"] == "comma, inside string is kept"
    assert parsed["subtitles"]["lines"] == []
