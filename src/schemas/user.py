from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)

    model_config = ConfigDict(extra="forbid")


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(extra="forbid")


class AuthResponse(BaseModel):
    username: str
    token: str

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int
    username: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
