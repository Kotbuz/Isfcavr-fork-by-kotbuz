from fastapi import HTTPException, status

from src.models.reply import Reply
from src.utils.validators import moderate_text


def create_reply(db, feedback_id, text):
    try:
        text = moderate_text(text)
    except ValueError as e:
        # Normalize moderation errors into a proper API response.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    reply = Reply(feedback_id=feedback_id, text=text)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply
