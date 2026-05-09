from datetime import datetime

from pydantic import BaseModel, Field


class YoutubeChannelSyncRequest(BaseModel):
    access_token: str = Field(min_length=1)


class YoutubeChannelResponse(BaseModel):
    youtube_channel_id: str
    title: str
    thumbnail_url: str | None
    country: str | None
    default_language: str | None
    added_at: datetime


class YoutubeChannelListResponse(BaseModel):
    channels: list[YoutubeChannelResponse]
