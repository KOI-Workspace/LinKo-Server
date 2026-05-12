# YouTube Channel Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add authenticated APIs that sync a user's Korean YouTube subscriptions and return channel cards sorted newest first.

**Architecture:** Keep route handlers thin. Add channel persistence models, Pydantic schemas, a YouTube channel service for upstream calls/filtering, and an API module under `/api/youtube/channels`.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL/SQLite tests, httpx, pytest.

---

### Task 1: Channel Models And Migration

**Files:**
- Create: `app/models/youtube_channel.py`
- Create: `alembic/versions/20260509_0002_create_youtube_channels.py`

- [ ] Add `YoutubeChannel` with `youtube_channel_id`, `title`, `thumbnail_url`, `country`, `default_language`, `raw_youtube_response`, and timestamps.
- [ ] Add `UserYoutubeChannel` with `user_id`, `youtube_channel_id`, timestamps, and a unique `(user_id, youtube_channel_id)` constraint.
- [ ] Add Alembic tables, indexes, foreign keys, and matching downgrade.
- [ ] Run `python3 -m pytest tests/test_models.py -q`.

### Task 2: YouTube Channel Service

**Files:**
- Modify: `app/services/youtube.py`
- Test: `tests/test_youtube_service.py`

- [ ] Add `fetch_user_subscription_channel_ids(access_token)` using `subscriptions.list?part=snippet&mine=true`.
- [ ] Add `fetch_youtube_channels(channel_ids)` using `channels.list?part=snippet,brandingSettings`.
- [ ] Add `is_korean_channel(item)` using `brandingSettings.channel.country == "KR"` or `snippet.defaultLanguage` starting with `ko`.
- [ ] Add tests for Korean/non-Korean/missing-language filtering.
- [ ] Run `python3 -m pytest tests/test_youtube_service.py -q`.

### Task 3: Channel Schemas And API

**Files:**
- Create: `app/schemas/youtube_channel.py`
- Create: `app/api/youtube.py`
- Modify: `app/main.py`
- Test: `tests/test_youtube_channels_api.py`

- [ ] Add `YoutubeChannelSyncRequest` and `YoutubeChannelResponse`.
- [ ] Add `POST /api/youtube/channels/sync`, authenticated, accepting a Google YouTube access token.
- [ ] Add `GET /api/youtube/channels`, authenticated, sorted by `UserYoutubeChannel.created_at.desc()`.
- [ ] Upsert channel rows and user-channel links without duplicates.
- [ ] Add API tests for auth, token rejection, Korean filtering, duplicate sync, and newest-first sorting.
- [ ] Run `python3 -m pytest tests/test_youtube_channels_api.py -q`.

### Task 4: Verification

**Files:**
- Modify: `README.md` if command docs need updates.

- [ ] Run `python3 -m pytest -q`.
- [ ] Run `python3 -m compileall app tests alembic`.
- [ ] Run `python3 -m alembic upgrade head` against local PostgreSQL.
- [ ] Commit implementation changes after tests pass.
