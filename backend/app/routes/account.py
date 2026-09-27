from flask import Blueprint, jsonify, request

from app.services import account_session, user_service
from app.services.user_service import AccountError

account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.post("/register")
def register():
    body = request.get_json(silent=True) or {}
    try:
        user = user_service.register_user(
            body.get("email") or "",
            body.get("username") or "",
            body.get("password") or "",
        )
    except (ValueError, AccountError) as exc:
        return jsonify(error=str(exc)), 400

    account_session.login_user(user.id)
    return jsonify(user=user.to_public_dict())


@account_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    try:
        user = user_service.authenticate(
            body.get("email") or "", body.get("password") or ""
        )
    except AccountError as exc:
        return jsonify(error=str(exc)), 401

    account_session.login_user(user.id)
    return jsonify(user=user.to_public_dict())


@account_bp.post("/logout")
def logout():
    account_session.logout_user()
    return jsonify(user=None)


@account_bp.get("/me")
def me():
    user_id = account_session.get_current_user_id()
    user = user_service.get_user(user_id) if user_id is not None else None

    if user_id is not None and user is None:
        # Stale session pointing at a since-deleted account.
        account_session.logout_user()

    return jsonify(user=user.to_public_dict() if user else None)
