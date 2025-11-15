#!/bin/bash
set -e

# Start the cron daemon in the background for scheduled tasks
echo "Starting cron daemon..."
cron -f &

# --- Static Site Cloning ---
STATIC_SITE_GIT_URL=${STATIC_SITE_GIT_URL:-"https://github.com/Jyf0214/upgraded-doodle.git"}
STATIC_SITE_GIT_BRANCH=${STATIC_SITE_GIT_BRANCH:-"gh-pages"}
STATIC_SITE_DIR="/app/static_site"

if [ -n "$STATIC_SITE_GIT_URL" ]; then
    echo "Cloning static site from $STATIC_SITE_GIT_URL (branch: $STATIC_SITE_GIT_BRANCH)..."
    # Remove existing directory to ensure a fresh clone
    rm -rf $STATIC_SITE_DIR
    git clone --quiet --depth 1 --branch "$STATIC_SITE_GIT_BRANCH" "$STATIC_SITE_GIT_URL" "$STATIC_SITE_DIR"
    if [ $? -eq 0 ]; then
        echo "Static site cloning successful."
    else
        echo "Static site cloning failed. Creating an empty directory."
        mkdir -p $STATIC_SITE_DIR
    fi
else
    echo "STATIC_SITE_GIT_URL not set. Skipping clone."
    mkdir -p $STATIC_SITE_DIR
fi


# --- Process Management ---
PID_FILE="/tmp/gallery-dl-web.pid"

# Function to start the pre-built binary
start_binary() {
    echo "Starting server from pre-built binary..."
    # The binary is located at /app/gallery-dl-web, copied during docker build
    /app/web-dl-manager &
    echo $! > "$PID_FILE"
}

# Function for graceful shutdown
handle_signal() {
    echo "Signal received, attempting graceful shutdown..."
    if [ -f "$PID_FILE" ]; then
        kill -TERM "$(cat "$PID_FILE")" &> /dev/null || true
        rm -f "$PID_FILE"
    fi
    exit 0
}

# Trap signals for graceful shutdown
trap 'handle_signal' SIGTERM SIGHUP

# --- Main Loop (Watchdog) ---
# This loop ensures the application restarts if it crashes

start_binary

while true; do
    sleep 60
    if [ -f "$PID_FILE" ]; then
        # Check if the process is still running
        if ! kill -0 "$(cat "$PID_FILE")" &> /dev/null; then
            echo "Process seems to have died. Restarting..."
            start_binary
        fi
    else
        echo "PID file not found. Assuming process is dead. Restarting..."
        start_binary
    fi
done
