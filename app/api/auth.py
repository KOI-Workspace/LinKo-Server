from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, TokenResponse
from app.services.google_auth import GoogleUserInfo, verify_google_id_token

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
