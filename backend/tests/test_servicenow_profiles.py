import time
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

from app.extensions import db
from app.services import servicenow_profile_service
from app.services.crypto import decrypt_json

OAUTH_PAYLOAD = {
    "label": "Acme Prod",
    "instance_url": "https://dev12345.service-now.com",
    "client_id": "abc123",
    "client_secret": "super-secret",
}

BASIC_PAYLOAD = {
    "label": "Acme Dev",
    "instance_url": "https://dev12345.service-now.com",
    "username": "admin",
    "password": "super-secret",
}


def _register(client, email="jane@example.com", username="jane_doe"):
    client.post(
        "/account/register",
        json={
            "email": email,
            "username": username,
            "password": "correct-horse-battery",
        },
    )


def test_list_profiles_requires_login(client):
    response = client.get("/profiles/servicenow")
    assert response.status_code == 401


def test_create_basic_requires_login(client):
    response = client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)
    assert response.status_code == 401


def test_start_oauth_requires_login(client):
    response = client.post("/profiles/servicenow/oauth/start", json=OAUTH_PAYLOAD)
    assert response.status_code == 401


def test_delete_requires_login(client):
    response = client.delete("/profiles/servicenow/1")
    assert response.status_code == 401


def test_create_basic_profile_success(client):
    _register(client)

    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        response = client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)

    assert response.status_code == 200
    profile = response.get_json()["profile"]
    assert profile["label"] == "Acme Dev"
    assert profile["auth_type"] == "basic"
    assert "password" not in profile


def test_create_basic_profile_rejects_invalid_credentials(client):
    _register(client)

    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=401),
    ):
        response = client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)

    assert response.status_code == 401


def test_create_basic_profile_rejects_invalid_instance_url(client):
    _register(client)

    response = client.post(
        "/profiles/servicenow/basic",
        json={**BASIC_PAYLOAD, "instance_url": "https://evil.example.com"},
    )
    assert response.status_code == 400


def test_create_basic_profile_rejects_missing_fields(client):
    _register(client)

    response = client.post("/profiles/servicenow/basic", json={})
    assert response.status_code == 400


def test_list_profiles_after_create(client):
    _register(client)

    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)

    response = client.get("/profiles/servicenow")
    profiles = response.get_json()["profiles"]
    assert len(profiles) == 1
    assert profiles[0]["label"] == "Acme Dev"


def test_delete_own_profile(client):
    _register(client)

    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        create_response = client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)
    profile_id = create_response.get_json()["profile"]["id"]

    delete_response = client.delete(f"/profiles/servicenow/{profile_id}")
    assert delete_response.status_code == 200

    list_response = client.get("/profiles/servicenow")
    assert list_response.get_json()["profiles"] == []


def test_cannot_delete_another_users_profile(client):
    _register(client, email="owner@example.com", username="owner")
    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        create_response = client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)
    profile_id = create_response.get_json()["profile"]["id"]

    client.post("/account/logout")
    _register(client, email="intruder@example.com", username="intruder")

    delete_response = client.delete(f"/profiles/servicenow/{profile_id}")
    assert delete_response.status_code == 404


