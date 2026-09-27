import secrets

from flask import Blueprint, current_app, jsonify, redirect, request

from app.services import (
    account_session,
    instance_url,
    servicenow_basic_auth,
    servicenow_oauth,
    servicenow_profile_service,
    session_store,
)

profiles_bp = Blueprint(
    "servicenow_profiles", __name__, url_prefix="/profiles/servicenow"
)


def _current_user_id() -> int | None:
    return account_session.get_current_user_id()


def _redirect_uri() -> str:
    return f"{current_app.config['APP_BASE_URL']}/profiles/servicenow/oauth/callback"


def _frontend_redirect(login: str, reason: str | None = None) -> str:
    url = f"{current_app.config['FRONTEND_URL']}/?login={login}"
    if reason:
        url += f"&reason={reason}"
    return url


@profiles_bp.get("")
def list_profiles():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    profiles = servicenow_profile_service.list_profiles(user_id)
    return jsonify(profiles=[profile.to_public_dict() for profile in profiles])


@profiles_bp.delete("/<int:profile_id>")
def delete_profile(profile_id: int):
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    deleted = servicenow_profile_service.delete_profile(user_id, profile_id)
    if not deleted:
        return jsonify(error="Profile not found"), 404
    return jsonify(ok=True)


@profiles_bp.post("/oauth/start")
def start_oauth():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    body = request.get_json(silent=True) or {}
    label = (body.get("label") or "").strip()
    client_id = (body.get("client_id") or "").strip()
    client_secret = (body.get("client_secret") or "").strip()
    raw_instance_url = (body.get("instance_url") or "").strip()

    if not label or not client_id or not client_secret or not raw_instance_url:
        return jsonify(
            error="label, instance_url, client_id, and client_secret are required"
        ), 400

    try:
        normalized_url = instance_url.normalize_instance_url(raw_instance_url)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    state = secrets.token_urlsafe(32)
    redirect_uri = _redirect_uri()
    session_store.store_pending_authorization(
        state, label, normalized_url, client_id, client_secret, redirect_uri
    )

    authorization_url = servicenow_oauth.build_authorization_url(
        normalized_url, client_id, redirect_uri, state
    )
    return jsonify(authorization_url=authorization_url)


@profiles_bp.get("/oauth/callback")
def oauth_callback():
    if request.args.get("error"):
        return redirect(_frontend_redirect("error", "sn_denied"))

    state = request.args.get("state", "")
    code = request.args.get("code")

    pending = session_store.pop_pending_authorization(state)
    if pending is None:
        return redirect(_frontend_redirect("error", "invalid_state"))
    if not code:
        return redirect(_frontend_redirect("error", "missing_code"))

    user_id = _current_user_id()
    if user_id is None:
        return redirect(_frontend_redirect("error", "not_logged_in"))

    try:
        token_response = servicenow_oauth.exchange_code_for_token(
            pending["instance_url"],
            pending["client_id"],
            pending["client_secret"],
            code,
            pending["redirect_uri"],
        )
    except servicenow_oauth.OAuthError:
        return redirect(_frontend_redirect("error", "token_exchange_failed"))

    servicenow_profile_service.create_oauth_profile(
        user_id,
        pending["label"],
        pending["instance_url"],
        pending["client_id"],
        pending["client_secret"],
        token_response,
    )
    return redirect(_frontend_redirect("success"))


@profiles_bp.post("/basic")
def create_basic():
    user_id = _current_user_id()
    if user_id is None:
        return jsonify(error="Not logged in"), 401

    body = request.get_json(silent=True) or {}
    label = (body.get("label") or "").strip()
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    raw_instance_url = (body.get("instance_url") or "").strip()

    if not label or not username or not password or not raw_instance_url:
        return jsonify(
            error="label, instance_url, username, and password are required"
        ), 400

    try:
        normalized_url = instance_url.normalize_instance_url(raw_instance_url)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    try:
        servicenow_basic_auth.verify_credentials(normalized_url, username, password)
    except servicenow_basic_auth.BasicAuthError as exc:
        return jsonify(error=str(exc)), 401

    profile = servicenow_profile_service.create_basic_profile(
        user_id, label, normalized_url, username, password
    )
    return jsonify(profile=profile.to_public_dict())
