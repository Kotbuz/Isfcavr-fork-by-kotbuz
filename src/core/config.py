import os


def get_telegram_bot_token() -> str | None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    return token or None


def get_telegram_bot_username() -> str:
    return os.getenv("TELEGRAM_BOT_USERNAME", "KotbuzBot").strip().lstrip("@")


def get_public_frontend_url() -> str:
    return os.getenv("PUBLIC_FRONTEND_URL", "http://localhost:5173").rstrip("/")


def get_internal_bot_secret() -> str:
    return os.getenv("INTERNAL_BOT_SECRET", "").strip()


def get_telegram_proxy_url() -> str | None:
    proxy = os.getenv("TELEGRAM_PROXY_URL", "").strip()
    return proxy or None
