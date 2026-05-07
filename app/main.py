from fastapi import APIRouter, FastAPI

app = FastAPI(title="LinKo Server")
api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
