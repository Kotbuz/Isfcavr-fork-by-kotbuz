from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    text: str


class ReplyOut(BaseModel):
    id: int
    text: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FeedbackOut(BaseModel):
    id: int
    text: str
    status: str
    moderation_notes: str | None = None
    created_at: str
    replies: list[ReplyOut] = []

    model_config = ConfigDict(from_attributes=True)
