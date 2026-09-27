import re

_INSTANCE_URL_RE = re.compile(
    r"^https://[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.service-now\.com$"
)


def normalize_instance_url(raw_url: str) -> str:
    """Validate and normalize a user-supplied ServiceNow instance URL.

    Restricted to https://<instance>.service-now.com to prevent SSRF via an
    attacker-controlled host being used as the target of server-side
    requests (OAuth token exchange/refresh, basic auth verification).
    """
    url = raw_url.strip().rstrip("/")
    if not _INSTANCE_URL_RE.match(url):
        raise ValueError(
            "Instance URL must look like https://your-instance.service-now.com"
        )
    return url