def test_start_oauth_returns_authorization_url(client):
    _register(client)

    response = client.post("/profiles/servicenow/oauth/start", json=OAUTH_PAYLOAD)

    assert response.status_code == 200
    auth_url = response.get_json()["authorization_url"]
    parsed = urlparse(auth_url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "dev12345.service-now.com"
    assert parsed.path == "/oauth_auth.do"
    assert query["client_id"] == [OAUTH_PAYLOAD["client_id"]]
    assert "state" in query


def test_start_oauth_rejects_invalid_instance_url(client):
    _register(client)

    response = client.post(
        "/profiles/servicenow/oauth/start",
        json={**OAUTH_PAYLOAD, "instance_url": "https://evil.example.com"},
    )
    assert response.status_code == 400


def test_oauth_callback_with_provider_error_redirects_with_reason(client):
    response = client.get("/profiles/servicenow/oauth/callback?error=access_denied")
    assert response.status_code == 302
    assert "reason=sn_denied" in response.location


def test_oauth_callback_without_pending_state_redirects_invalid_state(client):
    response = client.get("/profiles/servicenow/oauth/callback?state=unknown&code=abc")
    assert response.status_code == 302
    assert "reason=invalid_state" in response.location


def test_oauth_callback_full_flow_creates_profile(client):
    _register(client)
    start_response = client.post("/profiles/servicenow/oauth/start", json=OAUTH_PAYLOAD)
    state = parse_qs(urlparse(start_response.get_json()["authorization_url"]).query)[
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
            f"/profiles/servicenow/oauth/callback?code=xyz&state={state}"
        )

    assert callback_response.status_code == 302
    assert "login=success" in callback_response.location

    profiles = client.get("/profiles/servicenow").get_json()["profiles"]
    assert len(profiles) == 1
    assert profiles[0]["label"] == "Acme Prod"
    assert profiles[0]["auth_type"] == "oauth"


def test_oauth_callback_token_exchange_failure_redirects_with_reason(client):
    _register(client)
    start_response = client.post("/profiles/servicenow/oauth/start", json=OAUTH_PAYLOAD)
    state = parse_qs(urlparse(start_response.get_json()["authorization_url"]).query)[
        "state"
    ][0]

    with patch(
        "app.services.servicenow_oauth.requests.post",
        return_value=Mock(status_code=400, json=dict),
    ):
        response = client.get(
            f"/profiles/servicenow/oauth/callback?code=xyz&state={state}"
        )

    assert response.status_code == 302
    assert "reason=token_exchange_failed" in response.location


def test_responses_never_contain_secrets(client):
    _register(client)

    with patch(
        "app.services.servicenow_basic_auth.requests.get",
        return_value=Mock(status_code=200),
    ):
        create_response = client.post("/profiles/servicenow/basic", json=BASIC_PAYLOAD)
    list_response = client.get("/profiles/servicenow")

    for response in (create_response, list_response):
        body_text = response.get_data(as_text=True)
        assert BASIC_PAYLOAD["password"] not in body_text

    oauth_start_response = client.post(
        "/profiles/servicenow/oauth/start", json=OAUTH_PAYLOAD
    )
    assert OAUTH_PAYLOAD["client_secret"] not in oauth_start_response.get_data(
        as_text=True
    )


def test_get_valid_access_token_refreshes_when_near_expiry(app):
    with app.app_context():
        from app.models.servicenow_profile import ServiceNowProfile
        from app.models.user import User
        from app.services.crypto import encrypt_json
        from werkzeug.security import generate_password_hash

        user = User(
            email="jane@example.com",
            username="jane_doe",
            password_hash=generate_password_hash("correct-horse-battery"),
        )
        db.session.add(user)
        db.session.commit()

        secret = app.config["SESSION_SECRET"]
        credentials = {
            "client_id": OAUTH_PAYLOAD["client_id"],
            "client_secret": OAUTH_PAYLOAD["client_secret"],
            "access_token": "expired-token",
            "refresh_token": "rt-1",
            "expires_at": time.time() - 10,
        }
        profile = ServiceNowProfile(
            user_id=user.id,
            label="Acme Prod",
            instance_url=OAUTH_PAYLOAD["instance_url"],
            auth_type="oauth",
            credentials_encrypted=encrypt_json(credentials, secret),
        )
        db.session.add(profile)
        db.session.commit()

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
            access_token = servicenow_profile_service.get_valid_access_token(profile)

        assert access_token == "fresh-token"
        stored = decrypt_json(profile.credentials_encrypted, secret)
        assert stored["access_token"] == "fresh-token"
        assert stored["refresh_token"] == "rt-2"
