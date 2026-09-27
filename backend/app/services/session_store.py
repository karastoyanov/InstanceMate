"""Shared session storage for the ServiceNow connection.

Both auth flows (#8 OAuth, #9 basic auth) plug into this module rather than
managing their own storage: it's the one place that knows how a connection
is kept between requests, so which login method was used stays an
implementation detail behind `get_connection()` / `store_*_connection()` /
`clear_connection()`.

Everything sensitive (tokens, the OAuth client secret, the basic auth
password) is kept server-side in Flask's signed session, and additionally
Fernet-encrypted (keyed from SESSION_SECRET) so it isn't sitting as
plaintext even in the session cookie. Nothing here is ever logged or
returned to the client - routes only ever read specific non-secret fields
(instance_url, auth_type) out of the decrypted dict.
"""

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


def _pending_lifetime() -> int:
    return current_app.config["PENDING_AUTHORIZATION_LIFETIME_SECONDS"]


def _session_lifetime() -> int:
    return current_app.config["SESSION_LIFETIME_SECONDS"]


def store_pending_authorization(
    state: str, instance_url: str, client_id: str, client_secret: str, redirect_uri: str
) -> None:
    session.permanent = True
    session[_PENDING_KEY] = encrypt_json(
        {
            "state": state,
            "instance_url": instance_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "created_at": time.time(),
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
    if time.time() - data["created_at"] > _pending_lifetime():
        return None
    return data


def store_oauth_connection(
    instance_url: str, client_id: str, client_secret: str, token_response: dict
) -> None:
    session.permanent = True
    session[_CONNECTION_KEY] = encrypt_json(
        {
            "auth_type": "oauth",
            "instance_url": instance_url,
            "client_id": client_id,
            "client_secret": client_secret,
            "access_token": token_response["access_token"],
            "refresh_token": token_response.get("refresh_token"),
            "expires_at": time.time() + float(token_response.get("expires_in", 0)),
            "established_at": _existing_established_at() or time.time(),
        },
        _secret(),
    )


def store_basic_connection(instance_url: str, username: str, password: str) -> None:
    session.permanent = True
    session[_CONNECTION_KEY] = encrypt_json(
        {
            "auth_type": "basic",
            "instance_url": instance_url,
            "username": username,
            "password": password,
            "established_at": time.time(),
        },
        _secret(),
    )


def _existing_established_at() -> float | None:
    """established_at of the current connection, if any - preserved across
    an OAuth token refresh so the session's absolute lifetime is measured
    from login, not from the last refresh."""
    raw = session.get(_CONNECTION_KEY)
    if raw is None:
        return None
    data = decrypt_json(raw, _secret())
    return data.get("established_at") if data else None


def get_connection() -> dict | None:
    """The current connection, or None if there isn't one or it has expired.

    A session older than SESSION_LIFETIME_SECONDS is treated as logged out
    and cleared, independent of how long-lived the underlying ServiceNow
    OAuth token/refresh token is - this bounds how long a stolen session
    cookie stays useful.
    """
    raw = session.get(_CONNECTION_KEY)
    if raw is None:
        return None

    data = decrypt_json(raw, _secret())
    if data is None:
        clear_connection()
        return None

    if time.time() - data["established_at"] > _session_lifetime():
        clear_connection()
        return None

    return data


def clear_connection() -> None:
    """Log out of ServiceNow: drop both the active connection and any
    stray pending-authorization state. Scoped to this module's own keys -
    other independent session data (e.g. the LLM provider config) is left
    alone, since disconnecting ServiceNow shouldn't reset unrelated
    settings."""
    session.pop(_CONNECTION_KEY, None)
    session.pop(_PENDING_KEY, None)


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
