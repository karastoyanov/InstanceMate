import time

from flask import current_app, session

from app.services import servicenow_oauth
from app.services.crypto import decrypt_json, encrypt_json

_PENDING_KEY = "sn_oauth_pending"
_CONNECTION_KEY = "sn_oauth_connection"

# Refresh the access token if it expires within this many seconds.
_EXPIRY_LEEWAY_SECONDS = 60


def _secret() -> str:
    return current_app.config["SESSION_SECRET"]


def store_pending_authorization(
    state: str, instance_url: str, client_id: str, client_secret: str, redirect_uri: str
) -> None:
    session[_PENDING_KEY] = encrypt_json(
        {
            "state": state,
            "instance_url": instance_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        },
        _secret(),
    )


def pop_pending_authorization(state: str) -> dict | None:
    """Consume and validate the pending authorization matching `state`."""
    raw = session.pop(_PENDING_KEY, None)
    if raw is None:
        return None
    data = decrypt_json(raw, _secret())
    if data is None or data.get("state") != state:
        return None
    return data


def store_oauth_connection(
    instance_url: str, client_id: str, client_secret: str, token_response: dict
) -> None:
    session[_CONNECTION_KEY] = encrypt_json(
        {
            "auth_type": "oauth",
            "instance_url": instance_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": token_response["access_token"],
            "refresh_token": token_response.get("refresh_token"),
            "expires_at": time.time() + float(token_response.get("expires_in", 0)),
        },
        _secret(),
    )


def store_basic_connection(instance_url: str, username: str, password: str) -> None:
    session[_CONNECTION_KEY] = encrypt_json(
        {
            "auth_type": "basic",
            "instance_url": instance_url,
            "username": username,
            "password": password,
        },
        _secret(),
    )


def get_connection() -> dict | None:
    raw = session.get(_CONNECTION_KEY)
    if raw is None:
        return None
    return decrypt_json(raw, _secret())


def clear_connection() -> None:
    session.pop(_CONNECTION_KEY, None)


def get_valid_access_token() -> str | None:
    """Return a live OAuth access token for the current session, refreshing
    it against ServiceNow first if it's expired or about to expire.

    Only meaningful for auth_type "oauth" connections; returns None for a
    basic-auth connection (or no connection at all).
    """
    connection = get_connection()
    if connection is None or connection.get("auth_type") != "oauth":
        return None

    if connection["expires_at"] - time.time() > _EXPIRY_LEEWAY_SECONDS:
        return connection["access_token"]

    if not connection.get("refresh_token"):
        clear_connection()
        return None

    try:
        token_response = servicenow_oauth.refresh_access_token(
            connection["instance_url"],
            connection["client_id"],
            connection["client_secret"],
            connection["refresh_token"],
        )
    except servicenow_oauth.OAuthError:
        clear_connection()
        return None

    store_oauth_connection(
        connection["instance_url"],
        connection["client_id"],
        connection["client_secret"],
        token_response,
    )
    return token_response["access_token"]
