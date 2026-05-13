import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.models.waitlist import WaitlistEntry
from app.schemas.waitlist import WaitlistCreateRequest, WaitlistEntryResponse
from app.services.discord import notify_waitlist_signup

router = APIRouter(prefix="/waitlist", tags=["waitlist"])
logger = logging.getLogger(__name__)


@router.post("", response_model=WaitlistEntryResponse)
def create_waitlist_entry(
    request: WaitlistCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WaitlistEntry:
    entry = WaitlistEntry(
        user_id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        youtube_url=request.youtube_url,
        source=request.source,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    webhook_url = get_settings().discord_waitlist_webhook_url
    if webhook_url:
        try:
            notify_waitlist_signup(entry, webhook_url)
        except Exception:
            logger.exception("Failed to notify Discord for waitlist signup", extra={"waitlist_entry_id": entry.id})

    return entry
