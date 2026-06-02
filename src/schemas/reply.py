from pydantic import BaseModel, ConfigDict


class ReplyCreate(BaseModel):
    text: str


class ReplyOut(BaseModel):
    id: int
    text: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
