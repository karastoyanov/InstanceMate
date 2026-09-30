from unittest.mock import Mock, patch

import openai
import pytest
from app.extensions import db
from app.models.llm_profile import LlmProfile
from app.models.user import User
from app.services import llm_client, llm_profile_service
from app.services.llm_client import LlmError
from werkzeug.security import generate_password_hash


def _make_profile(provider: str, api_key: str) -> LlmProfile:
    # The `app` fixture already keeps one app context open for the whole
    # test, so this runs in it - no need to push another one here.
    user = User(
        email="jane@example.com",
        username="jane_doe",
        password_hash=generate_password_hash("correct-horse-battery"),
    )
    db.session.add(user)
    db.session.commit()

    return llm_profile_service.create_profile(
        user.id, "Test profile", provider, api_key
    )


@pytest.mark.parametrize(
    ("provider", "expected_model"),
    [
        ("openai", "gpt-4o-mini"),
        ("anthropic", "claude-3-5-sonnet-20241022"),
        ("google", "gemini/gemini-1.5-flash"),
    ],
)
def test_complete_maps_provider_to_expected_model(app, provider, expected_model):
    profile = _make_profile(provider, "the-api-key")
    messages = [{"role": "user", "content": "hi"}]

    fake_response = Mock()
    with patch(
        "app.services.llm_client.litellm.completion", return_value=fake_response
    ) as mock_completion:
        result = llm_client.complete(profile, messages)

    assert result is fake_response
    mock_completion.assert_called_once_with(
        model=expected_model,
        messages=messages,
        api_key="the-api-key",
        tools=None,
    )


def test_complete_passes_tools_through(app):
    profile = _make_profile("openai", "the-api-key")
    tools = [{"type": "function", "function": {"name": "ping"}}]

    with patch(
        "app.services.llm_client.litellm.completion", return_value=Mock()
    ) as mock_completion:
        llm_client.complete(profile, [{"role": "user", "content": "hi"}], tools=tools)

    assert mock_completion.call_args.kwargs["tools"] == tools


def test_complete_wraps_provider_errors_without_leaking_details(app):
    profile = _make_profile("openai", "the-api-key")

    with (
        patch(
            "app.services.llm_client.litellm.completion",
            side_effect=openai.OpenAIError("invalid api key: the-api-key"),
        ),
        pytest.raises(LlmError) as exc_info,
    ):
        llm_client.complete(profile, [{"role": "user", "content": "hi"}])

    assert "the-api-key" not in str(exc_info.value)
