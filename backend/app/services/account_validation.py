import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")
_MIN_PASSWORD_LENGTH = 8


def validate_email(raw_email: str) -> str:
    email = raw_email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValueError("Enter a valid email address")
    return email


def validate_username(raw_username: str) -> str:
    username = raw_username.strip()
    if not _USERNAME_RE.match(username):
        raise ValueError("Username must be 3-32 characters: letters, numbers, - or _")
    return username


def validate_password(password: str) -> str:
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters")
    return password
