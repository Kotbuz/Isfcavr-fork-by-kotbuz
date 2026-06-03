from pathlib import Path

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOADED = False


def load_env() -> None:
    global _LOADED
    if _LOADED:
        return
    load_dotenv(_PROJECT_ROOT / ".env")
    _LOADED = True
