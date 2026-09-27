from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.user import User
from app.services import account_validation


class AccountError(Exception):
    """Raised when registration/login can't proceed for a user-facing reason."""


def register_user(raw_email: str, raw_username: str, raw_password: str) -> User:
    email = account_validation.validate_email(raw_email)
    username = account_validation.validate_username(raw_username)
    password = account_validation.validate_password(raw_password)

    if User.query.filter_by(email=email).first() is not None:
        raise AccountError("Email is already registered")
    if User.query.filter_by(username=username).first() is not None:
        raise AccountError("Username is already taken")

    user = User(
        email=email, username=username, password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(raw_email: str, raw_password: str) -> User:
    email = raw_email.strip().lower()
    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, raw_password):
        # Deliberately the same message either way, so a login attempt can't
        # be used to discover whether an email is registered.
        raise AccountError("Invalid email or password")
    return user


def get_user(user_id: int) -> User | None:
    return db.session.get(User, user_id)
