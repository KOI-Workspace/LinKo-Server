from typing import Literal

from pydantic import BaseModel


class FlashcardVideo(BaseModel):
    youtubeId: str
    startSec: int
    endSec: int


class RelatedVideo(BaseModel):
    id: str
    title: str
    channelName: str
    thumbnailUrl: str | None = None
    startSec: int


class ConversationTurn(BaseModel):
    text: str
    isQuestion: bool


class BadgePartDetail(BaseModel):
    category: Literal[
        "선어말어미",
        "어말-종결",
        "어말-연결",
        "어말-전성",
        "어말-보조적",
        "어간변화",
    ]
    subCategories: list[str]
    explanation: str


class ConjugationBadge(BaseModel):
    removed: str | None = None
    added: str
    removedDetail: BadgePartDetail | None = None
    addedDetail: BadgePartDetail | None = None


class WordFlashcard(BaseModel):
    id: str
    type: Literal["word"] = "word"
    expression: str
    meaning: str
    exampleSentence: str
    exampleTranslation: str
    video: FlashcardVideo
    relatedVideos: list[RelatedVideo]
    dailyConversation: list[ConversationTurn] | None = None


class EndingFlashcard(BaseModel):
    id: str
    type: Literal["ending"]
    baseWord: str
    baseWordMeaning: str | None = None
    conjugatedForm: str
    conjugationBadges: list[ConjugationBadge]
    ending: str
    endingMeaning: str
    endingExplanation: str
    scriptSentence: str
    scriptTranslation: str
    video: FlashcardVideo
    relatedVideos: list[RelatedVideo]


AnyFlashcard = WordFlashcard | EndingFlashcard


class LessonFlashcardsResponse(BaseModel):
    lessonId: str
    lessonTitle: str
    cards: list[AnyFlashcard]
