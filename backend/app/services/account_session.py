"""Tracks which InstanceMate account is logged in for the current session.

Independent of session_store.py (ServiceNow) and llm_session_store.py (LLM
provider) - just an integer user id, not a secret, so it's kept plainly in
Flask's signed session rather than Fernet-encrypted like those are.
"""

from flask import session

_USER_ID_KEY = "account_user_id"


def login_user(user_id: int) -> None:
    session.permanent = True
    session[_USER_ID_KEY] = user_id


def get_current_user_id() -> int | None:
    return session.get(_USER_ID_KEY)


def logout_user() -> None:
    session.pop(_USER_ID_KEY, None)
