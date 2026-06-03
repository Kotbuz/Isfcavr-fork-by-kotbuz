from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import get_internal_bot_secret
from src.db.database import get_db
from src.schemas.telegram import TelegramConfirmRequest, TelegramConfirmResponse
from src.services.telegram_link_service import confirm_link

router = APIRouter(prefix="/internal", tags=["internal"])


def _verify_bot_secret(x_bot_secret: str | None = Header(None, alias="X-Bot-Secret")) -> None:
    expected = get_internal_bot_secret()
    if not expected or not x_bot_secret or x_bot_secret != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/telegram/confirm", response_model=TelegramConfirmResponse)
def telegram_confirm(
    data: TelegramConfirmRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_bot_secret),
):
    try:
        user = confirm_link(db, data.code.strip(), data.telegram_user_id)
    except ValueError as exc:
        reason = str(exc)
        if reason == "invalid_code":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid link code") from exc
        if reason == "code_used":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link code already used") from exc
        if reason == "code_expired":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link code expired") from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to link") from exc

    return TelegramConfirmResponse(ok=True, username=user.username)
