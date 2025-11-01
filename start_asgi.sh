#!/bin/bash

# ASGI Server Startup Script for ADHD Print Task Management
# This script starts the application using uvicorn ASGI server

set -e

# Configuration
HOST=${ASGI_HOST:-127.0.0.1}
PORT=${ASGI_PORT:-8000}
WORKERS=${ASGI_WORKERS:-1}
LOG_LEVEL=${ASGI_LOG_LEVEL:-info}
RELOAD=${ASGI_RELOAD:-false}

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$SCRIPT_DIR"

echo "Starting ADHD Print Task Management ASGI Server..."
echo "Configuration:"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Workers: $WORKERS"
echo "  Log Level: $LOG_LEVEL"
echo "  Auto-reload: $RELOAD"
echo "  Project Directory: $PROJECT_DIR"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --no-input

# Check for background jobs
echo "Starting background jobs system..."
python manage.py background_jobs status || true

# Start the ASGI server
echo "Starting ASGI server..."
if [ "$RELOAD" = "true" ]; then
    echo "Running in development mode with auto-reload..."
    python manage.py runasgi --host "$HOST" --port "$PORT" --reload --log-level "$LOG_LEVEL"
else
    echo "Running in production mode..."
    python manage.py runasgi --host "$HOST" --port "$PORT" --workers "$WORKERS" --log-level "$LOG_LEVEL"
fi