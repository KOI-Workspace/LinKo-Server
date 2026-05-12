# LinKo Server

FastAPI server skeleton for LinKo.

## Local Development

Start PostgreSQL:

```sh
docker compose up -d postgres
```

The local container publishes PostgreSQL on host port `5433` to avoid conflicts with an existing local PostgreSQL on `5432`.

Install development dependencies:

```sh
python3 -m pip install -e ".[dev]"
```

Create `.env` from `.env.example`, then fill `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, and `YOUTUBE_API_KEY`.

Run database migrations:

```sh
python3 -m alembic upgrade head
```

Run tests:

```sh
python3 -m pytest -v
```

Run the development server:

```sh
python3 -m uvicorn app.main:app --reload
```

## API Notes

All application endpoints are prefixed with `/api`.

- `POST /api/auth/google`: exchange a frontend Google ID token for a service JWT.
- `GET /api/me`: return the authenticated user's name, email, and profile image.
- `GET /api/videos/metadata?url=...`: return YouTube video metadata.
- `POST /api/lessons`: create a generating lesson from a YouTube URL and start background artifact generation.
- `GET /api/lessons`: list the authenticated user's lessons.
- `GET /api/lessons/{lesson_id}`: return lesson generation status for polling.
- `GET /api/lessons/{lesson_id}/flashcards`: return frontend-ready word and ending flashcards for a lesson.
- `GET /api/lessons/{lesson_id}/subtitles`: return transcript lines, vocab hover data, and cultural notes for watch mode.
- `POST /api/youtube/channels/sync`: sync Korean subscribed channels from a Google YouTube access token.
- `GET /api/youtube/channels`: list synced channels newest first.

Lesson generation uses `AI_PROVIDER=mock` by default for local deterministic output. Set `AI_PROVIDER=gemini` and `GEMINI_API_KEY` to call Gemini for real artifacts.

For channel sync, the frontend should request this additional Google scope:

```text
https://www.googleapis.com/auth/youtube.readonly
```

Stop local services:

```sh
docker compose down
```
