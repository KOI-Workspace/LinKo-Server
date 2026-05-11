from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import get_google_user
from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.services.google_auth import GoogleUserInfo


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    enable_sqlite_foreign_keys(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_google() -> GoogleUserInfo:
        return GoogleUserInfo("google-flashcards", "flash@example.com", "Flash User", None)

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_google_user] = override_google
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def auth_headers(client: TestClient) -> dict[str, str]:
    login = client.post("/api/auth/google", json={"id_token": "token"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_lesson_flashcards_returns_frontend_contract(client: TestClient):
    headers = auth_headers(client)

    response = client.get("/api/lessons/3/flashcards", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["lessonId"] == "3"
    assert data["lessonTitle"] == "Korean Street Food Tour Seoul"
    assert len(data["cards"]) == 8

    word_card = data["cards"][0]
    assert word_card == {
        "id": "fc-3-1",
        "type": "word",
        "expression": "길거리 음식",
        "meaning": "Street food",
        "exampleSentence": "서울의 길거리 음식은 정말 다양하고 맛있어요.",
        "exampleTranslation": "Street food in Seoul is incredibly diverse and delicious.",
        "video": {"youtubeId": "dQw4w9WgXcQ", "startSec": 12, "endSec": 28},
        "relatedVideos": [
            {
                "id": "7",
                "title": "10 Must-Know Korean Slang Words",
                "channelName": "Talk To Me In Korean",
                "thumbnailUrl": None,
                "startSec": 45,
            },
            {
                "id": "8",
                "title": "Korean Food Vocabulary with Chef",
                "channelName": "Maangchi",
                "thumbnailUrl": None,
                "startSec": 102,
            },
        ],
        "dailyConversation": [
            {"text": "한국 길거리 음식 먹어본 적 있어요?", "isQuestion": True},
            {"text": "네! 떡볶이랑 호떡이 제일 맛있었어요.", "isQuestion": False},
        ],
    }

    ending_card = data["cards"][3]
    assert ending_card["type"] == "ending"
    assert ending_card["baseWord"] == "가득하다"
    assert ending_card["conjugatedForm"] == "가득해요"
    assert ending_card["conjugationBadges"] == [
        {
            "removed": "하",
            "added": "해요",
            "removedDetail": {
                "category": "어간변화",
                "subCategories": ["Contraction"],
                "explanation": "The stem-final \"하\" in 하다 verbs contracts with a following vowel ending. 하 + 아/어 -> 해 is an irregular but extremely common pattern.",
            },
            "addedDetail": {
                "category": "어말-종결",
                "subCategories": ["Declarative", "Informal"],
                "explanation": "The most common polite sentence-final ending in everyday conversation. Expresses present tense in a friendly, polite manner.",
            },
        }
    ]


def test_lesson_flashcards_supports_other_mock_lessons(client: TestClient):
    headers = auth_headers(client)

    response = client.get("/api/lessons/4/flashcards", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["lessonId"] == "4"
    assert data["cards"][2]["type"] == "ending"
    assert data["cards"][2]["ending"] == "았/었어요"


def test_lesson_flashcards_returns_404_when_missing(client: TestClient):
    headers = auth_headers(client)

    response = client.get("/api/lessons/999/flashcards", headers=headers)

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "code": "flashcards_not_found",
            "message": "Flashcards are not available for this lesson.",
        }
    }
