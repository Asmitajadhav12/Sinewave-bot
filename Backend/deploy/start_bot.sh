#!/bin/bash

# Usage: ./start_bot.sh [prod|dev]

ENV=$1

if [ -z "$ENV" ]; then
    echo "Usage: ./start_bot.sh [prod|dev]"
    exit 1
fi

# Go to project root (parent directory of this script)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."

if [ "$ENV" == "prod" ]; then
    SESSION_NAME="prod_sinewave_bot"
    PORT=8000
    echo "Starting PRODUCTION bot on port $PORT..."
elif [ "$ENV" == "dev" ]; then
    SESSION_NAME="dev_sinewave_bot"
    PORT=8001
    echo "Starting DEVELOPMENT bot on port $PORT..."
else
    echo "Invalid environment. Use 'prod' or 'dev'."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create it first."
    exit 1
fi

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: 'venv' directory not found. Please run 'python3 -m venv venv' and install requirements."
    exit 1
fi

# Start tmux session
# We use '|| true' to ignore error if session already exists, but we should probably check.
tmux has-session -t $SESSION_NAME 2>/dev/null

if [ $? != 0 ]; then
    # tmux new-session -d -s $SESSION_NAME "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    pm2 start python3 --name $SESSION_NAME -- \
    -m uvicorn app.main:app --host 0.0.0.0 --port $PORT

    echo "Bot started '$SESSION_NAME'."
else
    echo "Session '$SESSION_NAME' already exists. Attach using: tmux attach -t $SESSION_NAME"
fi
