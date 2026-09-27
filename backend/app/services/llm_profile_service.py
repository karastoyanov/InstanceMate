from flask import current_app

from app.extensions import db
from app.models.llm_profile import LlmProfile
from app.services.crypto import encrypt_json


def _secret() -> str:
    return current_app.config["SESSION_SECRET"]


def list_profiles(user_id: int) -> list[LlmProfile]:
    return (
        LlmProfile.query.filter_by(user_id=user_id)
        .order_by(LlmProfile.created_at)
        .all()
    )


def get_profile(user_id: int, profile_id: int) -> LlmProfile | None:
    return LlmProfile.query.filter_by(id=profile_id, user_id=user_id).first()


def delete_profile(user_id: int, profile_id: int) -> bool:
    profile = get_profile(user_id, profile_id)
    if profile is None:
        return False
    db.session.delete(profile)
    db.session.commit()
    return True


def create_profile(user_id: int, label: str, provider: str, api_key: str) -> LlmProfile:
    profile = LlmProfile(
        user_id=user_id,
        label=label,
        provider=provider,
        credentials_encrypted=encrypt_json({"api_key": api_key}, _secret()),
    )
    db.session.add(profile)
    db.session.commit()
    return profile
