from dataclasses import dataclass
from typing import Any
import json
import random

from app.core.config import get_settings
from app.services.transcripts import TranscriptResult, TranscriptSegment


FLASHCARD_TRANSCRIPT_MAX_SECONDS = 180
FLASHCARD_TRANSCRIPT_MAX_CHARS = 6000


class ArtifactValidationError(ValueError):
    pass


@dataclass(frozen=True)
class LessonArtifacts:
    flashcards: dict[str, Any]
    subtitles: dict[str, Any]
    watch_vocab: dict[str, Any]
    cultural_notes: list[dict[str, Any]]


def generate_lesson_artifacts_from_transcript(
    lesson_id: str,
    lesson_title: str,
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
    english_transcript: TranscriptResult | None = None,
) -> LessonArtifacts:
    subtitles = build_subtitle_artifacts(
        youtube_id=youtube_id,
        duration_seconds=duration_seconds,
        transcript=transcript,
        english_transcript=english_transcript,
    )
    flashcard_transcript = sample_transcript_for_flashcards(
        transcript=transcript,
        seed=f"{lesson_id}:{youtube_id}",
    )
    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        payload = _call_gemini(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            youtube_id=youtube_id,
            duration_seconds=duration_seconds,
            transcript=flashcard_transcript,
        )
    else:
        payload = _mock_flashcards(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            youtube_id=youtube_id,
            duration_seconds=duration_seconds,
            transcript=flashcard_transcript,
        )

    flashcards = validate_flashcard_artifacts(payload)
    watch_enrichments = validate_watch_enrichments(payload)
    return LessonArtifacts(
        flashcards=flashcards,
        subtitles=subtitles,
        watch_vocab=watch_enrichments.watch_vocab,
        cultural_notes=watch_enrichments.cultural_notes,
    )


@dataclass(frozen=True)
class WatchEnrichments:
    watch_vocab: dict[str, Any]
    cultural_notes: list[dict[str, Any]]


def build_subtitle_artifacts(
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
    english_transcript: TranscriptResult | None = None,
) -> dict[str, Any]:
    return {
        "youtubeId": youtube_id,
        "durationSec": duration_seconds,
        "lines": [
            {
                "id": f"s{index}",
                "startSec": segment.start_sec,
                "endSec": segment.end_sec,
                "korean": segment.text,
                "english": _matching_english_text(segment, english_transcript),
            }
            for index, segment in enumerate(transcript.segments, start=1)
        ],
    }


def _matching_english_text(
    korean_segment: TranscriptSegment,
    english_transcript: TranscriptResult | None,
) -> str:
    if english_transcript is None:
        return ""

    matches = [
        segment.text
        for segment in english_transcript.segments
        if segment.end_sec > korean_segment.start_sec
        and segment.start_sec < korean_segment.end_sec
    ]
    return " ".join(matches)


def limit_transcript_for_flashcards(
    transcript: TranscriptResult,
    max_seconds: int = FLASHCARD_TRANSCRIPT_MAX_SECONDS,
    max_chars: int = FLASHCARD_TRANSCRIPT_MAX_CHARS,
) -> TranscriptResult:
    segments: list[TranscriptSegment] = []
    used_chars = 0

    for segment in transcript.segments:
        if segment.start_sec >= max_seconds:
            break

        remaining_chars = max_chars - used_chars
        if remaining_chars <= 0:
            break

        text = segment.text[:remaining_chars].rstrip()
        if not text:
            break

        segments.append(
            TranscriptSegment(
                start_sec=segment.start_sec,
                end_sec=min(segment.end_sec, max_seconds),
                text=text,
            )
        )
        used_chars += len(text)

        if segment.end_sec >= max_seconds or used_chars >= max_chars:
            break

    return TranscriptResult(
        source=transcript.source,
        text="\n".join(segment.text for segment in segments),
        segments=segments,
        lang=transcript.lang,
    )


def sample_transcript_for_flashcards(
    transcript: TranscriptResult,
    seed: str,
    max_seconds: int = FLASHCARD_TRANSCRIPT_MAX_SECONDS,
    max_chars: int = FLASHCARD_TRANSCRIPT_MAX_CHARS,
) -> TranscriptResult:
    if not transcript.segments:
        return TranscriptResult(source=transcript.source, text="", segments=[], lang=transcript.lang)

    total_start = transcript.segments[0].start_sec
    total_end = max(segment.end_sec for segment in transcript.segments)
    if total_end - total_start <= max_seconds:
        return limit_transcript_for_flashcards(transcript, max_seconds=max_seconds, max_chars=max_chars)

    rng = random.Random(seed)
    window_count = 2
    window_seconds = max_seconds / window_count
    bucket_seconds = (total_end - total_start) / window_count
    starts = []
    for index in range(window_count):
        bucket_start = total_start + (index * bucket_seconds)
        bucket_end = total_start + ((index + 1) * bucket_seconds)
        latest_start = max(bucket_start, bucket_end - window_seconds)
        starts.append(rng.uniform(bucket_start, latest_start))

    selected: list[TranscriptSegment] = []
    used_chars = 0
    selected_keys: set[tuple[float, float, str]] = set()

    for start in starts:
        end = min(start + window_seconds, total_end)
        for segment in transcript.segments:
            if segment.end_sec <= start or segment.start_sec >= end:
                continue
            remaining_chars = max_chars - used_chars
            if remaining_chars <= 0:
                break

            text = segment.text[:remaining_chars].rstrip()
            if not text:
                break

            clipped = TranscriptSegment(
                start_sec=max(segment.start_sec, start),
                end_sec=min(segment.end_sec, end),
                text=text,
            )
            key = (clipped.start_sec, clipped.end_sec, clipped.text)
            if key in selected_keys:
                continue

            selected.append(clipped)
            selected_keys.add(key)
            used_chars += len(text)

        if used_chars >= max_chars:
            break

    if not selected:
        return limit_transcript_for_flashcards(
            transcript,
            max_seconds=max_seconds,
            max_chars=max_chars,
        )

    selected.sort(key=lambda segment: (segment.start_sec, segment.end_sec))
    return TranscriptResult(
        source=transcript.source,
        text="\n".join(segment.text for segment in selected),
        segments=selected,
        lang=transcript.lang,
    )


