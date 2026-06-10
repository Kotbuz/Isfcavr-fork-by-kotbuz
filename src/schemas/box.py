from pydantic import BaseModel, ConfigDict, Field


class BoxCreateResponse(BaseModel):
    uuid: str = Field(..., description="Публичный UUID ящика отзывов", examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"])
    owner_token: str = Field(
        ...,
        description="Секретный токен владельца для чтения отзывов и ответов",
        examples=["owner_secret_token_xyz"],
    )

    model_config = ConfigDict(from_attributes=True)


class BoxUuidOut(BaseModel):
    uuid: str = Field(..., description="UUID ящика")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601")

    model_config = ConfigDict(from_attributes=True)


class UserBoxesResponse(BaseModel):
    boxes: list[BoxUuidOut] = Field(default_factory=list, description="Ящики, привязанные к аккаунту")

    model_config = ConfigDict(from_attributes=True)


class ReplyOut(BaseModel):
    id: int = Field(..., description="Идентификатор ответа")
    text: str = Field(..., description="Текст ответа")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601")

    model_config = ConfigDict(from_attributes=True)


class FeedbackShortOut(BaseModel):
    id: int = Field(..., description="Идентификатор отзыва")
    box_uuid: str = Field(..., description="UUID ящика, в котором оставлен отзыв")
    text: str = Field(..., description="Текст отзыва")
    status: str = Field(..., description="Статус модерации")
    moderation_notes: str | None = Field(None, description="Заметки модерации")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601")
    replies: list[ReplyOut] = Field(default_factory=list, description="Ответы владельца")

    model_config = ConfigDict(from_attributes=True)


class UserFeedbacksResponse(BaseModel):
    feedbacks: list[FeedbackShortOut] = Field(default_factory=list, description="Все отзывы по ящикам пользователя")

    model_config = ConfigDict(from_attributes=True)


class FeedbackOut(BaseModel):
    id: int = Field(..., description="Идентификатор отзыва")
    text: str = Field(..., description="Текст отзыва")
    status: str = Field(..., description="Статус модерации")
    moderation_notes: str | None = Field(None, description="Заметки модерации")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601")
    replies: list[ReplyOut] = Field(default_factory=list, description="Ответы владельца")

    model_config = ConfigDict(from_attributes=True)


class BoxFeedbacksResponse(BaseModel):
    uuid: str = Field(..., description="UUID ящика")
    feedbacks: list[FeedbackOut] = Field(default_factory=list, description="Список отзывов в ящике")

    model_config = ConfigDict(from_attributes=True)
