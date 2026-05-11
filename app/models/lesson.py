from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    youtube_url: Mapped[str] = mapped_column(Text)
    youtube_video_id: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(500))
    channel_title: Mapped[str] = mapped_column(String(255))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    generation_status: Mapped[str] = mapped_column(String(32), index=True, default="generating")
    transcript_status: Mapped[str] = mapped_column(String(32), default="pending")
    transcript_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    transcript_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    caption_segments_json: Mapped[list | None] = mapped_column(
        MutableList.as_mutable(JSON), nullable=True
    )
    flashcards_json: Mapped[dict | None] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )
    subtitles_json: Mapped[dict | None] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )
    watch_vocab_json: Mapped[dict | None] = mapped_column(
        MutableDict.as_mutable(JSON), nullable=True
    )
    cultural_notes_json: Mapped[list | None] = mapped_column(
        MutableList.as_mutable(JSON), nullable=True
    )
    raw_youtube_metadata: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transcript_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
