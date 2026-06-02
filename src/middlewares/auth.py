from fastapi import HTTPException, status


def validate_owner_token(token: str, box):
    if not token or token != box.owner_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid owner token")
