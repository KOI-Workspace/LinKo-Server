import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, TokenResponse
from app.services.discord import notify_new_user_signup
from app.services.google_auth import GoogleUserInfo, verify_google_id_token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def get_google_user(request: GoogleLoginRequest) -> GoogleUserInfo:
    return verify_google_id_token(request.id_token)


@router.post("/google", response_model=TokenResponse)
def google_login(
    db: Session = Depends(get_db),
    google_user: GoogleUserInfo = Depends(get_google_user),
) -> TokenResponse:
    user = db.scalar(select(User).where(User.google_sub == google_user.sub))
    is_new_user = user is None

    if is_new_user:
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

    webhook_url = get_settings().discord_new_user_webhook_url
    if is_new_user and webhook_url:
        try:
            notify_new_user_signup(user, webhook_url)
        except Exception:
            logger.exception("Failed to notify Discord for new Google login", extra={"user_id": user.id})

    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        user=user,
    )
