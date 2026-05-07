from dataclasses import dataclass
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

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
    except HTTPError as exc:
        if exc.code in (400, 401):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "invalid_google_token",
                    "message": "Invalid Google token",
                },
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "google_verification_failed",
                "message": "Google token verification failed",
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "google_verification_failed",
                "message": "Google token verification failed",
            },
        ) from exc

    if payload.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_google_token",
                "message": "Invalid Google token audience",
            },
        )

    return GoogleUserInfo(
        sub=payload["sub"],
        email=payload["email"],
        name=payload.get("name", payload["email"]),
        picture=payload.get("picture"),
    )
