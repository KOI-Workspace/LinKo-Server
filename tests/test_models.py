import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys
from app.models.user import User
from app.models.video import Video, VideoQuery


def create_model_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    Base.metadata.create_all(engine)
    return engine


def test_user_video_and_query_persist():
    engine = create_model_engine()

    try:
        with Session(engine) as session:
            user = User(
                google_sub="google-123",
                email="person@example.com",
                name="Person",
                picture="https://example.com/pic.png",
            )
            video = Video(
                youtube_video_id="abc123",
                title="Video",
                channel_title="Channel",
                thumbnail_url="https://example.com/thumb.jpg",
                duration_seconds=754,
                published_at=None,
                raw_youtube_response={"id": "abc123"},
            )
            session.add_all([user, video])
            session.flush()
            session.add(
                VideoQuery(
                    user_id=user.id,
                    video_id=video.id,
                    requested_url="https://youtu.be/abc123",
                )
            )
            session.commit()

        with Session(engine) as session:
            saved_user = session.scalar(select(User).where(User.google_sub == "google-123"))
            saved_video = session.scalar(
                select(Video).where(Video.youtube_video_id == "abc123")
            )
            query = session.scalar(select(VideoQuery))

        assert saved_user is not None
        assert saved_user.email == "person@example.com"
        assert saved_video is not None
        assert saved_video.raw_youtube_response == {"id": "abc123"}
        assert query is not None
        assert query.user_id == saved_user.id
        assert query.video_id == saved_video.id
    finally:
        engine.dispose()


def test_sqlite_rejects_video_query_with_missing_user_or_video():
    engine = create_model_engine()

    try:
        with Session(engine) as session:
            session.add(
                VideoQuery(
                    user_id=999,
                    video_id=999,
                    requested_url="https://youtu.be/missing",
                )
            )

            with pytest.raises(IntegrityError):
                session.commit()
    finally:
        engine.dispose()


def test_raw_youtube_response_in_place_mutation_persists():
    engine = create_model_engine()

    try:
        with Session(engine) as session:
            video = Video(
                youtube_video_id="mutable",
                title="Mutable Video",
                channel_title="Channel",
                thumbnail_url=None,
                duration_seconds=42,
                published_at=None,
                raw_youtube_response={"id": "mutable"},
            )
            session.add(video)
            session.commit()
            video_id = video.id

        with Session(engine) as session:
            saved_video = session.get(Video, video_id)
            assert saved_video is not None
            saved_video.raw_youtube_response["title"] = "Updated in place"
            session.commit()

        with Session(engine) as session:
            reloaded_video = session.get(Video, video_id)

        assert reloaded_video is not None
        assert reloaded_video.raw_youtube_response == {
            "id": "mutable",
            "title": "Updated in place",
        }
    finally:
        engine.dispose()


def test_timestamps_are_populated():
    engine = create_model_engine()

    try:
        with Session(engine) as session:
            user = User(
                google_sub="timestamp-user",
                email="timestamp@example.com",
                name="Timestamp",
                picture=None,
            )
            video = Video(
                youtube_video_id="timestamp-video",
                title="Timestamp Video",
                channel_title="Channel",
                thumbnail_url=None,
                duration_seconds=1,
                published_at=None,
                raw_youtube_response={"id": "timestamp-video"},
            )
            session.add_all([user, video])
            session.commit()
            user_id = user.id
            video_id = video.id

        with Session(engine) as session:
            saved_user = session.get(User, user_id)
            saved_video = session.get(Video, video_id)

        assert saved_user is not None
        assert saved_user.created_at is not None
        assert saved_user.updated_at is not None
        assert saved_video is not None
        assert saved_video.created_at is not None
        assert saved_video.updated_at is not None
    finally:
        engine.dispose()
