from sqlalchemy.orm import Session

from src.models.user import User
from src.utils.security import generate_auth_token, hash_password, verify_password


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_user_by_token(db: Session, token: str) -> User | None:
    return db.query(User).filter(User.auth_token == token).first()


def create_user(db: Session, username: str, password: str) -> User:
    password_hash = hash_password(password)
    auth_token = generate_auth_token()
    user = User(username=username, password_hash=password_hash, auth_token=auth_token)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.auth_token:
        user.auth_token = generate_auth_token()
        db.commit()
        db.refresh(user)
    return user
