"""Session storage for the user's chosen LLM provider + BYOK API key.

Independent of the ServiceNow connection (session_store.py) - a session can
hold both at once, and clearing one must not clear the other. Stored the
same way: server-side in Flask's signed session, additionally
Fernet-encrypted so the key isn't sitting as plaintext in the cookie.
"""

from flask import current_app, session

from app.services.crypto import decrypt_json, encrypt_json

_LLM_CONFIG_KEY = "llm_config"


def _secret() -> str:
    return current_app.config["SESSION_SECRET"]


def store_llm_config(provider: str, api_key: str) -> None:
    session.permanent = True
    session[_LLM_CONFIG_KEY] = encrypt_json(
        {"provider": provider, "api_key": api_key}, _secret()
    )


def get_llm_config() -> dict | None:
    raw = session.get(_LLM_CONFIG_KEY)
    if raw is None:
        return None
    return decrypt_json(raw, _secret())


def clear_llm_config() -> None:
    session.pop(_LLM_CONFIG_KEY, None)
