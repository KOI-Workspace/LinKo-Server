from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.video import Video, VideoQuery
from app.schemas.video import VideoMetadataResponse
from app.services.youtube import (
    extract_video_id,
    fetch_youtube_video_item,
    format_duration,
    parse_iso8601_duration_seconds,
    parse_published_at,
    select_thumbnail_url,
)

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/metadata", response_model=VideoMetadataResponse)
def get_video_metadata(
    url: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoMetadataResponse:
    try:
        youtube_video_id = extract_video_id(url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_youtube_url", "message": "Invalid YouTube URL"},
        ) from exc

    item = fetch_youtube_video_item(youtube_video_id)
    snippet = item["snippet"]
    content_details = item["contentDetails"]
    duration_seconds = parse_iso8601_duration_seconds(content_details["duration"])
    published_at = parse_published_at(snippet.get("publishedAt"))
    thumbnail_url = select_thumbnail_url(snippet.get("thumbnails", {}))

    video = db.scalar(select(Video).where(Video.youtube_video_id == youtube_video_id))
    if video is None:
        video = Video(
            youtube_video_id=youtube_video_id,
            title=snippet["title"],
            channel_title=snippet["channelTitle"],
            thumbnail_url=thumbnail_url,
            duration_seconds=duration_seconds,
            published_at=published_at,
            raw_youtube_response=item,
        )
        db.add(video)
    else:
        video.title = snippet["title"]
        video.channel_title = snippet["channelTitle"]
        video.thumbnail_url = thumbnail_url
        video.duration_seconds = duration_seconds
        video.published_at = published_at
        video.raw_youtube_response = item

    db.flush()
    db.add(VideoQuery(user_id=current_user.id, video_id=video.id, requested_url=url))
    db.commit()
    db.refresh(video)

    return VideoMetadataResponse(
        video_id=video.youtube_video_id,
        title=video.title,
        published_at=published_at,
        thumbnail_url=video.thumbnail_url,
        channel_title=video.channel_title,
        duration_seconds=video.duration_seconds,
        duration_text=format_duration(video.duration_seconds),
        url=url,
    )
