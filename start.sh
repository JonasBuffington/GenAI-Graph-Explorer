#!/bin/bash
set -euo pipefail

REDIS_CONFIG_PATH="${REDIS_CONFIG_PATH:-/code/redis.conf}"
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_MAX_ATTEMPTS="${REDIS_MAX_ATTEMPTS:-20}"
REDIS_WAIT_SECONDS="${REDIS_WAIT_SECONDS:-0.5}"

if [[ -f "$REDIS_CONFIG_PATH" ]]; then
    echo "Starting Redis using config at $REDIS_CONFIG_PATH"
    redis-server "$REDIS_CONFIG_PATH"
else
    echo "Starting Redis with default configuration"
    redis-server --daemonize yes
fi

attempt=1
until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; do
    if (( attempt >= REDIS_MAX_ATTEMPTS )); then
        echo "Redis failed to become ready after $REDIS_MAX_ATTEMPTS attempts." >&2
        exit 1
    fi
    echo "Waiting for Redis to become ready ($attempt/$REDIS_MAX_ATTEMPTS)..."
    attempt=$((attempt + 1))
    sleep "$REDIS_WAIT_SECONDS"
done
echo "Redis is ready."

# Start the Uvicorn server in the foreground
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
