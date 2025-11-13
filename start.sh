#!/bin/bash

# Start the Redis server in the background
redis-server --daemonize yes

# Give Redis a moment to initialize before starting the web server
sleep 1

# Start the Uvicorn server in the foreground
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}