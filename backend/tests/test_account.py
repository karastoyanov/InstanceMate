VALID_PAYLOAD = {
    "email": "Jane@Example.com",
    "username": "jane_doe",
    "password": "correct-horse-battery",
}


def test_me_defaults_to_logged_out(client):
    response = client.get("/account/me")
    assert response.get_json() == {"user": None}


def test_register_success_logs_in_and_normalizes_email(client):
    response = client.post("/account/register", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.get_json()["user"]
    assert body["email"] == "jane@example.com"
    assert body["username"] == "jane_doe"
    assert "password" not in body
    assert "password_hash" not in body

    me_response = client.get("/account/me")
    assert me_response.get_json()["user"]["email"] == "jane@example.com"


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/account/register", json={**VALID_PAYLOAD, "email": "not-an-email"}
    )
    assert response.status_code == 400


def test_register_rejects_invalid_username(client):
    response = client.post("/account/register", json={**VALID_PAYLOAD, "username": "a"})
    assert response.status_code == 400


def test_register_rejects_short_password(client):
    response = client.post(
        "/account/register", json={**VALID_PAYLOAD, "password": "short"}
    )
    assert response.status_code == 400


def test_register_rejects_duplicate_email(client):
    client.post("/account/register", json=VALID_PAYLOAD)
    response = client.post(
        "/account/register", json={**VALID_PAYLOAD, "username": "someone_else"}
    )
    assert response.status_code == 400


def test_register_rejects_duplicate_username(client):
    client.post("/account/register", json=VALID_PAYLOAD)
    response = client.post(
        "/account/register", json={**VALID_PAYLOAD, "email": "other@example.com"}
    )
    assert response.status_code == 400


def test_login_success(client):
    client.post("/account/register", json=VALID_PAYLOAD)
    client.post("/account/logout")

    response = client.post(
        "/account/login",
        json={"email": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]},
    )
    assert response.status_code == 200
    assert response.get_json()["user"]["username"] == "jane_doe"


def test_login_wrong_password_and_unknown_email_give_same_message(client):
    client.post("/account/register", json=VALID_PAYLOAD)
    client.post("/account/logout")

    wrong_password = client.post(
        "/account/login",
        json={"email": VALID_PAYLOAD["email"], "password": "wrong-password"},
    )
    unknown_email = client.post(
        "/account/login",
        json={"email": "nobody@example.com", "password": VALID_PAYLOAD["password"]},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.get_json()["error"] == unknown_email.get_json()["error"]


def test_logout_clears_session(client):
    client.post("/account/register", json=VALID_PAYLOAD)
    client.post("/account/logout")

    response = client.get("/account/me")
    assert response.get_json() == {"user": None}


def test_responses_never_contain_the_password(client):
    register_response = client.post("/account/register", json=VALID_PAYLOAD)
    assert VALID_PAYLOAD["password"] not in register_response.get_data(as_text=True)

    client.post("/account/logout")
    login_response = client.post(
        "/account/login",
        json={"email": VALID_PAYLOAD["email"], "password": VALID_PAYLOAD["password"]},
    )
    assert VALID_PAYLOAD["password"] not in login_response.get_data(as_text=True)
