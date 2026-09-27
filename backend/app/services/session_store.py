"""Session storage for an in-progress ServiceNow OAuth authorization attempt
(the window between /profiles/servicenow/oauth/start and .../oauth/callback).

The resulting connection itself is NOT stored here - per #39 it's persisted
as a ServiceNowProfile row owned by the logged-in InstanceMate user (see
servicenow_profile_service.py), not session state, so saved profiles
survive across logins/devices instead of being tied to one browser session.
"""

import time

from flask import current_app, session

from app.services.crypto import decrypt_json, encrypt_json

_PENDING_KEY = "sn_oauth_pending"


def _secret() -> str:
    return current_app.config["SESSION_SECRET"]


def _pending_lifetime() -> int:
    return current_app.config["PENDING_AUTHORIZATION_LIFETIME_SECONDS"]


def store_pending_authorization(
    state: str,
    label: str,
    instance_url: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
) -> None:
    session.permanent = True
    session[_PENDING_KEY] = encrypt_json(
        {
            "state": state,
            "label": label,
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
