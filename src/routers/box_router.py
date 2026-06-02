from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.middlewares.rate_limit import check_rate
from src.schemas.box import BoxCreateResponse
from src.services.box_service import create_box
from src.services.user_service import get_user_by_token

router = APIRouter()


@router.post("/box", response_model=BoxCreateResponse, status_code=status.HTTP_200_OK)
def create_box_endpoint(
    request: Request, authorization: str = Header(None, alias="Authorization"), db: Session = Depends(get_db)
):
    check_rate(request.client.host, "POST:/box")
    user_id = None
    if authorization:
        token = authorization
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        user = get_user_by_token(db, token)
        if user:
            user_id = user.id
    box = create_box(db, user_id=user_id)
    if not box:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to create box")
    return box
