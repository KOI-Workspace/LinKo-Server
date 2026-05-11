"""Public (unauthenticated) landing-page endpoints.

GET /public/preview-lessons                → curated preview lesson list
GET /public/lessons/{lesson_id}/flashcards → flashcard data  (same schema as /lessons/{id}/flashcards)
GET /public/lessons/{lesson_id}/subtitles  → subtitle data   (same schema as /lessons/{id}/subtitles)

All three endpoints require NO bearer token.  They only serve lessons that
have been explicitly marked is_preview=True by an admin via the
PATCH /lessons/{id}/preview endpoint.

Per-user fields (bookmarks, saved state, etc.) are always empty / false.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lesson import Lesson
from app.schemas.flashcard import LessonFlashcardsResponse
from app.schemas.lesson import LessonSummary
from app.services.youtube import format_duration

router = APIRouter(prefix="/public", tags=["public"])


def _lesson_to_summary(lesson: Lesson) -> LessonSummary:
    return LessonSummary(
        id=str(lesson.id),
        title=lesson.title,
        channelName=lesson.channel_title,
        thumbnailUrl=lesson.thumbnail_url,
        duration=format_duration(lesson.duration_seconds),
        date=lesson.created_at.strftime("%Y.%m.%d") if lesson.created_at else None,
        generationStatus=lesson.generation_status,
        flashcardDone=lesson.flashcards_json is not None,
        subtitleDone=lesson.subtitles_json is not None,
        errorCode=lesson.error_code,
        errorMessage=lesson.error_message,
    )


def _get_ready_preview_lesson(db: Session, lesson_id: str) -> Lesson:
    """Return the lesson only if it is a ready preview lesson, else raise."""
    if not lesson_id.isdigit():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "lesson_not_found", "message": "Preview lesson not found"},
        )
    lesson = db.get(Lesson, int(lesson_id))
    if lesson is None or not lesson.is_preview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "lesson_not_found", "message": "Preview lesson not found"},
        )
    if lesson.generation_status == "generating":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "lesson_not_ready", "message": "Lesson is still generating"},
        )
    if lesson.generation_status == "failed":
        raise HTTPException(
            status_code=422,
            detail={
                "code": "lesson_generation_failed",
                "message": lesson.error_message or "Lesson generation failed",
            },
        )
    return lesson


# ---------------------------------------------------------------------------
# Preview lesson list (replaces hard-coded VIDEO_EXAMPLES on the client)
# ---------------------------------------------------------------------------


@router.get("/preview-lessons", response_model=list[LessonSummary])
def list_preview_lessons(db: Session = Depends(get_db)) -> list[LessonSummary]:
    """Return all lessons marked is_preview=True, ordered by creation date desc."""
    lessons = db.scalars(
        select(Lesson)
        .where(Lesson.is_preview == True)  # noqa: E712
        .where(Lesson.generation_status == "ready")
        .order_by(Lesson.created_at.desc())
    ).all()
    return [_lesson_to_summary(lesson) for lesson in lessons]


# ---------------------------------------------------------------------------
# Flashcard data for a preview lesson
# ---------------------------------------------------------------------------


@router.get(
    "/lessons/{lesson_id}/flashcards",
    response_model=LessonFlashcardsResponse,
)
def get_preview_flashcards(
    lesson_id: str,
    db: Session = Depends(get_db),
) -> LessonFlashcardsResponse | dict:
    """Return flashcard data for a preview lesson without authentication."""
    lesson = _get_ready_preview_lesson(db, lesson_id)
    if lesson.flashcards_json is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "flashcards_not_found",
                "message": "Flashcards are not available for this preview lesson.",
            },
        )
    return lesson.flashcards_json


# ---------------------------------------------------------------------------
# Subtitle / watch data for a preview lesson
# ---------------------------------------------------------------------------


@router.get("/lessons/{lesson_id}/subtitles")
def get_preview_subtitles(
    lesson_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """Return subtitle + vocabMap + culturalNotes for a preview lesson without authentication."""
    lesson = _get_ready_preview_lesson(db, lesson_id)
    if lesson.subtitles_json is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "subtitles_not_found",
                "message": "Subtitles are not available for this preview lesson.",
            },
        )
    return {
        **lesson.subtitles_json,
        "vocabMap": lesson.watch_vocab_json or {},
        "culturalNotes": lesson.cultural_notes_json or [],
    }
