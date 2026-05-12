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
            flashcards_json={
                "lessonId": "1",
                "lessonTitle": "Example Korean Lesson",
                "cards": [],
            },
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
