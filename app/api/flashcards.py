from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.db.session import get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.flashcard import LessonFlashcardsResponse
from app.services.flashcards import get_lesson_flashcards

router = APIRouter(prefix="/lessons", tags=["flashcards"])


@router.get("/{lesson_id}/flashcards", response_model=LessonFlashcardsResponse)
def get_flashcards_for_lesson(
    lesson_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LessonFlashcardsResponse | dict:
    if lesson_id.isdigit():
        lesson = db.get(Lesson, int(lesson_id))
        if lesson is not None and lesson.user_id == current_user.id:
            if lesson.generation_status == "generating":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "code": "lesson_not_ready",
                        "message": "Lesson is still generating",
                    },
                )
            if lesson.generation_status == "failed":
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": "lesson_generation_failed",
                        "message": lesson.error_message or "Lesson generation failed",
                    },
                )
            if lesson.flashcards_json is not None:
                return lesson.flashcards_json

    flashcards = get_lesson_flashcards(lesson_id)
    if flashcards is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "flashcards_not_found",
                "message": "Flashcards are not available for this lesson.",
            },
        )

    return flashcards
