import time
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from app import create_app
from app.services.crypto import encrypt_json

VALID_PAYLOAD = {
    "instance_url": "https://dev12345.service-now.com",
    "client_id": "abc123",
    "client_secret": "super-secret",
}

VALID_BASIC_PAYLOAD = {
    "instance_url": "https://dev12345.service-now.com",
    "username": "admin",
    "password": "super-secret",
}


def test_expired_session_is_treated_as_logged_out(app, client):
    with app.app_context():
        secret = app.config["SESSION_SECRET"]
        lifetime = app.config["SESSION_LIFETIME_SECONDS"]
        connection = {
            "auth_type": "basic",
            "instance_url": VALID_BASIC_PAYLOAD["instance_url"],
            "username": VALID_BASIC_PAYLOAD["username"],
            "password": VALID_BASIC_PAYLOAD["password"],
            "established_at": time.time() - lifetime - 1,
        }
        encrypted = encrypt_json(connection, secret)

    with client.session_transaction() as sess:
        sess["sn_oauth_connection"] = encrypted

    response = client.get("/auth/servicenow/status")
    assert response.get_json() == {"connected": False}

    # The expired connection should have been cleared, not just hidden.
    with client.session_transaction() as sess:
        assert "sn_oauth_connection" not in sess


def test_expired_pending_authorization_is_rejected(app, client):
    login_response = client.post("/auth/servicenow/login", json=VALID_PAYLOAD)
    state = parse_qs(urlparse(login_response.get_json()["authorization_url"]).query)[
        "state"
    ][0]

    with app.app_context(), client.session_transaction() as sess:
        secret = app.config["SESSION_SECRET"]
        lifetime = app.config["PENDING_AUTHORIZATION_LIFETIME_SECONDS"]
        pending = {
            "state": state,
            "instance_url": VALID_PAYLOAD["instance_url"],
            "client_id": VALID_PAYLOAD["client_id"],
            "client_secret": VALID_PAYLOAD["client_secret"],
            "redirect_uri": "http://localhost:5000/auth/servicenow/callback",
            "created_at": time.time() - lifetime - 1,
        }
        sess["sn_oauth_pending"] = encrypt_json(pending, secret)

    response = client.get(f"/auth/servicenow/callback?code=xyz&state={state}")

    assert response.status_code == 302
    assert "reason=invalid_state" in response.location


def test_logout_clears_pending_authorization_too(client):
    login_response = client.post("/auth/servicenow/login", json=VALID_PAYLOAD)
    state = parse_qs(urlparse(login_response.get_json()["authorization_url"]).query)[
        "state"
    ][0]

    client.post("/auth/servicenow/logout")

    response = client.get(f"/auth/servicenow/callback?code=xyz&state={state}")
    assert response.status_code == 302
    assert "reason=invalid_state" in response.location


def test_oauth_status_response_never_contains_secrets(client):
    login_response = client.post("/auth/servicenow/login", json=VALID_PAYLOAD)
    state = parse_qs(urlparse(login_response.get_json()["authorization_url"]).query)[
        "state"
    ][0]

    token_response = Mock(
        status_code=200,
        json=lambda: {
            "access_token": "at-1",
            "refresh_token": "rt-1",
            "expires_in": 1800,
        },
    )
    with patch(
        "app.services.servicenow_oauth.requests.post", return_value=token_response
    ):
        client.get(f"/auth/servicenow/callback?code=xyz&state={state}")

    response = client.get("/auth/servicenow/status")
    body_text = response.get_data(as_text=True)

    for secret_value in ("super-secret", "at-1", "rt-1"):
        assert secret_value not in body_text


def test_basic_login_response_never_contains_password(client):
    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        response = client.post("/auth/servicenow/basic-login", json=VALID_BASIC_PAYLOAD)

    assert VALID_BASIC_PAYLOAD["password"] not in response.get_data(as_text=True)

    status_response = client.get("/auth/servicenow/status")
    assert VALID_BASIC_PAYLOAD["password"] not in status_response.get_data(as_text=True)


def test_unhandled_exception_returns_generic_error_outside_debug():
    app = create_app("production")

    @app.route("/__boom")
    def boom():
        raise RuntimeError("a secret detail that must not leak")

    client = app.test_client()
    response = client.get("/__boom")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert "secret detail" not in response.get_data(as_text=True)


def test_unknown_route_still_returns_a_normal_404(client):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
