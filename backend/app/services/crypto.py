import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken


def _fernet(secret: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)


def encrypt_json(data: dict, secret: str) -> str:
    payload = json.dumps(data).encode()
    return _fernet(secret).encrypt(payload).decode()


def decrypt_json(token: str, secret: str) -> dict | None:
    try:
        payload = _fernet(secret).decrypt(token.encode())
    except (InvalidToken, ValueError):
        return None
    return json.loads(payload)
