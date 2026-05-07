from datetime import UTC, datetime

from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trips_subject():
    token = create_access_token(subject="user-123")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert datetime.fromtimestamp(payload["exp"], tz=UTC) > datetime.now(UTC)
