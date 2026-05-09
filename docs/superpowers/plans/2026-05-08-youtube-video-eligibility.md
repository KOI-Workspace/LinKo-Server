# YouTube Video Eligibility Plan

## Goal

Define backend validation rules for YouTube videos before the frontend opens the video learning modal. The frontend should show a modal only when the backend marks the video as unsupported.

## Response Shape

Extend the video metadata response with an eligibility result.

```json
{
  "video": {
    "id": "youtube-video-id",
    "title": "Video title"
  },
  "eligibility": {
    "allowed": false,
    "reasons": [
      {
        "code": "SHORTS",
        "message": "Shorts videos are not supported."
      }
    ]
  }
}
```

If `allowed` is `true`, `reasons` should be an empty array and the frontend should not show a modal.

## Unsupported Cases

- `VR_360`: reject videos whose YouTube `contentDetails.projection` is `360`.
- `SHORTS`: reject URLs using the `/shorts/{video_id}` path. For MVP, URL shape is the source of truth.
- `NON_KOREAN`: reject videos whose `snippet.defaultAudioLanguage` or `snippet.defaultLanguage` is not `ko` or `ko-*`.
- `LANGUAGE_UNKNOWN`: reject videos when no language metadata is available.
- `TOO_LONG`: reject videos whose parsed `contentDetails.duration` is `>= 7200` seconds.
- `EMBEDDING_DISABLED`: reject videos whose YouTube `status.embeddable` is `false`.

## Backend Changes

1. Add `status` to the YouTube Data API `videos.list` `part` value.
2. Preserve whether the original URL was a Shorts URL during video ID parsing.
3. Add an eligibility service that accepts the YouTube API item plus URL context and returns `allowed` and `reasons`.
4. Add response schemas for eligibility reason code and message.
5. Return metadata and eligibility together from `GET /api/videos/metadata`.

## Tests

Add focused tests for:

- 360 video rejection.
- Shorts URL rejection.
- non-Korean language rejection.
- missing language rejection.
- duration `>= 7200` rejection.
- `status.embeddable == false` rejection.
- allowed Korean, embeddable, rectangular, under-2-hour video.
