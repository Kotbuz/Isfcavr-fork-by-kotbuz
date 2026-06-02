from pydantic import BaseModel, ConfigDict


class BoxCreateResponse(BaseModel):
    uuid: str
    owner_token: str

    model_config = ConfigDict(from_attributes=True)


class BoxUuidOut(BaseModel):
    uuid: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class UserBoxesResponse(BaseModel):
    boxes: list[BoxUuidOut] = []

    model_config = ConfigDict(from_attributes=True)


class ReplyOut(BaseModel):
    id: int
    text: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FeedbackShortOut(BaseModel):
    id: int
    box_uuid: str
    text: str
    status: str
    moderation_notes: str | None = None
    created_at: str
    replies: list[ReplyOut] = []

    model_config = ConfigDict(from_attributes=True)


class UserFeedbacksResponse(BaseModel):
    feedbacks: list[FeedbackShortOut] = []

    model_config = ConfigDict(from_attributes=True)


class FeedbackOut(BaseModel):
    id: int
    text: str
    status: str
    moderation_notes: str | None = None
    created_at: str
    replies: list[ReplyOut] = []

    model_config = ConfigDict(from_attributes=True)


class BoxFeedbacksResponse(BaseModel):
    uuid: str
    feedbacks: list[FeedbackOut] = []

    model_config = ConfigDict(from_attributes=True)
