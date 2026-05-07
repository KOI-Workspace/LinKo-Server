from datetime import datetime

from pydantic import BaseModel


class VideoMetadataResponse(BaseModel):
    video_id: str
    title: str
    published_at: datetime | None
    thumbnail_url: str | None
    channel_title: str
    duration_seconds: int
    duration_text: str
    url: str
