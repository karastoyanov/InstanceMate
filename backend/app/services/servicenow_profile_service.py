import time

from flask import current_app

from app.extensions import db
from app.models.servicenow_profile import ServiceNowProfile
from app.services import servicenow_oauth
from app.services.crypto import decrypt_json, encrypt_json

# Refresh the access token if it expires within this many seconds.
_EXPIRY_LEEWAY_SECONDS = 60


def _secret() -> str:
    return current_app.config["SESSION_SECRET"]


def list_profiles(user_id: int) -> list[ServiceNowProfile]:
    return (
        ServiceNowProfile.query.filter_by(user_id=user_id)
        .order_by(ServiceNowProfile.created_at)
        .all()
    )


def get_profile(user_id: int, profile_id: int) -> ServiceNowProfile | None:
    return ServiceNowProfile.query.filter_by(id=profile_id, user_id=user_id).first()


def delete_profile(user_id: int, profile_id: int) -> bool:
    profile = get_profile(user_id, profile_id)
    if profile is None:
        return False
    db.session.delete(profile)
    db.session.commit()
    return True


def create_oauth_profile(
    user_id: int,
    label: str,
    instance_url: str,
    client_id: str,
    client_secret: str,
    token_response: dict,
) -> ServiceNowProfile:
    credentials = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": token_response["access_token"],
        "refresh_token": token_response.get("refresh_token"),
        "expires_at": time.time() + float(token_response.get("expires_in", 0)),
    }
    profile = ServiceNowProfile(
        user_id=user_id,
        label=label,
        instance_url=instance_url,
        auth_type="oauth",
        credentials_encrypted=encrypt_json(credentials, _secret()),
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def create_basic_profile(
    user_id: int, label: str, instance_url: str, username: str, password: str
) -> ServiceNowProfile:
    credentials = {"username": username, "password": password}
    profile = ServiceNowProfile(
        user_id=user_id,
        label=label,
        instance_url=instance_url,
        auth_type="basic",
        credentials_encrypted=encrypt_json(credentials, _secret()),
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def get_credentials(profile: ServiceNowProfile) -> dict:
    return decrypt_json(profile.credentials_encrypted, _secret())


def get_valid_access_token(profile: ServiceNowProfile) -> str | None:
    """Live OAuth access token for this profile, refreshing and persisting
    to the DB row first if it's expired or about to expire.

    Only meaningful for auth_type "oauth" profiles; returns None otherwise.
    """
    if profile.auth_type != "oauth":
        return None

    credentials = get_credentials(profile)
    if credentials["expires_at"] - time.time() > _EXPIRY_LEEWAY_SECONDS:
        return credentials["access_token"]

    if not credentials.get("refresh_token"):
        return None

    try:
        token_response = servicenow_oauth.refresh_access_token(
            profile.instance_url,
            credentials["client_id"],
            credentials["client_secret"],
            credentials["refresh_token"],
        )
    except servicenow_oauth.OAuthError:
        return None

    credentials["access_token"] = token_response["access_token"]
    credentials["refresh_token"] = token_response.get("refresh_token")
    credentials["expires_at"] = time.time() + float(token_response.get("expires_in", 0))
    profile.credentials_encrypted = encrypt_json(credentials, _secret())
    db.session.commit()
    return credentials["access_token"]