def validate_lesson_artifacts(payload: dict[str, Any]) -> LessonArtifacts:
    subtitles = payload.get("subtitles")
    if not isinstance(subtitles, dict):
        raise ArtifactValidationError("subtitles must be an object")
    if not isinstance(subtitles.get("lines"), list):
        raise ArtifactValidationError("subtitles.lines must be a list")

    return LessonArtifacts(
        flashcards=validate_flashcard_artifacts(payload),
        subtitles={
            "youtubeId": subtitles.get("youtubeId"),
            "durationSec": subtitles.get("durationSec"),
            "lines": subtitles["lines"],
        },
        watch_vocab=_validate_watch_vocab(subtitles),
        cultural_notes=_validate_cultural_notes(subtitles),
    )


def validate_flashcard_artifacts(payload: dict[str, Any]) -> dict[str, Any]:
    flashcards = payload.get("flashcards")
    if not isinstance(flashcards, dict):
        raise ArtifactValidationError("flashcards must be an object")
    if not isinstance(flashcards.get("cards"), list):
        raise ArtifactValidationError("flashcards.cards must be a list")
    return flashcards


def validate_watch_enrichments(payload: dict[str, Any]) -> WatchEnrichments:
    watch = payload.get("watch", {})
    if watch is None:
        watch = {}
    if not isinstance(watch, dict):
        raise ArtifactValidationError("watch must be an object")

    watch_vocab = watch.get("vocabMap", {})
    if not isinstance(watch_vocab, dict):
        raise ArtifactValidationError("watch.vocabMap must be an object")

    cultural_notes = watch.get("culturalNotes", [])
    if not isinstance(cultural_notes, list):
        raise ArtifactValidationError("watch.culturalNotes must be a list")

    return WatchEnrichments(
        watch_vocab=watch_vocab,
        cultural_notes=cultural_notes,
    )


def _validate_watch_vocab(subtitles: dict[str, Any]) -> dict[str, Any]:
    watch_vocab = subtitles.get("vocabMap", {})
    if not isinstance(watch_vocab, dict):
        raise ArtifactValidationError("subtitles.vocabMap must be an object")
    return watch_vocab


def _validate_cultural_notes(subtitles: dict[str, Any]) -> list[dict[str, Any]]:
    cultural_notes = subtitles.get("culturalNotes", [])
    if not isinstance(cultural_notes, list):
        raise ArtifactValidationError("subtitles.culturalNotes must be a list")
    return cultural_notes


def _mock_flashcards(
    lesson_id: str,
    lesson_title: str,
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
) -> dict[str, Any]:
    first_segment = transcript.segments[0] if transcript.segments else None
    start_sec = int(first_segment.start_sec) if first_segment else 0
    end_sec = int(first_segment.end_sec) if first_segment else min(duration_seconds, 5)
    first_text = first_segment.text if first_segment else transcript.text[:80]
    expression = _first_korean_token(first_text)
    card_id = f"fc-{lesson_id}-1"

    return {
        "flashcards": {
            "lessonId": lesson_id,
            "lessonTitle": lesson_title,
            "cards": [
                {
                    "id": card_id,
                    "type": "word",
                    "expression": expression,
                    "meaning": f"Meaning of {expression}",
                    "exampleSentence": first_text,
                    "exampleTranslation": f"English translation for: {first_text}",
                    "video": {
                        "youtubeId": youtube_id,
                        "startSec": start_sec,
                        "endSec": end_sec,
                    },
                    "relatedVideos": [],
                    "dailyConversation": [
                        {"text": f"{expression} 무슨 뜻이에요?", "isQuestion": True},
                        {"text": f"{expression} means the key expression here.", "isQuestion": False},
                    ],
                }
            ],
        },
        "watch": {
            "vocabMap": {
                expression: {
                    "meaning": f"Meaning of {expression}",
                    "cardId": card_id,
                    "lessonId": lesson_id,
                    "expression": expression,
                    "exampleSentence": first_text,
                    "exampleTranslation": f"English translation for: {first_text}",
                }
            },
            "culturalNotes": [
                {
                    "id": f"culture-{lesson_id}-1",
                    "subtitleId": "s1",
                    "title": expression,
                    "keyword": "Context",
                    "explanation": "This note is generated from the transcript context.",
                }
            ],
        },
    }


