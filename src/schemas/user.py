from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Уникальное имя пользователя", examples=["owner1"])
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)", examples=["secret123"])
    confirm_password: str = Field(..., min_length=6, description="Подтверждение пароля", examples=["secret123"])

    model_config = ConfigDict(extra="forbid")


class LoginRequest(BaseModel):
    username: str = Field(..., description="Имя пользователя", examples=["owner1"])
    password: str = Field(..., description="Пароль", examples=["secret123"])

    model_config = ConfigDict(extra="forbid")


class AuthResponse(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    token: str = Field(
        ...,
        description="Bearer-токен для заголовка Authorization",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )

    model_config = ConfigDict(from_attributes=True)


class UserOut(BaseModel):
    id: int = Field(..., description="Идентификатор пользователя")
    username: str = Field(..., description="Имя пользователя")
    created_at: str = Field(..., description="Дата регистрации в формате ISO 8601")

    model_config = ConfigDict(from_attributes=True)
