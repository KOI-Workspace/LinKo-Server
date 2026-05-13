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
Set `DISCORD_WAITLIST_WEBHOOK_URL` too if you want waitlist signups to post to Discord.

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

## EC2 Deployment

The production deployment uses GitHub Actions to copy the app to an EC2 instance
and restart Docker Compose there. Configure these GitHub environment secrets for
the `production` environment:

- `EC2_HOST`: EC2 public host or IP address.
- `EC2_USER`: SSH user, for example `ubuntu`.
- `EC2_SSH_KEY`: private key with SSH access to the instance.
- `EC2_PORT`: optional SSH port, defaults to `22`.
- `EC2_DEPLOY_PATH`: optional deploy directory, defaults to `/opt/linko-server`.
- `PROD_ENV`: full contents of the production `.env` file. Use `.env.example` as
  the template, and replace secrets before deploying.

On the EC2 instance, install Docker and the Docker Compose plugin first. Then run
the `Deploy to EC2` workflow manually, or merge to `main` to deploy
automatically. The workflow builds the FastAPI image on EC2, starts the API and
PostgreSQL containers, and runs Alembic migrations.