def _first_korean_token(text: str) -> str:
    for token in text.replace(".", " ").replace(",", " ").split():
        if token.strip():
            return token.strip()
    return "표현"


def _call_gemini(
    lesson_id: str,
    lesson_title: str,
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
) -> dict[str, Any]:
    settings = get_settings()
    import httpx

    prompt = _build_gemini_prompt(
        lesson_id=lesson_id,
        lesson_title=lesson_title,
        youtube_id=youtube_id,
        duration_seconds=duration_seconds,
        transcript=transcript,
    )
    response = httpx.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
        headers={
            "x-goog-api-key": settings.gemini_api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"},
        },
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()
    text = "".join(
        part.get("text", "")
        for part in data["candidates"][0]["content"].get("parts", [])
    )
    return _parse_gemini_json(text)


def _parse_gemini_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return json.loads(_remove_trailing_commas(text))


def _remove_trailing_commas(text: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    index = 0

    while index < len(text):
        char = text[index]

        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue

        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue

        if char == ",":
            lookahead = index + 1
            while lookahead < len(text) and text[lookahead].isspace():
                lookahead += 1
            if lookahead < len(text) and text[lookahead] in "}]":
                index += 1
                continue

        result.append(char)
        index += 1

    return "".join(result)


def _build_gemini_prompt(
    lesson_id: str,
    lesson_title: str,
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
) -> str:
    timestamped_segments = "\n".join(
        f"[s{index} {int(segment.start_sec)}-{int(segment.end_sec)}] {segment.text}"
        for index, segment in enumerate(transcript.segments, start=1)
    )

    return f"""
Create Korean learning artifacts for the LinKo frontend.
Return only valid JSON, no markdown.

Required top-level shape:
{{
  "flashcards": {{"lessonId": "{lesson_id}", "lessonTitle": "{lesson_title}", "cards": []}},
  "watch": {{"vocabMap": {{}}, "culturalNotes": []}}
}}

Rules:
- You are receiving a deterministic sample of continuous transcript excerpts, capped to roughly {FLASHCARD_TRANSCRIPT_MAX_SECONDS // 60} total minutes and {FLASHCARD_TRANSCRIPT_MAX_CHARS} characters to keep the request small and reliable.
- Create flashcards and watch enrichments only from these sampled excerpts. Do not try to cover the whole video.
- flashcards.cards must contain 3 to 5 cards when the excerpt has enough material.
- Prefer word cards. Include at most 1 ending card only if a useful grammar pattern is obvious.
- Use ONLY the timestamped transcript segments below for all startSec/endSec values.
- For every flashcard video, startSec/endSec MUST match the transcript segment that contains the exampleSentence or scriptSentence. Do not invent timestamps.
- watch.vocabMap powers hidden vocabulary labels in the Watch UI. Keys MUST be Korean surface forms that appear verbatim in the sampled transcript.
- watch.vocabMap must contain at most 5 entries. When an entry corresponds to a flashcard, set cardId to that flashcard id.
- watch.vocabMap values MUST include meaning, lessonId, expression, exampleSentence, and exampleTranslation.
- watch.culturalNotes should contain 0 to 2 notes for slang, idioms, cultural context, or grammar patterns found in the sampled excerpts.
- watch.culturalNotes subtitleId MUST reference one of the sampled subtitle ids shown below, such as s1, s2, s3.
- Use these compact card shapes:

Word card:
{{
  "id": "fc-{lesson_id}-word-1",
  "type": "word",
  "expression": "Korean word here",
  "meaning": "English meaning",
  "exampleSentence": "Korean example sentence from transcript",
  "exampleTranslation": "English translation",
  "video": {{"youtubeId": "{youtube_id}", "startSec": 0, "endSec": 5}},
  "relatedVideos": [],
  "dailyConversation": [
    {{"text": "Korean question using the word?", "isQuestion": true}},
    {{"text": "Korean answer using the word.", "isQuestion": false}}
  ]
}}

Ending card:
{{
  "id": "fc-{lesson_id}-ending-1",
  "type": "ending",
  "baseWord": "Korean dictionary form (e.g. 가다)",
  "baseWordMeaning": "English meaning of base word",
  "conjugatedForm": "Korean conjugated form",
  "conjugationBadges": [
    {{"added": "Korean ending added (e.g. -고 있어요)"}}
  ],
  "ending": "The grammar point (e.g. -고 있다)",
  "endingMeaning": "English meaning of the grammar",
  "endingExplanation": "Explanation of the grammar usage",
  "scriptSentence": "Korean sentence from transcript",
  "scriptTranslation": "English translation",
  "video": {{"youtubeId": "{youtube_id}", "startSec": 0, "endSec": 5}},
  "relatedVideos": []
}}

Transcript source: {transcript.source}
Timestamped transcript segments:
{timestamped_segments}
""".strip()
