import time
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

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


def test_login_rejects_missing_fields(client):
    response = client.post("/auth/servicenow/login", json={})
    assert response.status_code == 400


def test_login_rejects_invalid_instance_url(client):
    response = client.post(
        "/auth/servicenow/login",
        json={**VALID_PAYLOAD, "instance_url": "https://evil.example.com"},
    )
    assert response.status_code == 400


def test_login_returns_authorization_url(client):
    response = client.post("/auth/servicenow/login", json=VALID_PAYLOAD)

    assert response.status_code == 200
    auth_url = response.get_json()["authorization_url"]
    parsed = urlparse(auth_url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "dev12345.service-now.com"
    assert parsed.path == "/oauth_auth.do"
    assert query["client_id"] == [VALID_PAYLOAD["client_id"]]
    assert query["response_type"] == ["code"]
    assert "state" in query


def test_callback_with_provider_error_redirects_with_reason(client):
    response = client.get("/auth/servicenow/callback?error=access_denied")

    assert response.status_code == 302
    assert "login=error" in response.location
    assert "reason=sn_denied" in response.location


def test_callback_without_pending_state_redirects_invalid_state(client):
    response = client.get("/auth/servicenow/callback?state=unknown&code=abc")

    assert response.status_code == 302
    assert "reason=invalid_state" in response.location


def test_full_login_flow_then_status_and_logout(client):
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
        callback_response = client.get(
            f"/auth/servicenow/callback?code=xyz&state={state}"
        )

    assert callback_response.status_code == 302
    assert "login=success" in callback_response.location

    status_response = client.get("/auth/servicenow/status")
    assert status_response.get_json() == {
        "connected": True,
        "instance_url": VALID_PAYLOAD["instance_url"],
        "auth_type": "oauth",
    }

    logout_response = client.post("/auth/servicenow/logout")
    assert logout_response.get_json() == {"connected": False}

    status_after_logout = client.get("/auth/servicenow/status")
    assert status_after_logout.get_json() == {"connected": False}


def test_callback_token_exchange_failure_redirects_with_reason(client):
    login_response = client.post("/auth/servicenow/login", json=VALID_PAYLOAD)
    state = parse_qs(urlparse(login_response.get_json()["authorization_url"]).query)[
        "state"
    ][0]

    with patch(
        "app.services.servicenow_oauth.requests.post",
        return_value=Mock(status_code=400, json=dict),
    ):
        response = client.get(f"/auth/servicenow/callback?code=xyz&state={state}")

    assert response.status_code == 302
    assert "reason=token_exchange_failed" in response.location


def test_status_refreshes_expired_token(app, client):
    with app.app_context():
        secret = app.config["SESSION_SECRET"]
        connection = {
            "auth_type": "oauth",
            "instance_url": VALID_PAYLOAD["instance_url"],
            "client_id": VALID_PAYLOAD["client_id"],
            "client_secret": VALID_PAYLOAD["client_secret"],
            "access_token": "expired-token",
            "refresh_token": "rt-1",
            "expires_at": time.time() - 10,
            "established_at": time.time(),
        }
        encrypted = encrypt_json(connection, secret)

    with client.session_transaction() as sess:
        sess["sn_oauth_connection"] = encrypted

    refreshed_token_response = Mock(
        status_code=200,
        json=lambda: {
            "access_token": "fresh-token",
            "refresh_token": "rt-2",
            "expires_in": 1800,
        },
    )
    with patch(
        "app.services.servicenow_oauth.requests.post",
        return_value=refreshed_token_response,
    ):
        response = client.get("/auth/servicenow/status")

    assert response.get_json() == {
        "connected": True,
        "instance_url": VALID_PAYLOAD["instance_url"],
        "auth_type": "oauth",
    }


def test_basic_login_rejects_missing_fields(client):
    response = client.post("/auth/servicenow/basic-login", json={})
    assert response.status_code == 400


def test_basic_login_rejects_invalid_instance_url(client):
    response = client.post(
        "/auth/servicenow/basic-login",
        json={**VALID_BASIC_PAYLOAD, "instance_url": "https://evil.example.com"},
    )
    assert response.status_code == 400


def test_basic_login_rejects_invalid_credentials(client):
    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=401),
    ):
        response = client.post("/auth/servicenow/basic-login", json=VALID_BASIC_PAYLOAD)

    assert response.status_code == 401
    assert "Invalid" in response.get_json()["error"]


def test_basic_login_success_then_status_and_logout(client):
    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        response = client.post("/auth/servicenow/basic-login", json=VALID_BASIC_PAYLOAD)

    assert response.status_code == 200
    assert response.get_json() == {
        "connected": True,
        "instance_url": VALID_BASIC_PAYLOAD["instance_url"],
        "auth_type": "basic",
    }

    status_response = client.get("/auth/servicenow/status")
    assert status_response.get_json() == {
        "connected": True,
        "instance_url": VALID_BASIC_PAYLOAD["instance_url"],
        "auth_type": "basic",
    }

    logout_response = client.post("/auth/servicenow/logout")
    assert logout_response.get_json() == {"connected": False}
