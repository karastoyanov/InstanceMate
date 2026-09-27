VALID_OPENAI_KEY = "sk-" + "a" * 20
VALID_ANTHROPIC_KEY = "sk-ant-" + "a" * 20
VALID_GOOGLE_KEY = "AIza" + "a" * 20


def test_get_provider_defaults_to_none(client):
    response = client.get("/llm/provider")
    assert response.get_json() == {"provider": None}


def test_set_provider_rejects_missing_fields(client):
    response = client.post("/llm/provider", json={})
    assert response.status_code == 400


def test_set_provider_rejects_unsupported_provider(client):
    response = client.post(
        "/llm/provider", json={"provider": "cohere", "api_key": VALID_OPENAI_KEY}
    )
    assert response.status_code == 400


def test_set_provider_rejects_short_key(client):
    response = client.post(
        "/llm/provider", json={"provider": "openai", "api_key": "sk-tooshort"}
    )
    assert response.status_code == 400


def test_set_provider_rejects_mismatched_key_prefix(client):
    response = client.post(
        "/llm/provider", json={"provider": "openai", "api_key": VALID_GOOGLE_KEY}
    )
    assert response.status_code == 400


def test_set_provider_rejects_anthropic_key_for_openai(client):
    # sk-ant-... also satisfies OpenAI's sk- prefix check, so this needs its
    # own explicit rejection - see llm_config.validate_api_key.
    response = client.post(
        "/llm/provider", json={"provider": "openai", "api_key": VALID_ANTHROPIC_KEY}
    )
    assert response.status_code == 400


def test_set_provider_success_then_get_then_clear(client):
    response = client.post(
        "/llm/provider", json={"provider": "openai", "api_key": VALID_OPENAI_KEY}
    )
    assert response.status_code == 200
    assert response.get_json() == {"provider": "openai"}

    status_response = client.get("/llm/provider")
    assert status_response.get_json() == {"provider": "openai"}

    clear_response = client.post("/llm/provider/clear")
    assert clear_response.get_json() == {"provider": None}

    status_after_clear = client.get("/llm/provider")
    assert status_after_clear.get_json() == {"provider": None}


def test_set_provider_accepts_anthropic_and_google_keys(client):
    for provider, key in (
        ("anthropic", VALID_ANTHROPIC_KEY),
        ("google", VALID_GOOGLE_KEY),
    ):
        response = client.post(
            "/llm/provider", json={"provider": provider, "api_key": key}
        )
        assert response.status_code == 200
        assert response.get_json() == {"provider": provider}


def test_set_provider_response_never_contains_the_api_key(client):
    response = client.post(
        "/llm/provider", json={"provider": "openai", "api_key": VALID_OPENAI_KEY}
    )
    assert VALID_OPENAI_KEY not in response.get_data(as_text=True)

    status_response = client.get("/llm/provider")
    assert VALID_OPENAI_KEY not in status_response.get_data(as_text=True)


def test_servicenow_logout_does_not_clear_llm_config(client):
    client.post(
        "/llm/provider", json={"provider": "openai", "api_key": VALID_OPENAI_KEY}
    )

    client.post("/auth/servicenow/logout")

    status_response = client.get("/llm/provider")
    assert status_response.get_json() == {"provider": "openai"}
