from dataclasses import dataclass
from typing import Any
import json

from app.core.config import get_settings
from app.services.transcripts import TranscriptResult


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
) -> LessonArtifacts:
    settings = get_settings()
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        payload = _call_gemini(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            youtube_id=youtube_id,
            duration_seconds=duration_seconds,
            transcript=transcript,
        )
    else:
        payload = _mock_artifacts(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            youtube_id=youtube_id,
            duration_seconds=duration_seconds,
            transcript=transcript,
        )

    return validate_lesson_artifacts(payload)


def validate_lesson_artifacts(payload: dict[str, Any]) -> LessonArtifacts:
    flashcards = payload.get("flashcards")
    if not isinstance(flashcards, dict):
        raise ArtifactValidationError("flashcards must be an object")
    if not isinstance(flashcards.get("cards"), list):
        raise ArtifactValidationError("flashcards.cards must be a list")

    subtitles = payload.get("subtitles")
    if not isinstance(subtitles, dict):
        raise ArtifactValidationError("subtitles must be an object")
    if not isinstance(subtitles.get("lines"), list):
        raise ArtifactValidationError("subtitles.lines must be a list")

    watch_vocab = subtitles.get("vocabMap", {})
    if not isinstance(watch_vocab, dict):
        raise ArtifactValidationError("subtitles.vocabMap must be an object")

    cultural_notes = subtitles.get("culturalNotes", [])
    if not isinstance(cultural_notes, list):
        raise ArtifactValidationError("subtitles.culturalNotes must be a list")

    return LessonArtifacts(
        flashcards=flashcards,
        subtitles={
            "youtubeId": subtitles.get("youtubeId"),
            "durationSec": subtitles.get("durationSec"),
            "lines": subtitles["lines"],
        },
        watch_vocab=watch_vocab,
        cultural_notes=cultural_notes,
    )


def _mock_artifacts(
    lesson_id: str,
    lesson_title: str,
    youtube_id: str,
    duration_seconds: int,
    transcript: TranscriptResult,
) -> dict[str, Any]:
    lines = [
        {
            "id": f"s{index}",
            "startSec": int(segment.start_sec),
            "endSec": int(segment.end_sec),
            "korean": segment.text,
            "english": f"English translation for: {segment.text}",
        }
        for index, segment in enumerate(transcript.segments, start=1)
    ]
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
        "subtitles": {
            "youtubeId": youtube_id,
            "durationSec": duration_seconds,
            "lines": lines,
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
        timeout=300,
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
        f"[{int(segment.start_sec)}-{int(segment.end_sec)}] {segment.text}"
        for segment in transcript.segments
    )

    return f"""
Create Korean learning artifacts for the LinKo frontend.
Return only valid JSON, no markdown.

Required top-level shape:
{{
  "flashcards": {{"lessonId": "{lesson_id}", "lessonTitle": "{lesson_title}", "cards": []}},
  "subtitles": {{
    "youtubeId": "{youtube_id}",
    "durationSec": {duration_seconds},
    "lines": [],
    "vocabMap": {{}},
    "culturalNotes": []
  }}
}}

Rules:
- flashcards.cards must contain 5 to 10 cards when the transcript has enough material.
- Include BOTH word cards and useful ending cards.
- Use ONLY the timestamped transcript segments below for all startSec/endSec values.
- For every flashcard video, startSec/endSec MUST match the transcript segment that contains the exampleSentence or scriptSentence. Do not invent timestamps.
- For subtitles.lines, preserve the transcript segment timing exactly unless adjacent segments must be merged for readability. If merging, use the first segment startSec and last segment endSec.
- YOU MUST format EACH card EXACTLY according to these structures:

Structure for Word card (type="word"):
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

Structure for Ending card (type="ending"):
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

- subtitles.lines must contain Korean and English lines with startSec and endSec. Example: {{"id": "s1", "startSec": 0, "endSec": 5, "korean": "...", "english": "..."}}
- vocabMap keys must be surface forms that appear in subtitle Korean text.
- culturalNotes should explain slang, idioms, cultural context, or grammar patterns.

Transcript source: {transcript.source}
Timestamped transcript segments:
{timestamped_segments[:18000]}
""".strip()
