from sqlalchemy.orm import Session

from src.models.box import Box
from src.utils.security import generate_token, generate_uuid


def create_box(db: Session, user_id: int | None = None) -> Box:
    box = Box(
        uuid=generate_uuid(),
        owner_token=generate_token(),
        user_id=user_id,
    )
    db.add(box)
    db.commit()
    db.refresh(box)
    return box
