from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    text: str = Field(
        ...,
        max_length=500,
        description="Текст анонимного отзыва (до 500 символов, без ссылок и запрещённых слов).",
        examples=["Очень понравился сервис, спасибо за быстрый ответ!"],
    )


class ReplyOut(BaseModel):
    id: int = Field(..., description="Идентификатор ответа")
    text: str = Field(..., description="Текст ответа владельца")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601", examples=["2026-06-05T12:00:00"])

    model_config = ConfigDict(from_attributes=True)


class FeedbackOut(BaseModel):
    id: int = Field(..., description="Идентификатор отзыва")
    text: str = Field(..., description="Текст отзыва")
    status: str = Field(..., description="Статус модерации", examples=["approved"])
    moderation_notes: str | None = Field(None, description="Заметки модерации, если есть")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601")
    replies: list[ReplyOut] = Field(default_factory=list, description="Ответы владельца на отзыв")

    model_config = ConfigDict(from_attributes=True)
