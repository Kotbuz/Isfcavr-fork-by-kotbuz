import logging

from fastapi import HTTPException, status

from src.models.feedback import Feedback
from src.utils.validators import moderate_text

logger = logging.getLogger(__name__)


def create_feedback(db, box_id, text):
    try:
        text = moderate_text(text)
    except ValueError as e:
        logger.warning("Feedback moderation rejected for box_id=%s: %s", box_id, e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    fb = Feedback(box_id=box_id, text=text, status="approved")
    db.add(fb)
    db.commit()
    db.refresh(fb)
    logger.info("Created feedback id=%s for box_id=%s", fb.id, box_id)
    return fb
