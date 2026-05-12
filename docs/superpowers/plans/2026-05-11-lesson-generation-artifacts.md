# Lesson Generation Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the MVP YouTube URL to generated lesson artifact pipeline using FastAPI `BackgroundTasks`, YouTube captions, Gemini-ready artifact generation, and DB-backed flashcard/subtitle APIs.

**Architecture:** Add a `Lesson` model with status and JSON artifact fields. `POST /api/lessons` creates a generating lesson and schedules `generate_lesson_artifacts`; that task acquires transcript data, generates validated flashcard/watch artifacts, and stores them. Artifact read endpoints return stored JSON or status-specific errors.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, Pydantic, `yt-dlp` subprocess calls, Gemini REST API via stdlib/httpx-compatible boundaries, pytest.

---

### Task 1: Lesson Model and Migration

**Files:**
- Create: `app/models/lesson.py`
- Modify: `app/models/__init__.py`
- Create: `alembic/versions/20260511_0003_create_lessons.py`
- Test: `tests/test_lesson_models.py`

- [ ] **Step 1: Write model tests**

Create `tests/test_lesson_models.py`:

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys
from app.models.lesson import Lesson
from app.models.user import User


def test_lesson_persists_generation_artifacts():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as session:
        user = User(
            google_sub="google-lesson",
            email="lesson@example.com",
            name="Lesson User",
            picture=None,
        )
        session.add(user)
        session.flush()

        lesson = Lesson(
            user_id=user.id,
            youtube_url="https://youtu.be/abc123XYZ00",
            youtube_video_id="abc123XYZ00",
            title="Example Korean Lesson",
            channel_title="Example Channel",
            thumbnail_url="https://example.com/thumb.jpg",
            duration_seconds=123,
            generation_status="ready",
            transcript_status="ready",
            transcript_source="youtube_caption",
            transcript_text="안녕하세요.",
            caption_segments_json=[{"startSec": 0, "endSec": 2, "text": "안녕하세요."}],
            flashcards_json={"lessonId": "1", "lessonTitle": "Example Korean Lesson", "cards": []},
            subtitles_json={"youtubeId": "abc123XYZ00", "durationSec": 123, "lines": []},
            watch_vocab_json={},
            cultural_notes_json=[],
            raw_youtube_metadata={"id": "abc123XYZ00"},
        )
        session.add(lesson)
        session.commit()

    with TestingSessionLocal() as session:
        saved = session.scalar(select(Lesson).where(Lesson.youtube_video_id == "abc123XYZ00"))

    assert saved is not None
    assert saved.flashcards_json["lessonTitle"] == "Example Korean Lesson"
    assert saved.caption_segments_json[0]["text"] == "안녕하세요."
    assert saved.created_at is not None
    assert saved.updated_at is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_lesson_models.py -v`

Expected: FAIL because `app.models.lesson` does not exist.

- [ ] **Step 3: Implement model and migration**

Create `app/models/lesson.py` with a SQLAlchemy model matching the spec. Import it in `app/models/__init__.py` so `Base.metadata.create_all` sees it in tests. Create Alembic revision `20260511_0003_create_lessons.py` with the same columns, indexes on `id`, `user_id`, `youtube_video_id`, and `generation_status`, and downgrade that drops them.

- [ ] **Step 4: Run model tests**

Run: `python3 -m pytest tests/test_lesson_models.py -v`

Expected: PASS.

### Task 2: Transcript Provider

**Files:**
- Create: `app/services/transcripts.py`
- Test: `tests/test_transcripts.py`

- [ ] **Step 1: Write transcript parsing tests**

Create tests for `parse_vtt`, `filter_segments`, `clean_caption_text`, and caption source selection. Use a temporary VTT file containing two Korean caption cues and assert parsed timings/text. Use monkeypatching for command execution when testing `download_youtube_captions`.

- [ ] **Step 2: Run transcript tests to verify failure**

Run: `python3 -m pytest tests/test_transcripts.py -v`

Expected: FAIL because `app.services.transcripts` does not exist.

- [ ] **Step 3: Implement transcript provider**

Port the safe parts of the POC caption module:

```python
@dataclass(frozen=True)
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    source: Literal["youtube_caption", "youtube_auto_caption"]
    text: str
    segments: list[TranscriptSegment]
