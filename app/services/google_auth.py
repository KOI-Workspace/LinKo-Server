from dataclasses import dataclass

import httpx
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

    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
            timeout=5,
        )
        if response.status_code in (400, 401):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "invalid_google_token",
                    "message": "Invalid Google token",
                },
            )
        response.raise_for_status()
        payload = response.json()
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "google_verification_failed",
                "message": "Google token verification failed",
            },
        ) from exc
    except ValueError as exc:
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
