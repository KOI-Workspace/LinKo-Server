from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.youtube_channel import UserYoutubeChannel, YoutubeChannel
from app.schemas.youtube_channel import (
    YoutubeChannelListResponse,
    YoutubeChannelResponse,
    YoutubeChannelSyncRequest,
)
from app.services.youtube import (
    fetch_user_subscription_channel_ids,
    fetch_youtube_channels,
    is_korean_channel,
    select_thumbnail_url,
)

router = APIRouter(prefix="/youtube", tags=["youtube"])


def channel_response(
    channel: YoutubeChannel,
    user_channel: UserYoutubeChannel,
) -> YoutubeChannelResponse:
    return YoutubeChannelResponse(
        youtube_channel_id=channel.youtube_channel_id,
        title=channel.title,
        thumbnail_url=channel.thumbnail_url,
        country=channel.country,
        default_language=channel.default_language,
        added_at=user_channel.created_at,
    )


def list_user_channels(db: Session, user_id: int) -> YoutubeChannelListResponse:
    rows = db.execute(
        select(YoutubeChannel, UserYoutubeChannel)
        .join(
            UserYoutubeChannel,
            UserYoutubeChannel.youtube_channel_id == YoutubeChannel.id,
        )
        .where(UserYoutubeChannel.user_id == user_id)
        .order_by(UserYoutubeChannel.created_at.desc())
    ).all()
    return YoutubeChannelListResponse(
        channels=[channel_response(channel, user_channel) for channel, user_channel in rows]
    )


@router.post("/channels/sync", response_model=YoutubeChannelListResponse)
def sync_youtube_channels(
    request: YoutubeChannelSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YoutubeChannelListResponse:
    channel_ids = fetch_user_subscription_channel_ids(request.access_token)
    channel_items = fetch_youtube_channels(channel_ids)

    for item in channel_items:
        if not is_korean_channel(item):
            continue

        snippet = item.get("snippet", {})
        branding_channel = item.get("brandingSettings", {}).get("channel", {})
        youtube_channel_id = item["id"]
        channel = db.scalar(
            select(YoutubeChannel).where(
                YoutubeChannel.youtube_channel_id == youtube_channel_id
            )
        )
        if channel is None:
            channel = YoutubeChannel(
                youtube_channel_id=youtube_channel_id,
                title=snippet["title"],
                thumbnail_url=select_thumbnail_url(snippet.get("thumbnails", {})),
                country=branding_channel.get("country"),
                default_language=snippet.get("defaultLanguage"),
                raw_youtube_response=item,
            )
            db.add(channel)
            db.flush()
        else:
            channel.title = snippet["title"]
            channel.thumbnail_url = select_thumbnail_url(snippet.get("thumbnails", {}))
            channel.country = branding_channel.get("country")
            channel.default_language = snippet.get("defaultLanguage")
            channel.raw_youtube_response = item

        existing_link = db.scalar(
            select(UserYoutubeChannel).where(
                UserYoutubeChannel.user_id == current_user.id,
                UserYoutubeChannel.youtube_channel_id == channel.id,
            )
        )
        if existing_link is None:
            db.add(
                UserYoutubeChannel(
                    user_id=current_user.id,
                    youtube_channel_id=channel.id,
                )
            )

    db.commit()
    return list_user_channels(db, current_user.id)


@router.get("/channels", response_model=YoutubeChannelListResponse)
def get_youtube_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> YoutubeChannelListResponse:
    return list_user_channels(db, current_user.id)
