import pytest

from app.services.youtube import (
    extract_video_id,
    is_korean_channel,
    parse_iso8601_duration_seconds,
    select_thumbnail_url,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=abc123XYZ00", "abc123XYZ00"),
        ("https://youtu.be/abc123XYZ00", "abc123XYZ00"),
        ("https://www.youtube.com/shorts/abc123XYZ00", "abc123XYZ00"),
    ],
)
def test_extract_video_id_accepts_common_youtube_urls(url: str, expected: str):
    assert extract_video_id(url) == expected


def test_extract_video_id_rejects_invalid_url():
    with pytest.raises(ValueError, match="Invalid YouTube URL"):
        extract_video_id("https://example.com/watch?v=abc123")


@pytest.mark.parametrize(
    ("duration", "expected"),
    [
        ("PT12M34S", 754),
        ("PT1H2M3S", 3723),
        ("PT45S", 45),
    ],
)
def test_parse_iso8601_duration_seconds(duration: str, expected: int):
    assert parse_iso8601_duration_seconds(duration) == expected


def test_select_thumbnail_url_prefers_highest_known_quality():
    thumbnails = {
        "default": {"url": "default.jpg"},
        "medium": {"url": "medium.jpg"},
        "high": {"url": "high.jpg"},
        "standard": {"url": "standard.jpg"},
    }

    assert select_thumbnail_url(thumbnails) == "standard.jpg"


def test_is_korean_channel_accepts_korean_country():
    item = {
        "snippet": {"defaultLanguage": "en"},
        "brandingSettings": {"channel": {"country": "KR"}},
    }

    assert is_korean_channel(item) is True


@pytest.mark.parametrize("language", ["ko", "ko-KR"])
def test_is_korean_channel_accepts_korean_default_language(language: str):
    item = {
        "snippet": {"defaultLanguage": language},
        "brandingSettings": {"channel": {"country": "US"}},
    }

    assert is_korean_channel(item) is True


def test_is_korean_channel_rejects_non_korean_channel():
    item = {
        "snippet": {"defaultLanguage": "en"},
        "brandingSettings": {"channel": {"country": "US"}},
    }

    assert is_korean_channel(item) is False


def test_is_korean_channel_rejects_missing_language_and_country():
    assert is_korean_channel({"snippet": {}, "brandingSettings": {"channel": {}}}) is False
