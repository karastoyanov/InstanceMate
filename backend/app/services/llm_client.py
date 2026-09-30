"""Thin wrapper around LiteLLM so call sites don't branch on provider.

Takes an LlmProfile (#41 - provider + encrypted api_key) instead of a raw
provider/key pair, so callers never handle the decrypted key directly.
"""

import litellm
import openai

from app.models.llm_profile import LlmProfile
from app.services import llm_profile_service


class LlmError(Exception):
    """Raised when the provider rejects or fails a completion request."""


# No per-user model selection yet - one sensible default per provider.
_DEFAULT_MODEL = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "google": "gemini/gemini-1.5-flash",
}


def complete(
    profile: LlmProfile, messages: list[dict], tools: list[dict] | None = None
) -> litellm.ModelResponse:
    """Run a chat completion using the given profile's provider/key.

    Raises LlmError (never the raw provider exception, which could include
    the API key or other request details) if the call fails.
    """
    api_key = llm_profile_service.get_api_key(profile)
    model = _DEFAULT_MODEL[profile.provider]

    try:
        return litellm.completion(
            model=model,
            messages=messages,
            api_key=api_key,
            tools=tools,
        )
    except openai.OpenAIError as exc:
        # LiteLLM normalizes every provider's errors into this (OpenAI SDK)
        # exception hierarchy, so this one except clause covers all three
        # providers - confirmed by checking the actual class hierarchy
        # rather than assuming.
        raise LlmError(
            "The AI provider rejected the request. Check your API key and try again."
        ) from exc
