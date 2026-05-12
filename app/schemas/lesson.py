from pydantic import BaseModel, Field


class LessonCreateRequest(BaseModel):
    youtube_url: str = Field(alias="youtubeUrl", min_length=1)


class LessonCreateResponse(BaseModel):
    lessonId: str
    generationStatus: str


class LessonSummary(BaseModel):
    id: str
    title: str
    channelName: str
    thumbnailUrl: str | None = None
    duration: str | None = None
    date: str | None = None
    generationStatus: str
    flashcardDone: bool = False
    subtitleDone: bool = False
    errorCode: str | None = None
    errorMessage: str | None = None


class LessonListResponse(BaseModel):
    lessons: list[LessonSummary]


class LessonStatusResponse(LessonSummary):
    transcriptStatus: str
    transcriptSource: str | None = None
