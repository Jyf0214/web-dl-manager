#!/bin/bash
set -e

# Start the cron daemon in the background for scheduled tasks
if command -v cron &> /dev/null; then
    cron -f &
fi

# --- Static Site Cloning ---
STATIC_SITE_GIT_URL=${STATIC_SITE_GIT_URL:-"https://github.com/Jyf0214/upgraded-doodle.git"}
STATIC_SITE_GIT_BRANCH=${STATIC_SITE_GIT_BRANCH:-"gh-pages"}
STATIC_SITE_DIR="/app/static_site"

if [ -n "$STATIC_SITE_GIT_URL" ]; then
    # Remove existing directory to ensure a fresh clone
    rm -rf $STATIC_SITE_DIR
    git clone --quiet --depth 1 --branch "$STATIC_SITE_GIT_BRANCH" "$STATIC_SITE_GIT_URL" "$STATIC_SITE_DIR"
fi

# --- Cloudflare Tunnel ---
if [ -n "$TUNNEL_TOKEN" ]; then
    # 启动cloudflared，重定向所有输出到/dev/null以禁用日志
    cloudflared tunnel --no-autoupdate run --token "$TUNNEL_TOKEN" > /dev/null 2>&1 &
fi

# --- Start the main application ---
# The python script now handles both the camouflage and main app servers.
exec python3 -m app.main
