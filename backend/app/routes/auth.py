import secrets

from flask import Blueprint, current_app, jsonify, redirect, request

from app.services import servicenow_oauth, session_store

auth_bp = Blueprint("auth", __name__, url_prefix="/auth/servicenow")


def _redirect_uri() -> str:
    return f"{current_app.config['APP_BASE_URL']}/auth/servicenow/callback"


def _frontend_redirect(login: str, reason: str | None = None) -> str:
    url = f"{current_app.config['FRONTEND_URL']}/?login={login}"
    if reason:
        url += f"&reason={reason}"
    return url


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    client_id = (body.get("client_id") or "").strip()
    client_secret = (body.get("client_secret") or "").strip()
    raw_instance_url = (body.get("instance_url") or "").strip()

    if not client_id or not client_secret or not raw_instance_url:
        return jsonify(
            error="instance_url, client_id, and client_secret are required"
        ), 400

    try:
        instance_url = servicenow_oauth.normalize_instance_url(raw_instance_url)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    state = secrets.token_urlsafe(32)
    redirect_uri = _redirect_uri()
    session_store.store_pending_authorization(
        state, instance_url, client_id, client_secret, redirect_uri
    )

    authorization_url = servicenow_oauth.build_authorization_url(
        instance_url, client_id, redirect_uri, state
    )
    return jsonify(authorization_url=authorization_url)


@auth_bp.get("/callback")
def callback():
    if request.args.get("error"):
        return redirect(_frontend_redirect("error", "sn_denied"))

    state = request.args.get("state", "")
    code = request.args.get("code")

    pending = session_store.pop_pending_authorization(state)
    if pending is None:
        return redirect(_frontend_redirect("error", "invalid_state"))
    if not code:
        return redirect(_frontend_redirect("error", "missing_code"))

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

    session_store.store_connection(
        pending["instance_url"],
        pending["client_id"],
        pending["client_secret"],
        token_response,
    )
    return redirect(_frontend_redirect("success"))


@auth_bp.get("/status")
def status():
    access_token = session_store.get_valid_access_token()
    if access_token is None:
        return jsonify(connected=False)

    connection = session_store.get_connection()
    return jsonify(connected=True, instance_url=connection["instance_url"])


@auth_bp.post("/logout")
def logout():
    session_store.clear_connection()
    return jsonify(connected=False)
