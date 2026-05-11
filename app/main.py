from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, flashcards, lessons, public, users, videos, waitlist, youtube
from app.core.config import get_settings

app = FastAPI(title="LinKo Server")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(public.router)
api_router.include_router(lessons.router)
api_router.include_router(flashcards.router)
api_router.include_router(users.router)
api_router.include_router(videos.router)
api_router.include_router(waitlist.router)
api_router.include_router(youtube.router)
app.include_router(api_router)
