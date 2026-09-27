from urllib.parse import urlencode

import requests

REQUEST_TIMEOUT_SECONDS = 10


class OAuthError(Exception):
    """Raised when ServiceNow rejects an authorization/token request."""


def build_authorization_url(
    instance_url: str, client_id: str, redirect_uri: str, state: str
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
    }
    return f"{instance_url}/oauth_auth.do?{urlencode(params)}"


def exchange_code_for_token(
    instance_url: str,
    client_id: str,
    client_secret: str,
    code: str,
    redirect_uri: str,
) -> dict:
    return _request_token(
        instance_url,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )


def refresh_access_token(
    instance_url: str, client_id: str, client_secret: str, refresh_token: str
) -> dict:
    return _request_token(
        instance_url,
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )


def _request_token(instance_url: str, form_data: dict) -> dict:
    try:
        response = requests.post(
            f"{instance_url}/oauth_token.do",
            data=form_data,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise OAuthError("Could not reach the ServiceNow instance") from exc

    if response.status_code != 200:
        raise OAuthError("ServiceNow rejected the token request")

    return response.json()
