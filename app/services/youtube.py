from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen
import json
import re

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
    query = urlencode(
        {"part": "snippet,contentDetails", "id": video_id, "key": settings.youtube_api_key}
    )
    url = f"https://www.googleapis.com/youtube/v3/videos?{query}"

    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
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


def parse_published_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
