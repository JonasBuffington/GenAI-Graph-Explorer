# app/core/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings


def get_user_id_key(request) -> str:
    """
    Returns the user ID from the request header, falling back to the remote address.
    """
    user_id = request.headers.get("x-user-id")
    return user_id or get_remote_address(request)


storage_uri = settings.LIMITER_STORAGE_URI or settings.REDIS_URL

limiter = Limiter(
    key_func=get_user_id_key,
    storage_uri=storage_uri,
    strategy="fixed-window"
)
