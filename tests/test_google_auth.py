from urllib.error import HTTPError, URLError
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.services.google_auth import verify_google_id_token


def test_verify_google_id_token_maps_invalid_token_http_error_to_unauthorized():
    error = HTTPError(
        url="https://oauth2.googleapis.com/tokeninfo",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=None,
    )

    with patch("app.services.google_auth.urlopen", side_effect=error):
        with pytest.raises(HTTPException) as exc_info:
            verify_google_id_token("bad-google-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "invalid_google_token"


def test_verify_google_id_token_maps_network_failure_to_bad_gateway():
    with patch(
        "app.services.google_auth.urlopen",
        side_effect=URLError("network unavailable"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            verify_google_id_token("google-token")

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["code"] == "google_verification_failed"
