import requests

REQUEST_TIMEOUT_SECONDS = 10


class BasicAuthError(Exception):
    """Raised when ServiceNow rejects basic auth credentials."""


def verify_credentials(instance_url: str, username: str, password: str) -> None:
    """Check username/password against the instance with a lightweight
    authenticated request. Raises BasicAuthError if they don't work."""
    try:
        response = requests.get(
            f"{instance_url}/api/now/table/sys_user",
            params={"sysparm_limit": 1},
            auth=(username, password),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise BasicAuthError("Could not reach the ServiceNow instance") from exc

    if response.status_code == 401:
        raise BasicAuthError("Invalid username or password")
    if response.status_code != 200:
        raise BasicAuthError("ServiceNow rejected the request")
