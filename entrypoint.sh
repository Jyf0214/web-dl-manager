#!/bin/bash
set -e

# Start the cron daemon in the background
echo "Starting cron daemon..."
cron -f &

# --- App Repository Configuration ---
# Use environment variables, with sensible defaults for this project
APP_GIT_URL=${APP_GIT_URL:-"https://github.com/Jyf0214/gallery-dl-web.git"}
APP_GIT_BRANCH=${APP_GIT_BRANCH:-"main"}

# --- Static Site (Blog) Configuration ---
STATIC_SITE_GIT_URL=${STATIC_SITE_GIT_URL:-"https://github.com/Jyf0214/upgraded-doodle.git"}
STATIC_SITE_GIT_BRANCH=${STATIC_SITE_GIT_BRANCH:-"gh-pages"}
STATIC_SITE_DIR="/app/static_site"

# --- App Initialization ---
# Check if the app directory is empty or doesn't have a .git folder
if [ ! -d "/app/.git" ]; then
    echo "No git repository found. Cloning application..."
    # Clone the repository into a temporary directory
    git clone --depth 1 --branch "$APP_GIT_BRANCH" "$APP_GIT_URL" /tmp/app_source
    # Move the contents to the current directory (/app)
    mv /tmp/app_source/* /app/
    mv /tmp/app_source/.* /app/ || true # Move hidden files like .gitignore
    rm -rf /tmp/app_source
    echo "Application cloned successfully."
else
    echo "Existing git repository found. Skipping clone."
fi

# --- Static Site Cloning ---
if [ -n "$STATIC_SITE_GIT_URL" ]; then
    echo "Cloning static site from $STATIC_SITE_GIT_URL (branch: $STATIC_SITE_GIT_BRANCH)..."
    # Remove existing directory to ensure a fresh clone
    rm -rf $STATIC_SITE_DIR
    git clone --depth 1 --branch "$STATIC_SITE_GIT_BRANCH" "$STATIC_SITE_GIT_URL" "$STATIC_SITE_DIR"
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

# Function to build the binary
build_binary() {
    echo "Building binary application..."
    cd /app
    python build_new.py
    if [ $? -eq 0 ]; then
        echo "Binary built successfully!"
        return 0
    else
        echo "Binary build failed!"
        return 1
    fi
}

# --- Process Management ---
PID_FILE="/tmp/uvicorn.pid"

# Function to start binary version (build if necessary)
start_binary() {
    # Build binary if not already built
    if [ ! -f "/app/dist/gallery-dl-web/gallery-dl-web" ]; then
        echo "Binary not found, building now..."
        build_binary
    fi
    
    if [ -f "/app/dist/gallery-dl-web/gallery-dl-web" ]; then
        echo "Starting binary version of server..."
        # Pass Cloudflare token to the binary if available
        CLOUDFLARED_TOKEN="$CLOUDFLARED_TOKEN" /app/dist/gallery-dl-web/gallery-dl-web &
        echo $! > $PID_FILE
    else
        echo "Binary build failed, exiting..."
        exit 1
    fi
}

# Graceful shutdown and restart
handle_signal() {
    echo "Signal received, attempting graceful shutdown..."
    if [ -f "$PID_FILE" ]; then
        kill -TERM "$(cat $PID_FILE)" &> /dev/null || true
        rm -f "$PID_FILE"
    fi
    exit 0
}

# Trap signals
trap 'handle_signal' SIGTERM SIGHUP

# --- Main Loop (Watchdog) ---
# Always build and start the binary version
start_binary

while true; do
    sleep 60
    if [ -f "$PID_FILE" ]; then
        # Check if the process with the given PID is running
        if ! kill -0 "$(cat $PID_FILE)" &> /dev/null; then
            echo "Process seems to have died. Restarting..."
            start_binary
        fi
    else
        echo "PID file not found. Assuming process is dead. Restarting..."
        start_binary
    fi
done