```

Implement `parse_vtt`, `filter_segments`, `download_youtube_captions`, and a small `run_command` wrapper around `subprocess.run`. Keep STT out of this task.

- [ ] **Step 4: Run transcript tests**

Run: `python3 -m pytest tests/test_transcripts.py -v`

Expected: PASS.

### Task 3: Artifact Generator

**Files:**
- Create: `app/services/lesson_artifacts.py`
- Modify: `app/core/config.py`
- Test: `tests/test_lesson_artifacts.py`

- [ ] **Step 1: Write artifact generation tests**

Test that `generate_lesson_artifacts_from_transcript` returns the existing frontend contracts when `AI_PROVIDER=mock` or no Gemini key exists. Test that validation rejects missing `flashcards.cards` and missing `subtitles.lines`.

- [ ] **Step 2: Run artifact tests to verify failure**

Run: `python3 -m pytest tests/test_lesson_artifacts.py -v`

Expected: FAIL because `app.services.lesson_artifacts` does not exist.

- [ ] **Step 3: Implement artifact generator**

Add settings: `ai_provider`, `gemini_api_key`, `gemini_model`. Implement:

```python
def generate_lesson_artifacts_from_transcript(
    lesson_id: str,
    lesson_title: str,
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
) -> LessonArtifacts:
```

For MVP tests and local development, return deterministic mock artifacts derived from transcript segments when Gemini is not configured. Include Gemini request construction with response schema-ready prompt, but keep tests monkeypatched and offline.

- [ ] **Step 4: Run artifact tests**

Run: `python3 -m pytest tests/test_lesson_artifacts.py -v`

Expected: PASS.

### Task 4: Lessons API and Background Orchestration

**Files:**
- Create: `app/schemas/lesson.py`
- Create: `app/api/lessons.py`
- Modify: `app/main.py`
- Modify: `app/api/flashcards.py`
- Create: `tests/test_lessons_api.py`
- Modify: `README.md`

- [ ] **Step 1: Write API tests**

Cover authentication, `POST /api/lessons`, ready lesson listing, `GET /api/lessons/{id}`, `GET /api/lessons/{id}/flashcards`, `GET /api/lessons/{id}/subtitles`, `409` while generating, and `422` when failed.

- [ ] **Step 2: Run API tests to verify failure**

Run: `python3 -m pytest tests/test_lessons_api.py -v`

Expected: FAIL because `app.api.lessons` does not exist.

- [ ] **Step 3: Implement schemas and routes**

Add Pydantic schemas using frontend camelCase response fields. `POST /api/lessons` should accept `youtubeUrl`, create a `Lesson`, schedule `generate_lesson_artifacts_task`, and return `lessonId` plus `generationStatus`.

- [ ] **Step 4: Implement background task**

In `app/api/lessons.py` or a focused `app/services/lesson_generation.py`, implement `generate_lesson_artifacts_task(lesson_id: int)` that opens its own DB session, fetches metadata, downloads transcript, generates artifacts, stores JSON, and records stable failure codes.

- [ ] **Step 5: Connect flashcard endpoint to DB**

Update `GET /api/lessons/{lesson_id}/flashcards` to prefer stored DB artifacts. Remove fixture-only behavior or keep fixtures only as fallback for existing IDs if tests require it.

- [ ] **Step 6: Run API tests**

Run: `python3 -m pytest tests/test_lessons_api.py tests/test_flashcards_api.py -v`

Expected: PASS.

### Task 5: Full Verification

**Files:**
- Existing tests and docs.

- [ ] **Step 1: Run full test suite**

Run: `python3 -m pytest`

Expected: all tests pass.

- [ ] **Step 2: Compile Python files**

Run: `python3 -m compileall app tests`

Expected: no syntax errors.

- [ ] **Step 3: Review git status**

Run: `git status --short`

Expected: only intended implementation, tests, migration, and docs are changed.
