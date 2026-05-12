# Lesson Generation Artifacts Design

## Goal

Add the backend generation flow that starts when a user submits a YouTube URL. The server creates a lesson, acquires a Korean transcript, asks Gemini to generate frontend-ready learning artifacts, stores the result, and later serves those artifacts through flashcard and subtitle APIs.

The important architectural decision is that the system is transcript-provider based, not YouTube-caption-only. The MVP uses YouTube captions and automatic captions. Later, if captions are unavailable, the same boundary can fall back to STT without changing the flashcard or subtitle APIs.

## Scope

In scope for the MVP:

- Authenticated lesson creation from a YouTube URL.
- FastAPI `BackgroundTasks` generation after the request returns.
- YouTube metadata lookup.
- Korean transcript acquisition from YouTube captions or automatic captions through the existing POC `yt-dlp` approach.
- Gemini generation that directly returns frontend-ready flashcard and subtitle/watch artifacts.
- Database persistence for lesson status, transcript data, and generated artifacts.
- Status polling APIs for the frontend.
- Flashcard API backed by stored generated artifacts.
- Subtitle/watch API contract for the next frontend/backend session.

Out of scope for the MVP:

- Actual STT implementation.
- Queue/worker infrastructure such as Celery, RQ, SQS, or Lambda.
- Whole-video chunking beyond a first bounded transcript segment.
- Payment or quota enforcement.
- Production YouTube compliance decisions beyond preserving the transcript-provider boundary.
- Frontend implementation.

## Frontend Context

The client already has the target UX shape:

- `UrlInput` accepts a YouTube URL, but its submit handler is not connected to a generation API yet.
- Home and Lessons pages show `generationStatus: "generating" | "ready"`.
- Lesson detail already shows a loading state while a lesson is generating.
- `FlashcardTab` currently reads `MOCK_FLASHCARDS[lessonId]`.
- `WatchTab` currently uses mock subtitle lines, vocab hover data, cultural notes, and bookmark markers.

The backend should support this sequence:

```text
UrlInput submits URL
-> lesson appears as generating
-> frontend polls lesson status or refreshes lesson list
-> lesson becomes ready
-> FlashcardTab calls flashcard API
-> WatchTab calls subtitle/watch API
```

## API Design

All application endpoints use the existing `/api` prefix. Lesson creation and user lesson lists require the existing service JWT.

```text
POST /api/lessons
GET  /api/lessons
GET  /api/lessons/{lesson_id}
GET  /api/lessons/{lesson_id}/flashcards
GET  /api/lessons/{lesson_id}/subtitles
```

`POST /api/lessons` accepts:

