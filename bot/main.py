import asyncio
import logging
import os
import sys

import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
from aiogram.filters import CommandStart
from aiogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000").rstrip("/")
BOT_SECRET = os.getenv("INTERNAL_BOT_SECRET", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "").strip()

POLL_RETRY_MIN_SECONDS = 5
POLL_RETRY_MAX_SECONDS = 120

dp = Dispatcher()


def _create_bot() -> Bot:
    if TELEGRAM_PROXY_URL:
        logger.info("Using TELEGRAM_PROXY_URL for Telegram API")
        session = AiohttpSession(proxy=TELEGRAM_PROXY_URL)
    else:
        session = AiohttpSession()
    return Bot(token=TELEGRAM_BOT_TOKEN, session=session)


async def _confirm_link_on_api(code: str, telegram_user_id: int) -> tuple[bool, str]:
    if not BOT_SECRET:
        return False, "Сервис привязки не настроен (INTERNAL_BOT_SECRET)."

    url = f"{API_BASE_URL}/internal/telegram/confirm"
    payload = {"code": code, "telegram_user_id": telegram_user_id}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-Bot-Secret": BOT_SECRET},
            )
            if resp.status_code == 200:
                data = resp.json()
                username = data.get("username", "")
                return True, f"Telegram привязан к аккаунту «{username}». Уведомления о новых отзывах включены."
            detail = "Не удалось привязать аккаунт."
            try:
                body = resp.json()
                if isinstance(body, dict) and body.get("detail"):
                    detail = str(body["detail"])
            except Exception:
                pass
            if resp.status_code == 400 and "expired" in detail.lower():
                detail = "Ссылка истекла. Создайте новую на сайте в админке."
            if resp.status_code == 400 and "already used" in detail.lower():
                detail = "Ссылка уже использована. Создайте новую на сайте."
            if resp.status_code == 404:
                detail = "Неверная ссылка. Создайте новую на сайте в админке."
            return False, detail
    except httpx.HTTPError as exc:
        logger.error("API confirm link error: %s", exc)
        return False, "Сервер недоступен. Попробуйте позже."


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    args = ""
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            args = parts[1].strip()

    if args.startswith("link_"):
        code = args[5:]
        if not code:
            await message.answer("Неверная ссылка привязки.")
            return
        ok, text = await _confirm_link_on_api(code, message.from_user.id)
        await message.answer(text)
        return

    await message.answer(
        "Бот уведомлений о новых отзывах.\n\n"
        "Чтобы привязать Telegram к аккаунту на сайте, откройте ссылку из админки."
    )


async def _run_polling_once() -> None:
    bot = _create_bot()
    try:
        logger.info("Starting Telegram bot polling")
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await bot.session.close()


async def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set")
        sys.exit(1)

    delay = POLL_RETRY_MIN_SECONDS
    while True:
        try:
            await _run_polling_once()
            delay = POLL_RETRY_MIN_SECONDS
        except TelegramNetworkError as exc:
            logger.error(
                "Нет соединения с api.telegram.org: %s. "
                "Часто это блокировка сети из Docker — включите VPN на ПК или задайте TELEGRAM_PROXY_URL в .env. "
                "Повтор через %s с.",
                exc,
                delay,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, POLL_RETRY_MAX_SECONDS)
        except Exception as exc:
            logger.exception("Bot polling stopped: %s", exc)
            await asyncio.sleep(delay)
            delay = min(delay * 2, POLL_RETRY_MAX_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
