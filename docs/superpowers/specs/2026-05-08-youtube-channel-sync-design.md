# YouTube Channel Sync Design

## Goal

Add a backend flow for the frontend `YouTube 연동` button. The user grants YouTube read-only access, the backend reads the user's subscribed channels, keeps only Korean channels, stores them, and returns them for channel card rendering.

## Scope

In scope:

- YouTube read-only OAuth access token accepted from the frontend.
- Current user's subscribed channel lookup through YouTube Data API v3.
- Korean channel filtering.
- Channel name and profile image persistence.
- Authenticated channel list API sorted by most recently added first.

Out of scope:

- Refresh token storage.
- Background channel synchronization.
- AI channel search behavior after the initial list is returned.
- Frontend UI implementation.

## User Flow

The existing Google site login remains unchanged. When the user clicks `YouTube 연동`, the frontend requests the additional scope:

```text
https://www.googleapis.com/auth/youtube.readonly
```

Google may show an account chooser or consent screen, but this is an additional permission grant rather than a separate site login. The frontend sends the resulting Google access token to the backend for one-time channel synchronization.

## API Design

All endpoints use the existing `/api` prefix and require `Authorization: Bearer <access_token>`.

```text
POST /api/youtube/channels/sync
GET  /api/youtube/channels
```

`POST /api/youtube/channels/sync` accepts:

```json
{
  "access_token": "google-youtube-readonly-access-token"
}
```

It returns the current user's stored Korean channels after synchronization.

`GET /api/youtube/channels` returns the current user's stored channels sorted by `created_at desc`, so the most recently added channel appears leftmost in the frontend.

## Data Model

Add user-specific channel storage:

- `youtube_channels`: `id`, `youtube_channel_id`, `title`, `thumbnail_url`, `country`, `default_language`, `raw_youtube_response`, timestamps.
- `user_youtube_channels`: `id`, `user_id`, `youtube_channel_id`, timestamps.

Use unique constraints on `youtube_channels.youtube_channel_id` and `(user_id, youtube_channel_id)`.

## YouTube API Usage

1. Call `subscriptions.list` with `part=snippet`, `mine=true`, and the user's OAuth access token.
2. Read `snippet.resourceId.channelId` from each subscription.
3. Call `channels.list` with `part=snippet,brandingSettings` and the collected channel IDs.
4. Store `snippet.title`, the best `snippet.thumbnails` URL, `snippet.defaultLanguage`, and `brandingSettings.channel.country`.

## Korean Channel Filtering

For MVP, a channel is considered Korean when either condition is true:

- `brandingSettings.channel.country == "KR"`
- `snippet.defaultLanguage` is `ko` or starts with `ko-`

If both values are missing or neither indicates Korean, exclude the channel from the saved list.

## Error Handling

Return `401` for missing or invalid service JWTs. Return `400` when the frontend omits the Google access token. Return `401` when YouTube rejects the Google access token. Return `502` when YouTube upstream calls fail unexpectedly.

## Testing

Cover:

- Sync requires service JWT authentication.
- Missing Google access token returns validation failure.
- YouTube access token rejection maps to `401`.
- Korean channels are stored and returned.
- non-Korean channels are excluded.
- Existing channels are updated without duplicate user-channel links.
- Channel list sorting is newest first.
