# app/api/idempotency.py
import json
import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.routing import APIRoute
from starlette.responses import JSONResponse
from app.core.redis_client import get_redis_client
from app.core.config import settings

# Define which methods are considered for idempotency
IDEMPOTENT_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours
LOCK_TTL_SECONDS = 10 # Short lock to prevent race conditions
logger = logging.getLogger(__name__)

class IdempotentAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_handler = super().get_route_handler()

        async def idempotent_handler(request: Request) -> Response:
            # Bypass for non-idempotent methods
            if request.method not in IDEMPOTENT_METHODS:
                return await original_handler(request)

            user_id = request.headers.get("x-user-id")
            idempotency_key = request.headers.get("idempotency-key")

            if not user_id or not idempotency_key:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "X-User-ID and Idempotency-Key headers are required for this operation."}
                )

            redis = get_redis_client()
            cache_key = f"idempotency:{user_id}:{idempotency_key}"
            lock_key = f"{cache_key}:lock"

            # 1. Check for a cached response
            cached_response_data = await redis.get(cache_key)
            if cached_response_data:
                if settings.IDEMPOTENCY_DEBUG:
                    logger.info("Idempotency cache hit for %s", cache_key)
                cached = json.loads(cached_response_data)
                return Response(
                    content=cached["body"],
                    status_code=cached["status_code"],
                    headers=cached["headers"]
                )
            elif settings.IDEMPOTENCY_DEBUG:
                logger.info("Idempotency cache miss for %s", cache_key)

            # 2. Lock the key to prevent race conditions
            if not await redis.set(lock_key, "1", nx=True, ex=LOCK_TTL_SECONDS):
                if settings.IDEMPOTENCY_DEBUG:
                    logger.info("Idempotency lock contention for %s", cache_key)
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={"detail": "A request with this Idempotency-Key is already in progress."}
                )

            try:
                # 3. Execute the original request handler
                response: Response = await original_handler(request)

                # 4. Cache the response if it's a success or a client error worth caching
                if 200 <= response.status_code < 500:
                    # We need to read the body to cache it.
                    # A response body can only be read once, so we must then create a new response.
                    response_body = response.body
                    
                    response_data_to_cache = {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response_body.decode("utf-8")
                    }
                    await redis.set(cache_key, json.dumps(response_data_to_cache), ex=CACHE_TTL_SECONDS)
                    if settings.IDEMPOTENCY_DEBUG:
                        logger.info("Cached response for %s", cache_key)
                
                return response

            finally:
                # 5. Release the lock
                await redis.delete(lock_key)
                if settings.IDEMPOTENCY_DEBUG:
                    logger.info("Released idempotency lock for %s", cache_key)

        return idempotent_handler
