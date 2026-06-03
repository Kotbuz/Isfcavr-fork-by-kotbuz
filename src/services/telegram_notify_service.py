import asyncio
import logging
import time

import httpx

from src.core.config import get_public_frontend_url, get_telegram_bot_token, get_telegram_proxy_url
from src.db.database import SessionLocal
from src.models.box import Box
from src.models.user import User

logger = logging.getLogger(__name__)

RETRY_DELAY_SECONDS = 2.0


def format_box_uuid(uuid_str: str) -> str:
    clean = uuid_str.replace("-", "")
    if len(clean) >= 8:
        return f"{clean[:4]}…{clean[-4:]}"
    return uuid_str


def _build_message(box_uuid: str) -> str:
    return f"Новый отзыв на ссылке {format_box_uuid(box_uuid)}"


def _send_sync(chat_id: int, text: str, button_url: str) -> bool:
    token = get_telegram_bot_token()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set; skipping notification")
        return False

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [[{"text": "Открыть на сайте", "url": button_url}]]
        },
    }
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    proxy = get_telegram_proxy_url()
    try:
        with httpx.Client(timeout=10.0, proxy=proxy) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200 and resp.json().get("ok"):
                return True
            logger.error(
                "Telegram sendMessage failed: status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
            return False
    except httpx.HTTPError as exc:
        logger.error("Telegram sendMessage request error: %s", exc)
        return False


def send_new_feedback_notification(telegram_user_id: int, box_uuid: str) -> None:
    text = _build_message(box_uuid)
    button_url = get_public_frontend_url()
    if _send_sync(telegram_user_id, text, button_url):
        return
    time.sleep(RETRY_DELAY_SECONDS)
    if not _send_sync(telegram_user_id, text, button_url):
        logger.error(
            "Telegram notification failed after retry for chat_id=%s box=%s",
            telegram_user_id,
            box_uuid,
        )


def notify_new_feedback_for_box(box_uuid: str) -> None:
    db = SessionLocal()
    try:
        box = db.query(Box).filter(Box.uuid == box_uuid).first()
        if box is None or box.user_id is None:
            return
        user = db.query(User).filter(User.id == box.user_id).first()
        if user is None or user.telegram_user_id is None:
            return
        send_new_feedback_notification(int(user.telegram_user_id), box_uuid)
    finally:
        db.close()


async def notify_new_feedback_for_box_async(box_uuid: str) -> None:
    await asyncio.to_thread(notify_new_feedback_for_box, box_uuid)
