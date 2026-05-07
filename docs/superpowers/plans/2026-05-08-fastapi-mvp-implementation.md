# FastAPI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first LinKo Server FastAPI backend with Google login, JWT profile auth, PostgreSQL persistence, and YouTube metadata lookup under `/api`.

**Architecture:** Use a small layered FastAPI app: routes define HTTP contracts, services handle Google and YouTube integrations, models define SQLAlchemy persistence, and schemas define Pydantic request/response objects. Start with synchronous SQLAlchemy and test external calls with dependency overrides or monkeypatches.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic Settings, PyJWT, pytest, httpx, python-dotenv, psycopg.

---

## File Structure

- Create `pyproject.toml`: package metadata, runtime dependencies, pytest config.
- Create `.env.example`: required configuration names without secrets.
- Create `app/main.py`: FastAPI application and `/api` router registration.
- Create `app/core/config.py`: environment-backed settings.
- Create `app/core/security.py`: JWT creation and decoding helpers.
- Create `app/db/session.py`: SQLAlchemy engine, session factory, dependency.
- Create `app/db/base.py`: declarative base imports for Alembic.
- Create `app/models/user.py`: `users` table model.
- Create `app/models/video.py`: `videos` and `video_queries` table models.
- Create `app/schemas/auth.py`: Google login request and token response schemas.
- Create `app/schemas/user.py`: profile response schema.
- Create `app/schemas/video.py`: video metadata response schema.
- Create `app/services/google_auth.py`: Google ID token verification boundary.
- Create `app/services/youtube.py`: YouTube URL parsing, duration parsing, API fetch boundary.
- Create `app/api/auth.py`: `POST /api/auth/google`.
- Create `app/api/users.py`: `GET /api/me`.
- Create `app/api/videos.py`: `GET /api/videos/metadata`.
- Create `tests/`: pytest coverage for config, auth, profile, YouTube parsing, and video metadata lookup.

---

### Task 1: Project Skeleton and Health Endpoint

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_app.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_app.py -v`

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Add project metadata and minimal app**

Create `pyproject.toml`:

```toml
[project]
name = "linko-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "alembic>=1.13",
  "email-validator>=2.1",
  "fastapi>=0.111",
  "httpx>=0.27",
  "psycopg[binary]>=3.1",
  "pydantic-settings>=2.2",
  "pyjwt>=2.8",
  "python-dotenv>=1.0",
  "sqlalchemy>=2.0",
  "uvicorn[standard]>=0.29",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

Create `.env.example`:

```text
DATABASE_URL=postgresql+psycopg://linko:linko@localhost:5432/linko
JWT_SECRET_KEY=replace-with-local-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
GOOGLE_CLIENT_ID=replace-with-google-client-id
YOUTUBE_API_KEY=replace-with-youtube-api-key
```

Create `app/__init__.py` as an empty file.

Create `app/main.py`:

```python
from fastapi import APIRouter, FastAPI

app = FastAPI(title="LinKo Server")
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_app.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example app/__init__.py app/main.py tests/test_app.py
git commit -m "Add FastAPI project skeleton"
```

---

### Task 2: Settings and JWT Security

**Files:**
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`
- Create: `app/core/security.py`
- Test: `tests/test_security.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_security.py`:

```python
from datetime import UTC, datetime

from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trips_subject():
    token = create_access_token(subject="user-123")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert datetime.fromtimestamp(payload["exp"], tz=UTC) > datetime.now(UTC)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_security.py -v`

Expected: FAIL because `app.core.security` does not exist.

- [ ] **Step 3: Add settings and JWT helpers**

Create `app/core/__init__.py` as an empty file.

Create `app/core/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./linko-dev.db"
    jwt_secret_key: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    google_client_id: str = "dev-google-client-id"
    youtube_api_key: str = "dev-youtube-api-key"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

Create `app/core/security.py`:

```python
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.core.config import get_settings


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_security.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core tests/test_security.py
git commit -m "Add JWT security helpers"
```

---

### Task 3: Database Models and Session

**Files:**
- Create: `app/db/__init__.py`
- Create: `app/db/base.py`
- Create: `app/db/session.py`
- Create: `app/models/__init__.py`
- Create: `app/models/user.py`
- Create: `app/models/video.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_models.py`:

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.user import User
from app.models.video import Video, VideoQuery


