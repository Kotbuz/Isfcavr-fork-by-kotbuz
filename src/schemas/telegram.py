from pydantic import BaseModel, ConfigDict


class TelegramStatusResponse(BaseModel):
    linked: bool

    model_config = ConfigDict(from_attributes=True)


class TelegramLinkTokenResponse(BaseModel):
    link_url: str
    expires_at: str

    model_config = ConfigDict(from_attributes=True)


class TelegramConfirmRequest(BaseModel):
    code: str
    telegram_user_id: int

    model_config = ConfigDict(extra="forbid")


class TelegramConfirmResponse(BaseModel):
    ok: bool
    username: str

    model_config = ConfigDict(from_attributes=True)
