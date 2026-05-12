from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class YoutubeChannel(Base):
    __tablename__ = "youtube_channels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    youtube_channel_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    country: Mapped[str | None] = mapped_column(String(16), nullable=True)
    default_language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    raw_youtube_response: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSON))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class UserYoutubeChannel(Base):
    __tablename__ = "user_youtube_channels"
    __table_args__ = (
        UniqueConstraint("user_id", "youtube_channel_id", name="uq_user_youtube_channel"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    youtube_channel_id: Mapped[int] = mapped_column(ForeignKey("youtube_channels.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