```json
{
  "youtubeUrl": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

It creates a lesson with `generationStatus: "generating"`, schedules a background generation task, and returns immediately:

```json
{
  "lessonId": "123",
  "generationStatus": "generating"
}
```

`GET /api/lessons` returns the current user's lessons for Home and My Lessons views. Each item should include the fields the client already models: `id`, `title`, `channelName`, `thumbnailUrl`, `duration`, `date`, `generationStatus`, `flashcardDone`, `subtitleDone`, and optional error fields when generation fails.

`GET /api/lessons/{lesson_id}` returns one lesson status record for polling.

`GET /api/lessons/{lesson_id}/flashcards` returns the stored frontend flashcard contract when ready. If the lesson is still generating, return `409 lesson_not_ready`. If generation failed, return `422 lesson_generation_failed`. If no lesson exists for the user, return `404`.

`GET /api/lessons/{lesson_id}/subtitles` returns the stored WatchTab contract when ready. It follows the same `409`, `422`, and `404` behavior as flashcards.

## Data Model

Use one `lessons` table for the MVP. The JSON fields can be split into artifact tables later without changing API contracts.

- `id`
- `user_id`
- `youtube_url`
- `youtube_video_id`
- `title`
- `channel_title`
- `thumbnail_url`
- `duration_seconds`
- `generation_status`: `generating | ready | failed`
- `transcript_status`: `pending | ready | unavailable | failed`
- `transcript_source`: `youtube_caption | youtube_auto_caption | stt`
- `transcript_text`
- `caption_segments_json`
- `flashcards_json`
- `subtitles_json`
- `watch_vocab_json`
- `cultural_notes_json`
- `raw_youtube_metadata`
- `error_code`
- `error_message`
- `transcript_error_code`
- `transcript_error_message`
- `created_at`
- `updated_at`

Use `generation_status` for the user-visible lesson lifecycle. Use `transcript_status` for the lower-level transcript acquisition lifecycle.

## Transcript Acquisition

Create a transcript provider boundary:

```text
acquire_transcript(youtube_url, requested_language="ko") -> TranscriptResult
```

For the MVP, `acquire_transcript` uses the POC caption flow:

1. Call `yt-dlp --dump-json --skip-download` for metadata.
2. Call `yt-dlp --skip-download --write-sub --write-auto-sub --sub-lang ko --sub-format vtt`.
3. Parse VTT into timed caption segments.
4. Select a bounded segment for generation.
5. Store transcript text and segment timings.

If manually authored Korean captions are available, set `transcript_source = "youtube_caption"`. If only automatic captions are available, set `transcript_source = "youtube_auto_caption"`.

If no Korean captions are available in the MVP, mark the lesson failed:

```text
generation_status = failed
transcript_status = unavailable
error_code = transcript_unavailable
```

When STT is added later, caption unavailability should trigger an STT provider instead of immediate failure:

```text
YouTube captions unavailable
-> extract or download audio
-> run STT
-> transcript_source = stt
-> continue the same artifact generation pipeline
```

Flashcard and subtitle APIs must not care which transcript provider produced the transcript.

## Artifact Generation

Gemini should generate artifacts directly in the frontend contracts rather than producing the POC `learning-pack` shape first.

The generated object should have this top-level shape:

```json
{
  "flashcards": {
    "lessonId": "123",
    "lessonTitle": "Video title",
    "cards": []
  },
  "subtitles": {
    "youtubeId": "VIDEO_ID",
    "durationSec": 123,
    "lines": [],
    "vocabMap": {},
    "culturalNotes": []
  }
}
```

`flashcards` must match the existing `LessonFlashcards` frontend type:

- Word cards include `id`, `type`, `expression`, `meaning`, `exampleSentence`, `exampleTranslation`, `video`, `relatedVideos`, and optional `dailyConversation`.
- Ending cards include `id`, `type: "ending"`, `baseWord`, `baseWordMeaning`, `conjugatedForm`, `conjugationBadges`, `ending`, `endingMeaning`, `endingExplanation`, `scriptSentence`, `scriptTranslation`, `video`, and `relatedVideos`.
- Generate 5 to 10 cards total.
- Insert one ending card after every 3 or 4 word cards when the transcript contains useful conjugation patterns. If the transcript does not contain useful conjugation patterns, return only word cards.
- `video.youtubeId`, `startSec`, and `endSec` must reference the source caption segment.

`subtitles` must match the WatchTab needs:

- `youtubeId`
- `durationSec`
- `lines`: `id`, `startSec`, `endSec`, `korean`, `english`
- `vocabMap`: keys are surface forms that may appear in subtitle text. Values include `meaning`, optional `cardId`, `lessonId`, `expression`, `exampleSentence`, and `exampleTranslation`.
- `culturalNotes`: `id`, `subtitleId`, `title`, `keyword`, `explanation`

The server should validate Gemini output before saving. If validation fails once, retry Gemini with the validation error and the prior JSON. If the repaired response still fails, mark generation failed with `error_code = artifact_validation_failed`.

## Background Task Flow

`POST /api/lessons` performs only fast work before responding:

1. Validate the URL and current user.
2. Create a lesson row with `generation_status = "generating"` and `transcript_status = "pending"`.
3. Schedule `generate_lesson_artifacts(lesson_id)`.
4. Return the lesson id.

`generate_lesson_artifacts`:

1. Reload the lesson from the database.
2. Fetch and store YouTube metadata.
3. Acquire transcript through the provider boundary.
4. Generate Gemini artifacts.
5. Save transcript, captions, flashcards, subtitles, vocab map, and cultural notes.
6. Set `generation_status = "ready"` and `transcript_status = "ready"`.

On any expected failure, store a stable `error_code` and human-readable `error_message`. Unexpected exceptions should be logged and mapped to `generation_failed`.

## Subtitle UI Overlap

The subtitle/watch UI session should not reimplement YouTube caption extraction or Gemini generation. It should consume `GET /api/lessons/{lesson_id}/subtitles`.

The backend contract must preserve the distinctions the UI needs:

- Previously bookmarked words can be computed from the user's bookmarks.
- Current lesson flashcard words come from `vocabMap` entries with `cardId` pointing at generated flashcards.
- Current lesson bookmarked flashcard words are the intersection of generated flashcard card ids and user bookmarks.
- Plain dictionary hover entries can be entries in `vocabMap` without a `cardId`.

Bookmarks themselves should remain a separate feature. The generated subtitle artifact provides enough identifiers and text for bookmark creation, but it should not encode per-user bookmark state.

## Error Handling

Stable generation errors:

- `invalid_youtube_url`
- `youtube_metadata_failed`
- `transcript_unavailable`
- `transcript_download_failed`
- `artifact_generation_failed`
- `artifact_validation_failed`
- `lesson_not_ready`
- `lesson_generation_failed`

`POST /api/lessons` should return validation errors synchronously for bad input. Background failures should be visible through `GET /api/lessons` and `GET /api/lessons/{lesson_id}`.

Artifact endpoints should not block waiting for generation. They return status-specific errors when data is not ready.

## Testing

Cover:

- Lesson creation requires authentication.
- Invalid YouTube URLs return `400`.
- Lesson creation stores `generating` status and schedules background work.
- Successful generation stores metadata, transcript, flashcards, subtitles, vocab map, and cultural notes.
- Flashcards endpoint returns `409` while generating.
- Flashcards endpoint returns stored generated JSON when ready.
- Subtitles endpoint returns `409` while generating.
- Subtitles endpoint returns stored WatchTab JSON when ready.
- Missing captions mark the lesson failed with `transcript_unavailable`.
- Failed lessons return `422` from artifact endpoints.
- Gemini validation failure is retried once and then marks the lesson failed if still invalid.

## Migration Path

The MVP keeps generation inside FastAPI `BackgroundTasks`. That is acceptable for local and early single-server testing, but production should move `generate_lesson_artifacts` behind a durable queue before relying on long-running jobs.

The STT migration should add a second transcript provider behind `acquire_transcript`. It should not require changes to lesson listing, flashcard retrieval, subtitle retrieval, or generated artifact schemas.
