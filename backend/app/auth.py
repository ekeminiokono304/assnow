"""Tiny stateless admin auth: password -> HMAC-signed, expiring bearer token."""
import base64
import hashlib
import hmac
import time

from fastapi import Header, HTTPException

from .config import get_settings

TOKEN_TTL = 12 * 3600


def _sign(payload: str) -> str:
    return hmac.new(get_settings().secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()


def make_token() -> str:
    exp = str(int(time.time()) + TOKEN_TTL)
    return base64.urlsafe_b64encode(f"{exp}.{_sign(exp)}".encode()).decode()


def check_password(password: str) -> bool:
    return hmac.compare_digest(password.encode(), get_settings().admin_password.encode())


def require_admin(authorization: str = Header(default="")) -> None:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        exp, sig = base64.urlsafe_b64decode(token.encode()).decode().split(".", 1)
        if hmac.compare_digest(sig, _sign(exp)) and int(exp) > time.time():
            return
    except Exception:
        pass
    raise HTTPException(status_code=401, detail="Not authorised")


def require_cron(x_cron_secret: str = Header(default="")) -> None:
    if not hmac.compare_digest(x_cron_secret.encode(), get_settings().cron_secret.encode()):
        raise HTTPException(status_code=401, detail="Bad cron secret")
