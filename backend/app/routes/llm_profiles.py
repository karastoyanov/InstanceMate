from flask import Blueprint, jsonify, request

from app.services import account_session, llm_config, llm_profile_service

profiles_bp = Blueprint("llm_profiles", __name__, url_prefix="/profiles/llm")


def _current_user_id() -> int | None:
    return account_session.get_current_user_id()


@profiles_bp.get("")
def list_profiles():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    profiles = llm_profile_service.list_profiles(user_id)
    return jsonify(profiles=[profile.to_public_dict() for profile in profiles])


@profiles_bp.post("")
def create_profile():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    body = request.get_json(silent=True) or {}
    label = (body.get("label") or "").strip()
    raw_provider = (body.get("provider") or "").strip()
    raw_api_key = body.get("api_key") or ""

    if not label or not raw_provider or not raw_api_key:
        return jsonify(error="label, provider, and api_key are required"), 400

    try:
        provider = llm_config.validate_provider(raw_provider)
        api_key = llm_config.validate_api_key(provider, raw_api_key)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    profile = llm_profile_service.create_profile(user_id, label, provider, api_key)
    return jsonify(profile=profile.to_public_dict())


@profiles_bp.delete("/<int:profile_id>")
def delete_profile(profile_id: int):
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    deleted = llm_profile_service.delete_profile(user_id, profile_id)
    if not deleted:
        return jsonify(error="Profile not found"), 404
    return jsonify(ok=True)
