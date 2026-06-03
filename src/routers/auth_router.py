from datetime import UTC

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.models.box import Box
from src.models.feedback import Feedback
from src.models.user import User
from src.schemas.box import BoxUuidOut, FeedbackShortOut, UserBoxesResponse, UserFeedbacksResponse
from src.schemas.box import ReplyOut as BoxReplyOut
from src.schemas.telegram import TelegramLinkTokenResponse, TelegramStatusResponse
from src.schemas.user import AuthResponse, LoginRequest, RegisterRequest
from src.services.telegram_link_service import (
    build_deep_link,
    create_link_code,
    get_telegram_status,
    unlink_telegram,
)
from src.services.user_service import authenticate_user, create_user, get_user_by_token, get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    if get_user_by_username(db, data.username) is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    user = create_user(db, data.username, data.password)
    return AuthResponse(username=user.username, token=user.auth_token)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return AuthResponse(username=user.username, token=user.auth_token)


@router.get("/me", response_model=AuthResponse)
def me(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    user = _get_user_or_401(authorization, db)
    return AuthResponse(username=user.username, token=user.auth_token)


def _get_user_or_401(authorization: str | None, db: Session) -> User:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header missing")
    token = authorization
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    user = get_user_by_token(db, token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


@router.get("/my-boxes", response_model=UserBoxesResponse)
def my_boxes(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    user = _get_user_or_401(authorization, db)
    items = [
        BoxUuidOut(uuid=box.uuid, created_at=box.created_at.isoformat())
        for box in db.query(Box).filter(Box.user_id == user.id).order_by(Box.created_at.desc()).all()
    ]
    return UserBoxesResponse(boxes=items)


@router.get("/my-feedbacks", response_model=UserFeedbacksResponse)
def my_feedbacks(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    user = _get_user_or_401(authorization, db)
    my_box_ids = [row[0] for row in db.query(Box.id).filter(Box.user_id == user.id).all()]
    if not my_box_ids:
        return UserFeedbacksResponse(feedbacks=[])

    feedbacks = []
    for fb in db.query(Feedback).filter(Feedback.box_id.in_(my_box_ids)).order_by(Feedback.created_at.desc()).all():
        box = db.query(Box).filter(Box.id == fb.box_id).first()
        if not box:
            continue
        replies = [
            BoxReplyOut(id=reply.id, text=reply.text, created_at=reply.created_at.isoformat()) for reply in fb.replies
        ]
        feedbacks.append(
            FeedbackShortOut(
                id=fb.id,
                box_uuid=box.uuid,
                text=fb.text,
                status=fb.status,
                moderation_notes=fb.moderation_notes,
                created_at=fb.created_at.isoformat(),
                replies=replies,
            )
        )
    return UserFeedbacksResponse(feedbacks=feedbacks)


@router.get("/telegram/status", response_model=TelegramStatusResponse)
def telegram_status(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    user = _get_user_or_401(authorization, db)
    return TelegramStatusResponse(linked=get_telegram_status(user))


@router.post("/telegram/link-token", response_model=TelegramLinkTokenResponse)
def telegram_link_token(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    user = _get_user_or_401(authorization, db)
    row = create_link_code(db, user)
    expires = row.expires_at.isoformat()
    if row.expires_at.tzinfo is None:
        expires = row.expires_at.replace(tzinfo=UTC).isoformat()
    return TelegramLinkTokenResponse(link_url=build_deep_link(row.code), expires_at=expires)


@router.delete("/telegram/unlink", status_code=status.HTTP_204_NO_CONTENT)
def telegram_unlink(authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)):
    user = _get_user_or_401(authorization, db)
    unlink_telegram(db, user)