def test_user_video_and_query_persist():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            google_sub="google-123",
            email="person@example.com",
            name="Person",
            picture="https://example.com/pic.png",
        )
        video = Video(
            youtube_video_id="abc123",
            title="Video",
            channel_title="Channel",
            thumbnail_url="https://example.com/thumb.jpg",
            duration_seconds=754,
            published_at=None,
            raw_youtube_response={"id": "abc123"},
        )
        session.add_all([user, video])
        session.flush()
        session.add(VideoQuery(user_id=user.id, video_id=video.id, requested_url="https://youtu.be/abc123"))
        session.commit()

    with Session(engine) as session:
        saved_user = session.scalar(select(User).where(User.google_sub == "google-123"))
        saved_video = session.scalar(select(Video).where(Video.youtube_video_id == "abc123"))
        query = session.scalar(select(VideoQuery))

    assert saved_user is not None
    assert saved_user.email == "person@example.com"
    assert saved_video is not None
    assert saved_video.raw_youtube_response == {"id": "abc123"}
    assert query is not None
    assert query.user_id == saved_user.id
    assert query.video_id == saved_video.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_models.py -v`

Expected: FAIL because database modules and models do not exist.

- [ ] **Step 3: Add database modules and models**

Create `app/db/__init__.py` and `app/models/__init__.py` as empty files.

Create `app/db/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Create `app/db/session.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Create `app/models/user.py`:

```python
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    picture: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
```

Create `app/models/video.py`:

```python
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    youtube_video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    channel_title: Mapped[str] = mapped_column(String(255))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_youtube_response: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class VideoQuery(Base):
    __tablename__ = "video_queries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), index=True)
    requested_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_models.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/db app/models tests/test_models.py
git commit -m "Add database models"
```

---

### Task 4: Google Login and Profile API

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/auth.py`
- Create: `app/api/users.py`
- Create: `app/schemas/__init__.py`
- Create: `app/schemas/auth.py`
- Create: `app/schemas/user.py`
- Create: `app/services/__init__.py`
- Create: `app/services/google_auth.py`
- Modify: `app/main.py`
- Test: `tests/test_auth_api.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_auth_api.py`:

```python
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.api.auth import get_google_user
from app.services.google_auth import GoogleUserInfo


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_google() -> GoogleUserInfo:
        return GoogleUserInfo(
            sub="google-123",
            email="person@example.com",
            name="Person",
            picture="https://example.com/pic.png",
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_google_login_creates_user_and_returns_access_token(client: TestClient):
    response = client.post("/api/auth/google", json={"id_token": "valid-google-token"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "person@example.com"


def test_me_returns_current_user_profile(client: TestClient):
    login = client.post("/api/auth/google", json={"id_token": "valid-google-token"})
    token = login.json()["access_token"]

    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "person@example.com",
        "name": "Person",
        "picture": "https://example.com/pic.png",
    }


def test_me_rejects_missing_token(client: TestClient):
    response = client.get("/api/me")

    assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_auth_api.py -v`

Expected: FAIL because auth routes, schemas, and service do not exist.

- [ ] **Step 3: Add auth schemas, service, routes, and router registration**

Create `app/api/__init__.py`, `app/schemas/__init__.py`, and `app/services/__init__.py` as empty files.

Create `app/schemas/user.py`:

```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    name: str
    picture: str | None

    model_config = ConfigDict(from_attributes=True)
```

Create `app/schemas/auth.py`:

```python
from pydantic import BaseModel

from app.schemas.user import UserProfile


class GoogleLoginRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
```

Create `app/services/google_auth.py`:

```python
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import urlopen
import json

from fastapi import HTTPException, status

from app.core.config import get_settings


@dataclass(frozen=True)
class GoogleUserInfo:
    sub: str
    email: str
    name: str
    picture: str | None


def verify_google_id_token(id_token: str) -> GoogleUserInfo:
    settings = get_settings()
    query = urlencode({"id_token": id_token})
    url = f"https://oauth2.googleapis.com/tokeninfo?{query}"

    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "google_verification_failed", "message": "Google token verification failed"},
        ) from exc

    if payload.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_google_token", "message": "Invalid Google token audience"},
        )

    return GoogleUserInfo(
        sub=payload["sub"],
        email=payload["email"],
        name=payload.get("name", payload["email"]),
        picture=payload.get("picture"),
    )
```

Create `app/api/auth.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, TokenResponse
from app.api.auth import get_google_user
from app.services.google_auth import GoogleUserInfo

router = APIRouter(prefix="/auth", tags=["auth"])


def get_google_user(request: GoogleLoginRequest) -> GoogleUserInfo:
    return verify_google_id_token(request.id_token)


@router.post("/google", response_model=TokenResponse)
def google_login(
    db: Session = Depends(get_db),
    google_user: GoogleUserInfo = Depends(get_google_user),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.google_sub == google_user.sub))

    if user is None:
        user = User(
            google_sub=google_user.sub,
            email=google_user.email,
            name=google_user.name,
            picture=google_user.picture,
        )
        db.add(user)
    else:
        user.email = google_user.email
        user.name = google_user.name
        user.picture = google_user.picture

    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        user=user,
    )
```

