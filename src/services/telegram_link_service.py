from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from src.core.config import get_telegram_bot_username
from src.models.telegram_link_code import TelegramLinkCode
from src.models.user import User
from src.utils.security import generate_auth_token


LINK_TTL_MINUTES = 10


def _bot_username() -> str:
    return get_telegram_bot_username()


def build_deep_link(code: str) -> str:
    return f"https://t.me/{_bot_username()}?start=link_{code}"


def get_telegram_status(user: User) -> bool:
    return user.telegram_user_id is not None


def create_link_code(db: Session, user: User) -> TelegramLinkCode:
    expires_at = datetime.now(UTC) + timedelta(minutes=LINK_TTL_MINUTES)
    row = TelegramLinkCode(
        code=generate_auth_token()[:32],
        user_id=user.id,
        expires_at=expires_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def unlink_telegram(db: Session, user: User) -> None:
    user.telegram_user_id = None
    user.telegram_linked_at = None
    db.commit()


def confirm_link(db: Session, code: str, telegram_user_id: int) -> User:
    now = datetime.now(UTC)
    row = db.query(TelegramLinkCode).filter(TelegramLinkCode.code == code).first()
    if row is None:
        raise ValueError("invalid_code")
    if row.used_at is not None:
        raise ValueError("code_used")
    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < now:
        raise ValueError("code_expired")

    db.query(User).filter(User.telegram_user_id == telegram_user_id).update(
        {User.telegram_user_id: None, User.telegram_linked_at: None},
        synchronize_session=False,
    )

    user = db.query(User).filter(User.id == row.user_id).first()
    if user is None:
        raise ValueError("user_not_found")

    user.telegram_user_id = telegram_user_id
    user.telegram_linked_at = now
    row.used_at = now
    db.commit()
    db.refresh(user)
    return user
