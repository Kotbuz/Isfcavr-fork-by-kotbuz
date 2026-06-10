import logging

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def validate_owner_token(token: str, box):
    if not token or token != box.owner_token:
        logger.warning("Invalid owner token provided for box %s", box.uuid)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid owner token")