Create `app/api/users.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserProfile

router = APIRouter(tags=["users"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "missing_token", "message": "Missing bearer token"})

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "invalid_token", "message": "Invalid bearer token"}) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"code": "invalid_token", "message": "Invalid bearer token"})
    return user


@router.get("/me", response_model=UserProfile)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
```

Modify `app/main.py`:

```python
from fastapi import APIRouter, FastAPI

from app.api import auth, users

app = FastAPI(title="LinKo Server")
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(users.router)
app.include_router(api_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_auth_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api app/schemas app/services app/main.py tests/test_auth_api.py
git commit -m "Add Google login and profile API"
```

---

### Task 5: YouTube Metadata Service

**Files:**
- Create: `app/schemas/video.py`
- Create: `app/services/youtube.py`
- Test: `tests/test_youtube_service.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_youtube_service.py`:

```python
import pytest

from app.services.youtube import (
    extract_video_id,
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_youtube_service.py -v`

Expected: FAIL because `app.services.youtube` does not exist.

- [ ] **Step 3: Add video schema and YouTube helpers**

Create `app/schemas/video.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class VideoMetadataResponse(BaseModel):
    video_id: str
    title: str
    published_at: datetime | None
    thumbnail_url: str | None
    channel_title: str
    duration_seconds: int
    duration_text: str
    url: str
```

Create `app/services/youtube.py`:

```python
from datetime import datetime
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import urlopen
import json
import re

from fastapi import HTTPException, status

from app.core.config import get_settings

YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,}$")
DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]
        else:
            video_id = ""
    else:
        video_id = ""

    if not YOUTUBE_ID_PATTERN.match(video_id):
        raise ValueError("Invalid YouTube URL")
    return video_id


def parse_iso8601_duration_seconds(duration: str) -> int:
    match = DURATION_PATTERN.match(duration)
    if match is None:
        raise ValueError("Invalid YouTube duration")
    hours = int(match.group("hours") or 0)
    minutes = int(match.group("minutes") or 0)
    seconds = int(match.group("seconds") or 0)
    return hours * 3600 + minutes * 60 + seconds


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def select_thumbnail_url(thumbnails: dict) -> str | None:
    for key in ("maxres", "standard", "high", "medium", "default"):
        image = thumbnails.get(key)
        if image and image.get("url"):
            return image["url"]
    return None


def fetch_youtube_video_item(video_id: str) -> dict:
    settings = get_settings()
    query = urlencode(
        {
            "part": "snippet,contentDetails",
            "id": video_id,
            "key": settings.youtube_api_key,
        }
    )
    url = f"https://www.googleapis.com/youtube/v3/videos?{query}"

    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "youtube_upstream_failed", "message": "YouTube metadata lookup failed"},
        ) from exc

    items = payload.get("items", [])
    if not items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "youtube_video_not_found", "message": "YouTube video not found"},
        )
    return items[0]


def parse_published_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_youtube_service.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/schemas/video.py app/services/youtube.py tests/test_youtube_service.py
git commit -m "Add YouTube metadata helpers"
```

---

### Task 6: Video Metadata API

**Files:**
- Create: `app/api/videos.py`
- Modify: `app/main.py`
- Test: `tests/test_videos_api.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_videos_api.py`:

```python
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.services.google_auth import GoogleUserInfo, verify_google_id_token
import app.api.videos as videos_api


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_google() -> GoogleUserInfo:
        return GoogleUserInfo(
            sub="google-123",
            email="person@example.com",
            name="Person",
            picture=None,
        )

    def override_youtube(video_id: str) -> dict:
        assert video_id == "abc123XYZ00"
        return {
            "id": "abc123XYZ00",
            "snippet": {
                "title": "Example video",
                "publishedAt": "2026-05-08T00:00:00Z",
                "channelTitle": "Example Channel",
                "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
            },
            "contentDetails": {"duration": "PT12M34S"},
        }

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(videos_api, "fetch_youtube_video_item", override_youtube)
    try:
        yield TestClient(app)
    finally:
        monkeypatch.undo()
        app.dependency_overrides.clear()


def test_video_metadata_requires_auth(client: TestClient):
    response = client.get("/api/videos/metadata?url=https://youtu.be/abc123XYZ00")

    assert response.status_code == 401


def test_video_metadata_returns_frontend_ready_data(client: TestClient):
    login = client.post("/api/auth/google", json={"id_token": "token"})
    token = login.json()["access_token"]

    response = client.get(
        "/api/videos/metadata?url=https://youtu.be/abc123XYZ00",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "video_id": "abc123XYZ00",
        "title": "Example video",
        "published_at": "2026-05-08T00:00:00Z",
        "thumbnail_url": "https://example.com/thumb.jpg",
        "channel_title": "Example Channel",
        "duration_seconds": 754,
        "duration_text": "12:34",
        "url": "https://youtu.be/abc123XYZ00",
    }
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_videos_api.py -v`

