import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.middlewares.auth import validate_owner_token
from src.middlewares.rate_limit import check_rate
from src.models.box import Box
from src.models.feedback import Feedback
from src.schemas.box import BoxFeedbacksResponse
from src.schemas.box import FeedbackOut as BoxFeedbackOut
from src.schemas.box import ReplyOut as BoxReplyOut
from src.schemas.feedback import FeedbackCreate, FeedbackOut
from src.schemas.reply import ReplyCreate, ReplyOut
from src.services.feedback_service import create_feedback
from src.services.reply_service import create_reply

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/box/{uuid}/feedback", response_model=FeedbackOut, status_code=status.HTTP_200_OK)
def send_feedback(uuid: str, feedback: FeedbackCreate, request: Request, db: Session = Depends(get_db)):
    client_host = request.client.host if request.client else "unknown"
    check_rate(client_host, "POST:/box/{uuid}/feedback")
    logger.info("Feedback submission requested for box %s from %s", uuid, client_host)
    box = db.query(Box).filter(Box.uuid == uuid).first()
    if box is None:
        logger.warning("Feedback submission failed: box not found %s", uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    created = create_feedback(db, box.id, feedback.text)
    logger.info("Feedback created for box %s id=%s", uuid, created.id)
    # Normalize response types to match Pydantic schema (created_at is a string in API contract).
    return FeedbackOut(
        id=created.id,
        text=created.text,
        status=created.status,
        moderation_notes=created.moderation_notes,
        created_at=created.created_at.isoformat(),
        replies=[],
    )


@router.get("/box/{uuid}", response_model=BoxFeedbacksResponse)
def get_feedbacks(
    uuid: str,
    token: str = Query(None),
    x_owner_token: str = Header(None, alias="X-Owner-Token"),
    db: Session = Depends(get_db),
):
    logger.info("Feedback retrieval requested for box %s", uuid)
    box = db.query(Box).filter(Box.uuid == uuid).first()
    if box is None:
        logger.warning("Feedback retrieval failed: box not found %s", uuid)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    provided_token = token or x_owner_token
    validate_owner_token(provided_token, box)

    feedbacks = []
    for fb in box.feedbacks:
        replies = [
            BoxReplyOut(id=reply.id, text=reply.text, created_at=reply.created_at.isoformat()) for reply in fb.replies
        ]
        feedbacks.append(
            BoxFeedbackOut(
                id=fb.id,
                text=fb.text,
                status=fb.status,
                moderation_notes=fb.moderation_notes,
                created_at=fb.created_at.isoformat(),
                replies=replies,
            )
        )

    return BoxFeedbacksResponse(uuid=box.uuid, feedbacks=feedbacks)


@router.post("/feedback/{id}/reply", response_model=ReplyOut, status_code=status.HTTP_200_OK)
def reply(
    id: int,
    request: Request,
    reply_data: ReplyCreate,
    token: str = Query(None),
    x_owner_token: str = Header(None, alias="X-Owner-Token"),
    db: Session = Depends(get_db),
):
    client_host = request.client.host if request.client else "unknown"
    check_rate(client_host, "POST:/feedback/{id}/reply")
    logger.info("Reply creation requested for feedback id=%s from %s", id, client_host)
    feedback = db.query(Feedback).filter(Feedback.id == id).first()
    if feedback is None:
        logger.warning("Reply creation failed: feedback not found %s", id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    box = db.query(Box).filter(Box.id == feedback.box_id).first()
    if box is None:
        logger.warning("Reply creation failed: box not found for feedback %s", id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Box not found")

    provided_token = token or x_owner_token
    validate_owner_token(provided_token, box)

    created = create_reply(db, feedback.id, reply_data.text)
    logger.info("Reply created for feedback id=%s reply_id=%s", id, created.id)
    return ReplyOut(id=created.id, text=created.text, created_at=created.created_at.isoformat())
