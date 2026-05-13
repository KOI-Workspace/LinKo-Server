from __future__ import annotations

from datetime import UTC

import httpx

from app.models.waitlist import WaitlistEntry
from app.services.youtube import extract_video_id


def _build_youtube_thumbnail_url(youtube_url: str) -> str | None:
    try:
        video_id = extract_video_id(youtube_url)
    except ValueError:
        return None
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def build_waitlist_signup_payload(entry: WaitlistEntry) -> dict:
    timestamp = int(entry.created_at.astimezone(UTC).timestamp())
    embed = {
        "title": f"{entry.name} joined the waitlist",
        "description": f"[Open submitted video]({entry.youtube_url})",
        "url": entry.youtube_url,
        "color": 0x5865F2,
        "fields": [
            {"name": "Email", "value": entry.email, "inline": True},
            {"name": "Source", "value": entry.source, "inline": True},
            {
                "name": "Signed Up",
                "value": f"<t:{timestamp}:F>\n<t:{timestamp}:R>",
                "inline": False,
            },
        ],
    }

    if entry.picture:
        embed["thumbnail"] = {"url": entry.picture}

    youtube_thumbnail_url = _build_youtube_thumbnail_url(entry.youtube_url)
    if youtube_thumbnail_url:
        embed["image"] = {"url": youtube_thumbnail_url}

    return {"content": None, "embeds": [embed]}


def notify_waitlist_signup(entry: WaitlistEntry, webhook_url: str) -> None:
    response = httpx.post(
        webhook_url,
        json=build_waitlist_signup_payload(entry),
        timeout=5.0,
    )
    response.raise_for_status()
