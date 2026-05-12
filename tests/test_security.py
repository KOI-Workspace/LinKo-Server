from datetime import UTC, datetime

import jwt
import pytest

from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trips_subject():
    token = create_access_token(subject="user-123")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert datetime.fromtimestamp(payload["exp"], tz=UTC) > datetime.now(UTC)


def test_decode_access_token_rejects_invalid_signature():
    tampered_token = jwt.encode(
        {"sub": "user-123"},
        "different-secret-key-for-negative-test",
        algorithm="HS256",
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)