Expected: FAIL because `/api/videos/metadata` does not exist.

- [ ] **Step 3: Add videos route and persistence**

Create `app/api/videos.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.video import Video, VideoQuery
from app.schemas.video import VideoMetadataResponse
from app.services.youtube import (
    extract_video_id,
    fetch_youtube_video_item,
    format_duration,
    parse_iso8601_duration_seconds,
    parse_published_at,
    select_thumbnail_url,
)

router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("/metadata", response_model=VideoMetadataResponse)
def get_video_metadata(
    url: str = Query(min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoMetadataResponse:
    try:
        youtube_video_id = extract_video_id(url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_youtube_url", "message": "Invalid YouTube URL"},
        ) from exc

    item = fetch_youtube_video_item(youtube_video_id)
    snippet = item["snippet"]
    content_details = item["contentDetails"]
    duration_seconds = parse_iso8601_duration_seconds(content_details["duration"])

    video = db.scalar(select(Video).where(Video.youtube_video_id == youtube_video_id))
    if video is None:
        video = Video(youtube_video_id=youtube_video_id, raw_youtube_response=item)
        db.add(video)

    video.title = snippet["title"]
    video.channel_title = snippet["channelTitle"]
    video.thumbnail_url = select_thumbnail_url(snippet.get("thumbnails", {}))
    video.duration_seconds = duration_seconds
    video.published_at = parse_published_at(snippet.get("publishedAt"))
    video.raw_youtube_response = item
    db.flush()
    db.add(VideoQuery(user_id=current_user.id, video_id=video.id, requested_url=url))
    db.commit()
    db.refresh(video)

    return VideoMetadataResponse(
        video_id=video.youtube_video_id,
        title=video.title,
        published_at=video.published_at,
        thumbnail_url=video.thumbnail_url,
        channel_title=video.channel_title,
        duration_seconds=video.duration_seconds,
        duration_text=format_duration(video.duration_seconds),
        url=url,
    )
```

Modify `app/main.py`:

```python
from fastapi import APIRouter, FastAPI

from app.api import auth, users, videos

app = FastAPI(title="LinKo Server")
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(videos.router)
app.include_router(api_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_videos_api.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/api/videos.py app/main.py tests/test_videos_api.py
git commit -m "Add video metadata API"
```

---

### Task 7: Alembic Setup and Final Verification

**Files:**
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/20260508_0001_create_initial_tables.py`
- Test: all tests

- [ ] **Step 1: Add Alembic configuration**

Create `alembic.ini`:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg://linko:linko@localhost:5432/linko

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Create `alembic/env.py`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.base import Base
from app.models import user, video

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 2: Add initial migration**

Create `alembic/versions/20260508_0001_create_initial_tables.py`:

```python
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision = "20260508_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("google_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("picture", sa.String(length=2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("youtube_video_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("channel_title", sa.String(length=255), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_youtube_response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_videos_id", "videos", ["id"])
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"], unique=True)

    op.create_table(
        "video_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id"), nullable=False),
        sa.Column("requested_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_video_queries_id", "video_queries", ["id"])
    op.create_index("ix_video_queries_user_id", "video_queries", ["user_id"])
    op.create_index("ix_video_queries_video_id", "video_queries", ["video_id"])


def downgrade() -> None:
    op.drop_index("ix_video_queries_video_id", table_name="video_queries")
    op.drop_index("ix_video_queries_user_id", table_name="video_queries")
    op.drop_index("ix_video_queries_id", table_name="video_queries")
    op.drop_table("video_queries")
    op.drop_index("ix_videos_youtube_video_id", table_name="videos")
    op.drop_index("ix_videos_id", table_name="videos")
    op.drop_table("videos")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
```

- [ ] **Step 3: Run full test suite**

Run: `python3 -m pytest -v`

Expected: PASS.

- [ ] **Step 4: Run compile check**

Run: `python3 -m compileall app tests`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add alembic.ini alembic app tests
git commit -m "Add database migrations"
```

---

## Self-Review

- Spec coverage: This plan covers `/api` prefix, Google login, JWT profile lookup, PostgreSQL persistence, YouTube Data API metadata lookup, consistent app layout, configuration, and tests.
- Placeholder scan: The plan contains no deferred implementation markers.
- Type consistency: User IDs are encoded as JWT `sub` strings and decoded to integers in `get_current_user`; video IDs use `youtube_video_id` in persistence and `video_id` in responses.
