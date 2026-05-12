from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.db.session import SessionLocal, get_db
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.lesson import (
    LessonCreateRequest,
    LessonCreateResponse,
    LessonListResponse,
    LessonStatusResponse,
    LessonSummary,
)
from app.services.lesson_artifacts import generate_lesson_artifacts_from_transcript
from app.services.transcripts import download_youtube_captions
from app.services.youtube import (
    extract_video_id,
    fetch_youtube_video_item,
    format_duration,
    parse_iso8601_duration_seconds,
    parse_published_at,
    select_thumbnail_url,
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


def _lesson_summary(lesson: Lesson) -> LessonSummary:
    return LessonSummary(
        id=str(lesson.id),
        title=lesson.title,
        channelName=lesson.channel_title,
        thumbnailUrl=lesson.thumbnail_url,
        duration=format_duration(lesson.duration_seconds),
        date=lesson.created_at.strftime("%Y.%m.%d") if lesson.created_at else None,
        generationStatus=lesson.generation_status,
        flashcardDone=False,
        subtitleDone=False,
        errorCode=lesson.error_code,
        errorMessage=lesson.error_message,
    )


def _get_user_lesson(db: Session, lesson_id: int, user_id: int) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None or lesson.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "lesson_not_found", "message": "Lesson not found"},
        )
    return lesson


@router.post("", response_model=LessonCreateResponse)
def create_lesson(
    request: LessonCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LessonCreateResponse:
    try:
        youtube_video_id = extract_video_id(request.youtube_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_youtube_url", "message": "Invalid YouTube URL"},
        ) from exc

    item = fetch_youtube_video_item(youtube_video_id)
    snippet = item["snippet"]
    duration_seconds = parse_iso8601_duration_seconds(item["contentDetails"]["duration"])
    lesson = Lesson(
        user_id=current_user.id,
        youtube_url=request.youtube_url,
        youtube_video_id=youtube_video_id,
        title=snippet["title"],
        channel_title=snippet["channelTitle"],
        thumbnail_url=select_thumbnail_url(snippet.get("thumbnails", {})),
        duration_seconds=duration_seconds,
        generation_status="generating",
        transcript_status="pending",
        raw_youtube_metadata={
            **item,
            "publishedAt": parse_published_at(snippet.get("publishedAt")).isoformat()
            if snippet.get("publishedAt")
            else None,
        },
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    background_tasks.add_task(generate_lesson_artifacts_task, lesson.id)

    return LessonCreateResponse(
        lessonId=str(lesson.id),
        generationStatus=lesson.generation_status,
    )


@router.get("", response_model=LessonListResponse)
def list_lessons(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LessonListResponse:
    lessons = db.scalars(
        select(Lesson)
        .where(Lesson.user_id == current_user.id)
        .order_by(Lesson.created_at.desc(), Lesson.id.desc())
    ).all()
    return LessonListResponse(lessons=[_lesson_summary(lesson) for lesson in lessons])


@router.get("/{lesson_id}", response_model=LessonStatusResponse)
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LessonStatusResponse:
    lesson = _get_user_lesson(db, lesson_id, current_user.id)
    summary = _lesson_summary(lesson).model_dump()
    return LessonStatusResponse(
        **summary,
        transcriptStatus=lesson.transcript_status,
        transcriptSource=lesson.transcript_source,
    )


@router.get("/{lesson_id}/subtitles")
def get_lesson_subtitles(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    lesson = _get_user_lesson(db, lesson_id, current_user.id)
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
    if lesson.subtitles_json is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "subtitles_not_found", "message": "Subtitles are not available"},
        )
    return {
        **lesson.subtitles_json,
        "vocabMap": lesson.watch_vocab_json or {},
        "culturalNotes": lesson.cultural_notes_json or [],
    }


@router.patch("/{lesson_id}/preview", response_model=LessonSummary)
def set_lesson_preview(
    lesson_id: int,
    is_preview: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LessonSummary:
    """Mark or unmark a lesson as a public landing-page preview.

    The lesson must belong to the requesting user (or an admin in the future).
    When is_preview=true, the lesson becomes accessible without authentication
    via GET /public/lessons/{id}/flashcards and /subtitles.
    """
    lesson = _get_user_lesson(db, lesson_id, current_user.id)
    lesson.is_preview = is_preview
    db.commit()
    db.refresh(lesson)
    return _lesson_summary(lesson)


def generate_lesson_artifacts_task(lesson_id: int) -> None:
    db = SessionLocal()
    try:
        lesson = db.get(Lesson, lesson_id)
        if lesson is None:
            return

        end_sec = min(lesson.duration_seconds, 600)
        with TemporaryDirectory() as tmp_dir:
            transcript = download_youtube_captions(
                lesson.youtube_url,
                Path(tmp_dir),
                lang="ko",
                start_sec=0,
                end_sec=end_sec,
                allow_auto=True,
            )

        if transcript is None:
            lesson.generation_status = "failed"
            lesson.transcript_status = "unavailable"
            lesson.error_code = "transcript_unavailable"
            lesson.error_message = "Korean captions are not available for this video yet."
            lesson.transcript_error_code = "transcript_unavailable"
            lesson.transcript_error_message = lesson.error_message
            db.commit()
            return

        artifacts = generate_lesson_artifacts_from_transcript(
            lesson_id=str(lesson.id),
            lesson_title=lesson.title,
            youtube_id=lesson.youtube_video_id,
            duration_seconds=lesson.duration_seconds,
            transcript=transcript,
        )
        lesson.transcript_status = "ready"
        lesson.transcript_source = transcript.source
        lesson.transcript_text = transcript.text
        lesson.caption_segments_json = [
            {
                "startSec": segment.start_sec,
                "endSec": segment.end_sec,
                "text": segment.text,
            }
            for segment in transcript.segments
        ]
        lesson.flashcards_json = artifacts.flashcards
        lesson.subtitles_json = artifacts.subtitles
        lesson.watch_vocab_json = artifacts.watch_vocab
        lesson.cultural_notes_json = artifacts.cultural_notes
        lesson.generation_status = "ready"
        lesson.error_code = None
        lesson.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        lesson = db.get(Lesson, lesson_id)
        if lesson is not None:
            lesson.generation_status = "failed"
            lesson.error_code = "generation_failed"
            lesson.error_message = str(exc)
            db.commit()
    finally:
        db.close()
