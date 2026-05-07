# FastAPI MVP Design

## Goal

Build the first backend API for LinKo Server with Python FastAPI. The MVP covers Google login, authenticated profile lookup, and YouTube video metadata lookup for a separate frontend client.

## Scope

In scope:

- Google login through frontend-provided Google ID tokens.
- Backend-issued JWT access tokens.
- User profile persistence in PostgreSQL.
- Authenticated profile lookup.
- Authenticated YouTube metadata lookup using YouTube Data API v3.
- `/api` prefix for all application endpoints.

Out of scope for this MVP:

- Refresh tokens.
- Admin features.
- Caption/STT/Gemini analysis pipeline.
- Background workers and queues.
- Frontend UI implementation.

## API Design

All application endpoints use the `/api` prefix.

```text
POST /api/auth/google
GET  /api/me
GET  /api/videos/metadata?url={youtube_url}
```

`POST /api/auth/google` accepts a Google ID token from the frontend. The backend verifies the token with Google, upserts the user by `google_sub`, and returns a JWT access token plus basic user data.

`GET /api/me` requires `Authorization: Bearer <access_token>` and returns the current user's `id`, `email`, `name`, and `picture`.

`GET /api/videos/metadata` requires authentication, extracts the YouTube video ID from the URL, fetches metadata from YouTube Data API v3, caches the video row, records the user's lookup, and returns frontend-ready metadata.

## Response Data

Video metadata response:

```json
{
  "video_id": "abc123",
  "title": "Example title",
  "published_at": "2026-05-08T00:00:00Z",
  "thumbnail_url": "https://...",
  "channel_title": "Example Channel",
  "duration_seconds": 754,
  "duration_text": "12:34",
  "url": "https://www.youtube.com/watch?v=abc123"
}
```

## Architecture

```text
app/
  main.py
  core/config.py
  core/security.py
  api/auth.py
  api/users.py
  api/videos.py
  db/session.py
  db/base.py
  models/user.py
  models/video.py
  schemas/auth.py
  schemas/user.py
  schemas/video.py
  services/google_auth.py
  services/youtube.py
```

Routes stay thin. Service modules handle Google verification, YouTube API calls, URL parsing, duration conversion, and persistence decisions. Schemas define request and response contracts.

## Database

Use PostgreSQL with SQLAlchemy 2.x and Alembic.

Tables:

- `users`: `id`, `google_sub`, `email`, `name`, `picture`, timestamps.
- `videos`: `id`, `youtube_video_id`, `title`, `channel_title`, `thumbnail_url`, `duration_seconds`, `published_at`, `raw_youtube_response`, timestamps.
- `video_queries`: `id`, `user_id`, `video_id`, `requested_url`, `created_at`.

Use unique indexes on `users.google_sub`, `users.email`, and `videos.youtube_video_id`.

## Configuration

Environment variables:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `GOOGLE_CLIENT_ID`
- `YOUTUBE_API_KEY`

Provide `.env.example` without secrets.

## Error Handling

Return `401` for missing or invalid JWTs, `400` for invalid YouTube URLs, `404` when YouTube reports a missing video, and `502` when Google or YouTube upstream calls fail unexpectedly. Error responses should use one consistent JSON shape.

## Testing

Use pytest with FastAPI's test client. Cover Google token exchange with mocked Google verification, `/api/me` auth success/failure, YouTube URL parsing, duration parsing, metadata lookup with mocked YouTube responses, and database upsert behavior.
