from datetime import datetime
from urllib.parse import parse_qs, urlparse
import re

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,}$")
DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]
        else:
            video_id = ""
    else:
        video_id = ""

    if not YOUTUBE_ID_PATTERN.match(video_id):
        raise ValueError("Invalid YouTube URL")
    return video_id


def parse_iso8601_duration_seconds(duration: str) -> int:
    match = DURATION_PATTERN.match(duration)
    if match is None:
        raise ValueError("Invalid YouTube duration")
    return (
        int(match.group("hours") or 0) * 3600
        + int(match.group("minutes") or 0) * 60
        + int(match.group("seconds") or 0)
    )


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def select_thumbnail_url(thumbnails: dict) -> str | None:
    for key in ("maxres", "standard", "high", "medium", "default"):
        image = thumbnails.get(key)
        if image and image.get("url"):
            return image["url"]
    return None


def fetch_youtube_video_item(video_id: str) -> dict:
    settings = get_settings()

    try:
        response = httpx.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet,contentDetails,status",
                "id": video_id,
                "key": settings.youtube_api_key,
            },
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "youtube_upstream_failed",
                "message": "YouTube metadata lookup failed",
            },
        ) from exc

    items = payload.get("items", [])
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "youtube_video_not_found", "message": "YouTube video not found"},
        )
    return items[0]


def validate_video_item(item: dict):
    """
    영상 메타데이터를 기반으로 LinKo 지원 여부를 검증합니다.
    """
    content_details = item.get("contentDetails", {})
    status_info = item.get("status", {})

    # 1. 360도 영상 체크
    if content_details.get("projection") == "360":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "360_video_not_supported",
                "message": "360 degree videos are not supported yet.",
            },
        )

    # 2. 영상 길이 체크 (2시간 = 7200초)
    duration_str = content_details.get("duration", "PT0S")
    duration_secs = parse_iso8601_duration_seconds(duration_str)
    if duration_secs > 7200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "video_too_long",
                "message": "Videos longer than 2 hours are not supported.",
            },
        )

    # 3. 외부 재생 차단 체크
    if not status_info.get("embeddable", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "embedding_blocked",
                "message": "This video blocks external playback.",
            },
        )


def fetch_user_subscription_channel_ids(access_token: str) -> list[str]:
    channel_ids: list[str] = []
    page_token: str | None = None

    while True:
        params = {"part": "snippet", "mine": "true", "maxResults": "50"}
        if page_token:
            params["pageToken"] = page_token

        try:
            response = httpx.get(
                "https://www.googleapis.com/youtube/v3/subscriptions",
                params=params,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5,
            )
            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "code": "invalid_youtube_access_token",
                        "message": "Invalid YouTube access token",
                    },
                )
            response.raise_for_status()
            payload = response.json()
        except HTTPException:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "code": "youtube_upstream_failed",
                    "message": "YouTube subscription lookup failed",
                },
            ) from exc

        for item in payload.get("items", []):
            channel_id = (
                item.get("snippet", {}).get("resourceId", {}).get("channelId")
            )
            if channel_id:
                channel_ids.append(channel_id)

        page_token = payload.get("nextPageToken")
        if not page_token:
            return channel_ids


def fetch_youtube_channels(channel_ids: list[str]) -> list[dict]:
    if not channel_ids:
        return []

    settings = get_settings()
    items: list[dict] = []

    for start in range(0, len(channel_ids), 50):
        batch = channel_ids[start : start + 50]
        try:
            response = httpx.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={
                    "part": "snippet,brandingSettings",
                    "id": ",".join(batch),
                    "key": settings.youtube_api_key,
                },
                timeout=5,
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "code": "youtube_upstream_failed",
                    "message": "YouTube channel lookup failed",
                },
            ) from exc

        items.extend(payload.get("items", []))

    return items


def is_korean_channel(item: dict) -> bool:
    snippet = item.get("snippet", {})
    branding_channel = item.get("brandingSettings", {}).get("channel", {})
    country = branding_channel.get("country")
    default_language = snippet.get("defaultLanguage")

    if country == "KR":
        return True
    return isinstance(default_language, str) and (
        default_language == "ko" or default_language.startswith("ko-")
    )


def parse_published_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
