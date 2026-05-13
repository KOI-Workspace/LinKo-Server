from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import html

import httpx

from app.core.config import get_settings
from app.services.youtube import extract_video_id


@dataclass(frozen=True)
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    source: Literal["youtube_caption", "youtube_auto_caption"]
    text: str
    segments: list[TranscriptSegment]
    lang: str | None = None


def filter_segments(
    segments: list[TranscriptSegment],
    start_sec: float,
    end_sec: float,
) -> list[TranscriptSegment]:
    return [
        item
        for item in segments
        if item.end_sec > start_sec and item.start_sec < end_sec
    ]


def language_matches(requested_lang: str, actual_lang: str | None) -> bool:
    if not actual_lang:
        return False

    return _base_language_code(requested_lang) == _base_language_code(actual_lang)


def _base_language_code(lang: str) -> str:
    return lang.strip().lower().replace("_", "-").split("-", maxsplit=1)[0]


def download_youtube_captions(
    url: str,
    output_dir: Path,  # Signature compatibility
    lang: str,
    start_sec: int,
    end_sec: int,
    allow_auto: bool = True,
    runner: any = None,  # Signature compatibility
    require_requested_lang: bool = True,
) -> TranscriptResult | None:
    settings = get_settings()
    if not settings.supadata_api_key:
        return None

    try:
        video_id = extract_video_id(url)
    except Exception:
        return None

    try:
        response = httpx.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            params={"videoId": video_id, "lang": lang},
            headers={"x-api-key": settings.supadata_api_key},
            timeout=30
        )
        if response.status_code != 200:
            return None
        
        data = response.json()
        actual_lang = data.get("lang")
        if require_requested_lang and not language_matches(lang, actual_lang):
            return None

        content = data.get("content", [])
        
        segments: list[TranscriptSegment] = []
        for item in content:
            # offset and duration are in ms
            start = item["offset"] / 1000.0
            duration = item["duration"] / 1000.0
            end = start + duration
            
            # Filter by time range
            if end > start_sec and start < end_sec:
                segments.append(
                    TranscriptSegment(
                        start_sec=start,
                        end_sec=end,
                        text=html.unescape(item["text"]),
                    )
                )

        if not segments:
            return None

        full_text = "\n".join(s.text for s in segments)
        if len(full_text.strip()) < 20:
            return None

        # Supadata defaults to the best available transcript.
        # We'll label it as youtube_caption for consistency.
        return TranscriptResult(
            source="youtube_caption",
            text=full_text,
            segments=segments,
            lang=actual_lang,
        )

    except Exception:
        return None
