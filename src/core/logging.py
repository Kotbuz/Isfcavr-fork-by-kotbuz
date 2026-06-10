import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> None:
    if LOG_DIR.exists() and not LOG_DIR.is_dir():
        raise RuntimeError(f"Log path exists and is not a directory: {LOG_DIR}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Reduce noisy SQLAlchemy logging (most DB tracebacks will be handled and
    # logged explicitly by application code). Capture warnings to route them
    # through the logging system.
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.captureWarnings(True)


def get_logger(name: str):
    return logging.getLogger(name)
