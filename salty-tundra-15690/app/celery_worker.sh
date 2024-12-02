#!/bin/bash

# Absolute path to the project directory
PROJECT_DIR="/Users/kokor/Downloads/FInal Project/analysis repo/salty-tundra-15690/app"

# Navigate to the project directory
cd "$PROJECT_DIR" || exit

# Activate the virtual environment
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
else
    echo "Error: Virtual environment not found at $PROJECT_DIR/venv/bin/activate"
    exit 1
fi

# Export PYTHONPATH to include the project directory
export PYTHONPATH="$PROJECT_DIR"

# Start Celery worker with the correct app path
celery -A config.celery_app worker --loglevel=info
