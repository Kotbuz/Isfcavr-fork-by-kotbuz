from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.middlewares.auth import validate_owner_token
from src.middlewares.rate_limit import check_rate
from src.models.box import Box
from src.models.feedback import Feedback
from src.openapi_responses import BAD_REQUEST, FORBIDDEN, NOT_FOUND, TOO_MANY_REQUESTS
from src.schemas.box import BoxFeedbacksResponse
from src.schemas.box import FeedbackOut as BoxFeedbackOut
from src.schemas.box import ReplyOut as BoxReplyOut
from src.schemas.feedback import FeedbackCreate, FeedbackOut
from src.schemas.reply import ReplyCreate, ReplyOut
from src.services.feedback_service import create_feedback
from src.services.reply_service import create_reply

router = APIRouter(tags=["feedback"])

_OWNER_SECURITY = [
    {"OwnerTokenQuery": []},
    {"OwnerTokenHeader": []},
]


@router.post(
    "/box/{uuid}/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_200_OK,
    summary="Отправить анонимный отзыв",
    description=(
        "Публичный эндпоинт: пользователь отправляет отзыв в ящик по `uuid` без авторизации. "
        "Текст проходит модерацию (длина, запрещённые слова, ссылки). Лимит: 10 запросов в минуту с IP."
    ),
    responses={
        200: {
            "description": "Отзыв принят",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "text": "Очень понравился сервис!",
                        "status": "approved",
                        "moderation_notes": None,
                        "created_at": "2026-06-05T12:00:00",
                        "replies": [],
                    }
                }
            },
        },
        400: BAD_REQUEST,
        404: NOT_FOUND,
        429: TOO_MANY_REQUESTS,
    },
)
def send_feedback(
    uuid: str,
    feedback: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    check_rate(request.client.host, "POST:/box/{uuid}/feedback")
    box = db.query(Box).filter(Box.uuid == uuid).first()
    if box is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    created = create_feedback(db, box.id, feedback.text)
    return FeedbackOut(
        id=created.id,
        text=created.text,
        status=created.status,
        moderation_notes=created.moderation_notes,
        created_at=created.created_at.isoformat(),
        replies=[],
    )


@router.get(
    "/box/{uuid}",
    response_model=BoxFeedbacksResponse,
    summary="Получить отзывы ящика (владелец)",
    description=(
        "Возвращает все отзывы и ответы для ящика. "
        "Требуется `owner_token`: query-параметр `token` или заголовок `X-Owner-Token`."
    ),
    responses={
        200: {
            "description": "Список отзывов",
            "content": {
                "application/json": {
                    "example": {
                        "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                        "feedbacks": [
                            {
                                "id": 1,
                                "text": "Очень понравился сервис!",
                                "status": "approved",
                                "moderation_notes": None,
                                "created_at": "2026-06-05T12:00:00",
                                "replies": [
                                    {
                                        "id": 1,
                                        "text": "Спасибо за отзыв!",
                                        "created_at": "2026-06-05T12:30:00",
                                    }
                                ],
                            }
                        ],
                    }
                }
            },
        },
        403: FORBIDDEN,
        404: NOT_FOUND,
    },
    openapi_extra={"security": _OWNER_SECURITY},
)
def get_feedbacks(
    uuid: str,
    token: str | None = Query(None, description="Owner token (альтернатива заголовку X-Owner-Token)"),
    x_owner_token: str | None = Header(None, alias="X-Owner-Token", description="Owner token ящика"),
    db: Session = Depends(get_db),
):
    box = db.query(Box).filter(Box.uuid == uuid).first()
    if box is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    provided_token = token or x_owner_token
    validate_owner_token(provided_token, box)

    feedbacks = []
    for fb in box.feedbacks:
        replies = [
            BoxReplyOut(id=reply.id, text=reply.text, created_at=reply.created_at.isoformat()) for reply in fb.replies
        ]
        feedbacks.append(
            BoxFeedbackOut(
                id=fb.id,
                text=fb.text,
                status=fb.status,
                moderation_notes=fb.moderation_notes,
                created_at=fb.created_at.isoformat(),
                replies=replies,
            )
        )

    return BoxFeedbacksResponse(uuid=box.uuid, feedbacks=feedbacks)


@router.post(
    "/feedback/{id}/reply",
    response_model=ReplyOut,
    status_code=status.HTTP_200_OK,
    summary="Ответить на отзыв (владелец)",
    description=(
        "Владелец отвечает на отзыв по его `id`. "
        "Нужен `owner_token` ящика (query `token` или заголовок `X-Owner-Token`). "
        "Лимит: 10 запросов в минуту с IP."
    ),
    responses={
        200: {
            "description": "Ответ создан",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "text": "Спасибо за обратную связь!",
                        "created_at": "2026-06-05T12:30:00",
                    }
                }
            },
        },
        400: BAD_REQUEST,
        403: FORBIDDEN,
        404: NOT_FOUND,
        429: TOO_MANY_REQUESTS,
    },
    openapi_extra={"security": _OWNER_SECURITY},
)
def reply(
    id: int,
    request: Request,
    reply_data: ReplyCreate,
    token: str | None = Query(None, description="Owner token ящика"),
    x_owner_token: str | None = Header(None, alias="X-Owner-Token", description="Owner token ящика"),
    db: Session = Depends(get_db),
):
    check_rate(request.client.host, "POST:/feedback/{id}/reply")
    feedback = db.query(Feedback).filter(Feedback.id == id).first()
    if feedback is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    box = db.query(Box).filter(Box.id == feedback.box_id).first()
    if box is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    provided_token = token or x_owner_token
    validate_owner_token(provided_token, box)

    created = create_reply(db, feedback.id, reply_data.text)
    return ReplyOut(id=created.id, text=created.text, created_at=created.created_at.isoformat())
