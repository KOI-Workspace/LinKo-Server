from fastapi import APIRouter, FastAPI

from app.api import auth, users, videos

app = FastAPI(title="LinKo Server")
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(videos.router)
app.include_router(api_router)
