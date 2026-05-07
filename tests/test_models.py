from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.user import User
from app.models.video import Video, VideoQuery


def test_user_video_and_query_persist():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

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
