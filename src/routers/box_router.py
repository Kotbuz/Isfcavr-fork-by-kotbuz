import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.middlewares.rate_limit import check_rate
from src.openapi_responses import INTERNAL_ERROR, TOO_MANY_REQUESTS
from src.schemas.box import BoxCreateResponse
from src.services.box_service import create_box
from src.services.user_service import get_user_by_token

router = APIRouter(tags=["boxes"])
logger = logging.getLogger(__name__)


@router.post(
    "/box",
    response_model=BoxCreateResponse,
    status_code=status.HTTP_200_OK,
    summary="Создать ящик отзывов",
    description=(
        "Создаёт новый Box с уникальным `uuid` и `owner_token`. "
        "Токен владельца нужен для просмотра отзывов и ответов. "
        "Опционально передайте `Authorization: Bearer <token>`, чтобы привязать ящик к аккаунту."
    ),
    responses={
        200: {
            "description": "Ящик успешно создан",
            "content": {
                "application/json": {
                    "example": {
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "owner_token": "owner_secret_token_xyz",
                    }
                }
            },
        },
        429: TOO_MANY_REQUESTS,
        500: INTERNAL_ERROR,
    },
)
def create_box_endpoint(
    request: Request,
    authorization: str | None = Header(
        None,
        alias="Authorization",
        description="Опционально: `Bearer <auth_token>` для привязки ящика к зарегистрированному пользователю",
    ),
    db: Session = Depends(get_db),
):
    client_host = request.client.host if request.client else "unknown"
    check_rate(client_host, "POST:/box")
    user_id = None
    if authorization:
        token = authorization
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        user = get_user_by_token(db, token)
        if user:
            user_id = user.id
    logger.info("Creating box request from %s for user_id=%s", client_host, user_id)
    box = create_box(db, user_id=user_id)
    if not box:
        logger.error("Unable to create box for user_id=%s", user_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create box")
    logger.info("Box created: %s for user_id=%s", box.uuid, user_id)
    return box
