from datetime import UTC, datetime

from app.models.waitlist import WaitlistEntry
from app.services.discord import build_waitlist_signup_payload


def test_build_waitlist_signup_payload_includes_user_and_video_context():
    entry = WaitlistEntry(
        id=1,
        user_id=7,
        email="waitlist@example.com",
        name="Waitlist User",
        picture="https://example.com/profile.png",
        youtube_url="https://www.youtube.com/watch?v=abc123XYZ00&t=1237s",
        source="landing_early_access",
        created_at=datetime(2026, 5, 13, 13, 6, 35, tzinfo=UTC),
    )

    payload = build_waitlist_signup_payload(entry)

    assert payload["content"] is None
    embed = payload["embeds"][0]
    assert embed["title"] == "Waitlist User joined the waitlist"
    assert embed["description"] == "[Open submitted video](https://www.youtube.com/watch?v=abc123XYZ00&t=1237s)"
    assert embed["url"] == "https://www.youtube.com/watch?v=abc123XYZ00&t=1237s"
    assert embed["thumbnail"] == {"url": "https://example.com/profile.png"}
    assert embed["image"] == {"url": "https://i.ytimg.com/vi/abc123XYZ00/hqdefault.jpg"}
    assert embed["fields"] == [
        {"name": "Email", "value": "waitlist@example.com", "inline": True},
        {"name": "Source", "value": "landing_early_access", "inline": True},
        {
            "name": "Signed Up",
            "value": "<t:1778677595:F>\n<t:1778677595:R>",
            "inline": False,
        },
    ]


def test_build_waitlist_signup_payload_omits_images_when_not_available():
    entry = WaitlistEntry(
        id=1,
        user_id=7,
        email="waitlist@example.com",
        name="Waitlist User",
        picture=None,
        youtube_url="https://example.com/not-youtube",
        source="landing_early_access",
        created_at=datetime(2026, 5, 13, 13, 6, 35, tzinfo=UTC),
    )

    payload = build_waitlist_signup_payload(entry)

    embed = payload["embeds"][0]
    assert "thumbnail" not in embed
    assert "image" not in embed
