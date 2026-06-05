"""Общие описания HTTP-ответов для OpenAPI / Swagger."""

from typing import Any


def _error(description: str, detail: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {"application/json": {"example": {"detail": detail}}},
    }


BAD_REQUEST = _error("Некорректные данные запроса", "Bad word detected")
UNAUTHORIZED = _error("Требуется авторизация", "Invalid username or password")
FORBIDDEN = _error("Доступ запрещён", "Invalid owner token")
NOT_FOUND = _error("Ресурс не найден", "Box not found")
TOO_MANY_REQUESTS = _error("Превышен лимит запросов", "Too many requests, please wait a minute")
INTERNAL_ERROR = _error("Внутренняя ошибка сервера", "Unable to create box")
VALIDATION_ERROR = _error(
    "Ошибка валидации тела запроса",
    [
        {
            "type": "string_too_short",
            "loc": ["body", "password"],
            "msg": "String should have at least 6 characters",
            "input": "123",
        }
    ],
)
