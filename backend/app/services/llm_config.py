SUPPORTED_PROVIDERS = ("openai", "anthropic", "google")

# Heuristic prefixes to catch an obviously-wrong-provider paste (e.g. an
# OpenAI key while "Google" is selected). Not exhaustive - real validation
# happens on first actual use of the key.
_KEY_PREFIXES = {
    "openai": "sk-",
    "anthropic": "sk-ant-",
    "google": "AIza",
}

_MIN_KEY_LENGTH = 20


def validate_provider(raw_provider: str) -> str:
    provider = raw_provider.strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported provider. Choose one of: {', '.join(SUPPORTED_PROVIDERS)}"
        )
    return provider


def validate_api_key(provider: str, raw_api_key: str) -> str:
    api_key = raw_api_key.strip()
    if len(api_key) < _MIN_KEY_LENGTH:
        raise ValueError("That doesn't look like a valid API key")

    # Anthropic's "sk-ant-" prefix also satisfies OpenAI's "sk-" check, so
    # rule that out explicitly before the general prefix check below.
    if provider == "openai" and api_key.startswith("sk-ant-"):
        raise ValueError("That looks like an Anthropic key, not an OpenAI key")

    expected_prefix = _KEY_PREFIXES.get(provider)
    if expected_prefix and not api_key.startswith(expected_prefix):
        raise ValueError(
            f"That doesn't look like a {provider} key "
            f"(expected it to start with '{expected_prefix}')"
        )
    return api_key
