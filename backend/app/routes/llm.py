from flask import Blueprint, jsonify, request

from app.services import llm_config, llm_session_store

llm_bp = Blueprint("llm", __name__, url_prefix="/llm")


@llm_bp.post("/provider")
def set_provider():
    body = request.get_json(silent=True) or {}
    raw_provider = (body.get("provider") or "").strip()
    raw_api_key = body.get("api_key") or ""

    if not raw_provider or not raw_api_key:
        return jsonify(error="provider and api_key are required"), 400

    try:
        provider = llm_config.validate_provider(raw_provider)
        api_key = llm_config.validate_api_key(provider, raw_api_key)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    llm_session_store.store_llm_config(provider, api_key)
    return jsonify(provider=provider)


@llm_bp.get("/provider")
def get_provider():
    config = llm_session_store.get_llm_config()
    return jsonify(provider=config["provider"] if config else None)


@llm_bp.post("/provider/clear")
def clear_provider():
    llm_session_store.clear_llm_config()
    return jsonify(provider=None)
