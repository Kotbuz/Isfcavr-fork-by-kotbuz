import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.core.env import load_env
from src.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

load_env()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")

    if not all([db_user, db_password, db_name]):
        logger.critical("PostgreSQL configuration is required. Set DATABASE_URL or DB_USER, DB_PASSWORD, DB_NAME.")
        raise RuntimeError("PostgreSQL configuration is required. Set DATABASE_URL or DB_USER, DB_PASSWORD, DB_NAME.")

    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logger.info("Database configuration loaded: host=%s port=%s db=%s", db_host, db_port, db_name)
else:
    logger.info("Database configuration loaded from DATABASE_URL")

if not DATABASE_URL.startswith("postgresql"):
    logger.critical("DATABASE_URL must use PostgreSQL: %s", DATABASE_URL)
    raise RuntimeError("DATABASE_URL must use PostgreSQL: postgresql://...")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = None
    try:
        db = SessionLocal()
        try:
            yield db
        except Exception:
            # Log any exception that occurs while handling a request that
            # used the database session. This captures OperationalError and
            # other SQLAlchemy exceptions raised during query/commit.
            logger.critical("Database operation failed", exc_info=True)
            raise
    finally:
        if db is not None:
            db.close()


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception:
        logger.critical("Database initialization failed", exc_info=True)
        raise
