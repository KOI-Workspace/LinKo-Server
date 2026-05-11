"""Public (unauthenticated) landing-page endpoints.

GET /public/preview-lessons          → preview lesson list
GET /public/lessons/{id}/flashcards  → flashcard data (same schema as /lessons/{id}/flashcards)
GET /public/lessons/{id}/subtitles   → subtitle data  (same schema as /lessons/{id}/subtitles)

All three endpoints require NO bearer token.  Per-user data (bookmarks,
saved-state, etc.) is always returned as empty / false.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.flashcard import LessonFlashcardsResponse
from app.schemas.lesson import LessonSummary
from app.services.flashcards import get_lesson_flashcards
from app.services.subtitles import get_public_subtitles

router = APIRouter(prefix="/public", tags=["public"])

# ---------------------------------------------------------------------------
# Preview-lesson list (replaces the hard-coded VIDEO_EXAMPLES on the client)
# ---------------------------------------------------------------------------
_PREVIEW_LESSONS: list[dict] = [
    {
        "id": "3",
        "title": "Korean Street Food Tour Seoul",
        "channelName": "Korean Vlog Daily",
        "profileImageUrl": None,
        "duration": "8:15",
        "date": "2026.05.07",
        "generationStatus": "ready",
        "flashcardDone": True,
        "subtitleDone": True,
    },
    {
        "id": "4",
        "title": "K-drama Vocabulary Basics",
        "channelName": "Talk To Me In Korean",
        "profileImageUrl": None,
        "duration": "6:30",
        "date": "2026.05.06",
        "generationStatus": "ready",
        "flashcardDone": True,
        "subtitleDone": True,
    },
    {
        "id": "5",
        "title": "Learn Korean with BLACKPINK",
        "channelName": "BLACKPINK",
        "profileImageUrl": None,
        "duration": "5:00",
        "date": "2026.05.05",
        "generationStatus": "ready",
        "flashcardDone": True,
        "subtitleDone": True,
    },
]


@router.get("/preview-lessons", response_model=list[LessonSummary])
def list_preview_lessons() -> list[dict]:
    """Return the curated list of preview lessons shown on the landing page."""
    return _PREVIEW_LESSONS


# ---------------------------------------------------------------------------
# Flashcard data for a preview lesson
# ---------------------------------------------------------------------------
@router.get(
    "/lessons/{lesson_id}/flashcards",
    response_model=LessonFlashcardsResponse,
)
def get_preview_flashcards(lesson_id: str) -> LessonFlashcardsResponse | dict:
    """Return flashcard data for a preview lesson without authentication."""
    flashcards = get_lesson_flashcards(lesson_id)
    if flashcards is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "flashcards_not_found",
                "message": "Flashcards are not available for this preview lesson.",
            },
        )
    return flashcards


# ---------------------------------------------------------------------------
# Subtitle / watch data for a preview lesson
# ---------------------------------------------------------------------------
@router.get("/lessons/{lesson_id}/subtitles")
def get_preview_subtitles(lesson_id: str) -> dict:
    """Return subtitle + vocabMap + culturalNotes for a preview lesson without authentication."""
    subtitles = get_public_subtitles(lesson_id)
    if subtitles is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "subtitles_not_found",
                "message": "Subtitles are not available for this preview lesson.",
            },
        )
    return subtitles
