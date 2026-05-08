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

Stop local services:

```sh
docker compose down
```
