from pydantic import BaseModel, ConfigDict, Field


class ReplyCreate(BaseModel):
    text: str = Field(
        ...,
        max_length=500,
        description="Текст ответа владельца (те же правила модерации, что и для отзыва).",
        examples=["Спасибо за обратную связь, мы уже работаем над улучшением."],
    )


class ReplyOut(BaseModel):
    id: int = Field(..., description="Идентификатор ответа")
    text: str = Field(..., description="Текст ответа")
    created_at: str = Field(..., description="Дата создания в формате ISO 8601", examples=["2026-06-05T12:30:00"])

    model_config = ConfigDict(from_attributes=True)
