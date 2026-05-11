from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WaitlistCreateRequest(BaseModel):
    youtube_url: str = Field(alias="youtubeUrl", min_length=1)
    source: str = "landing_early_access"


class WaitlistEntryResponse(BaseModel):
    id: int
    user_id: int
    email: str
    name: str
    picture: str | None
    youtube_url: str
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
