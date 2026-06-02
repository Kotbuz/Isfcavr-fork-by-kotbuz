from fastapi import HTTPException, status

from src.models.feedback import Feedback
from src.utils.validators import moderate_text


def create_feedback(db, box_id, text):
    try:
        text = moderate_text(text)
    except ValueError as e:
        # Normalize moderation errors into a proper API response.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    fb = Feedback(box_id=box_id, text=text, status="approved")
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb
