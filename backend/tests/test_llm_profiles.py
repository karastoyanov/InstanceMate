VALID_OPENAI_KEY = "sk-" + "a" * 20
VALID_ANTHROPIC_KEY = "sk-ant-" + "a" * 20
VALID_GOOGLE_KEY = "AIza" + "a" * 20

VALID_PAYLOAD = {
    "label": "Personal OpenAI",
    "provider": "openai",
    "api_key": VALID_OPENAI_KEY,
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
    response = client.get("/profiles/llm")
    assert response.status_code == 401


def test_create_profile_requires_login(client):
    response = client.post("/profiles/llm", json=VALID_PAYLOAD)
    assert response.status_code == 401


def test_delete_requires_login(client):
    response = client.delete("/profiles/llm/1")
    assert response.status_code == 401


def test_create_profile_success(client):
    _register(client)

    response = client.post("/profiles/llm", json=VALID_PAYLOAD)

    assert response.status_code == 200
    profile = response.get_json()["profile"]
    assert profile["label"] == "Personal OpenAI"
    assert profile["provider"] == "openai"
    assert "api_key" not in profile


def test_create_profile_rejects_missing_fields(client):
    _register(client)
    response = client.post("/profiles/llm", json={})
    assert response.status_code == 400


def test_create_profile_rejects_unsupported_provider(client):
    _register(client)
    response = client.post(
        "/profiles/llm", json={**VALID_PAYLOAD, "provider": "cohere"}
    )
    assert response.status_code == 400


def test_create_profile_rejects_short_key(client):
    _register(client)
    response = client.post(
        "/profiles/llm", json={**VALID_PAYLOAD, "api_key": "sk-tooshort"}
    )
    assert response.status_code == 400


def test_create_profile_rejects_mismatched_key_prefix(client):
    _register(client)
    response = client.post(
        "/profiles/llm", json={**VALID_PAYLOAD, "api_key": VALID_GOOGLE_KEY}
    )
    assert response.status_code == 400


def test_create_profile_accepts_anthropic_and_google(client):
    _register(client)
    for provider, key in (
        ("anthropic", VALID_ANTHROPIC_KEY),
        ("google", VALID_GOOGLE_KEY),
    ):
        response = client.post(
            "/profiles/llm",
            json={"label": provider, "provider": provider, "api_key": key},
        )
        assert response.status_code == 200
        assert response.get_json()["profile"]["provider"] == provider


def test_list_profiles_after_create(client):
    _register(client)
    client.post("/profiles/llm", json=VALID_PAYLOAD)

    response = client.get("/profiles/llm")
    profiles = response.get_json()["profiles"]
    assert len(profiles) == 1
    assert profiles[0]["label"] == "Personal OpenAI"


def test_delete_own_profile(client):
    _register(client)
    create_response = client.post("/profiles/llm", json=VALID_PAYLOAD)
    profile_id = create_response.get_json()["profile"]["id"]

    delete_response = client.delete(f"/profiles/llm/{profile_id}")
    assert delete_response.status_code == 200

    list_response = client.get("/profiles/llm")
    assert list_response.get_json()["profiles"] == []


def test_cannot_delete_another_users_profile(client):
    _register(client, email="owner@example.com", username="owner")
    create_response = client.post("/profiles/llm", json=VALID_PAYLOAD)
    profile_id = create_response.get_json()["profile"]["id"]

    client.post("/account/logout")
    _register(client, email="intruder@example.com", username="intruder")

    delete_response = client.delete(f"/profiles/llm/{profile_id}")
    assert delete_response.status_code == 404


def test_responses_never_contain_the_api_key(client):
    _register(client)
    create_response = client.post("/profiles/llm", json=VALID_PAYLOAD)
    assert VALID_OPENAI_KEY not in create_response.get_data(as_text=True)

    list_response = client.get("/profiles/llm")
    assert VALID_OPENAI_KEY not in list_response.get_data(as_text=True)
