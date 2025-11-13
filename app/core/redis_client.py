# app/core/redis_client.py
import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    _client: redis.Redis | None = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """Returns a shared Redis client instance."""
        if cls._client is None:
            cls._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return cls._client

    @classmethod
    async def close_client(cls):
        """Closes the shared Redis client instance."""
        if cls._client:
            await cls._client.close()
            cls._client = None

def get_redis_client() -> redis.Redis:
    """Dependency to get the Redis client."""
    return RedisClient.get_client()