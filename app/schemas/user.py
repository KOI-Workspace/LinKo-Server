from pydantic import BaseModel, ConfigDict, EmailStr


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    name: str
    picture: str | None

    model_config = ConfigDict(from_attributes=True)
