import pytest

from app.core.config import get_settings
from app.services.lesson_artifacts import (
    ArtifactValidationError,
    FLASHCARD_TRANSCRIPT_MAX_CHARS,
    build_subtitle_artifacts,
    generate_lesson_artifacts_from_transcript,
    limit_transcript_for_flashcards,
    sample_transcript_for_flashcards,
    _parse_gemini_json,
    validate_lesson_artifacts,
    validate_watch_enrichments,
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
    get_settings.cache_clear()

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
    assert artifacts.subtitles["lines"][0]["english"] == ""
    assert "안녕하세요" in artifacts.watch_vocab
    assert artifacts.watch_vocab["안녕하세요"]["cardId"] == "fc-42-1"
    assert artifacts.cultural_notes[0]["subtitleId"] == "s1"
    get_settings.cache_clear()


def test_build_subtitle_artifacts_merges_overlapping_english_segments():
    english_transcript = TranscriptResult(
        source="youtube_caption",
        text="Hello. Today we study Korean.",
        lang="en",
        segments=[
            TranscriptSegment(start_sec=0, end_sec=2, text="Hello."),
            TranscriptSegment(start_sec=2, end_sec=5, text="Today we study Korean."),
        ],
    )

    subtitles = build_subtitle_artifacts(
        youtube_id="abc123XYZ00",
        duration_seconds=10,
        transcript=sample_transcript(),
        english_transcript=english_transcript,
    )

    assert subtitles["lines"][0]["english"] == "Hello. Today we study Korean."
    assert subtitles["lines"][1]["english"] == ""


def test_flashcard_transcript_is_limited_to_safe_duration_and_character_count():
    transcript = TranscriptResult(
        source="youtube_caption",
        text="",
        segments=[
            TranscriptSegment(start_sec=0, end_sec=120, text="가" * 6000),
            TranscriptSegment(start_sec=120, end_sec=240, text="나" * 6000),
            TranscriptSegment(start_sec=240, end_sec=360, text="다" * 6000),
        ],
    )

    limited = limit_transcript_for_flashcards(transcript)

    assert limited.segments[-1].end_sec <= 180
    assert len(limited.text) <= FLASHCARD_TRANSCRIPT_MAX_CHARS + len(limited.segments)
    assert all(segment.start_sec < 180 for segment in limited.segments)


def test_flashcard_transcript_sampling_is_deterministic_and_not_always_the_start():
    transcript = TranscriptResult(
        source="youtube_caption",
        text="",
        segments=[
            TranscriptSegment(start_sec=i * 30, end_sec=(i + 1) * 30, text=f"구간{i}")
            for i in range(40)
        ],
    )

    first = sample_transcript_for_flashcards(transcript, seed="lesson:abc")
    second = sample_transcript_for_flashcards(transcript, seed="lesson:abc")

    assert first.segments == second.segments
    assert first.segments[0].start_sec > 0
    covered_seconds = sum(segment.end_sec - segment.start_sec for segment in first.segments)
    assert covered_seconds <= 180


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


def test_validate_watch_enrichments_rejects_bad_shapes():
    with pytest.raises(ArtifactValidationError, match="watch.vocabMap"):
        validate_watch_enrichments({"watch": {"vocabMap": []}})

    with pytest.raises(ArtifactValidationError, match="watch.culturalNotes"):
        validate_watch_enrichments({"watch": {"culturalNotes": {}}})


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
