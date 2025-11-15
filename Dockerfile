# Stage 1: Build kemono-dl in a separate environment
FROM python:3.11-slim as builder

# Install git for kemono-dl installation
RUN apt-get update && apt-get install -y --no-install-recommends git

# Install kemono-dl and its dependencies
RUN pip install --no-cache-dir git+https://github.com/AlphaSlayer1964/kemono-dl.git

# Stage 2: Final image
FROM python:3.11-slim

# 1. Install system dependencies including cron
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    unzip \
    ca-certificates \
    zstd \
    git \
    cron \
    && curl https://rclone.org/install.sh | bash \
    && wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
    && dpkg -i cloudflared-linux-amd64.deb \
    && rm cloudflared-linux-amd64.deb \
    && apt-get purge -y --auto-remove curl wget \
    && rm -rf /var/lib/apt/lists/*

# 2. Create a non-root user
RUN useradd -m -u 1000 user

# 3. Set up directories
WORKDIR /app
RUN mkdir -p /data/downloads /data/archives /data/status && chown -R 1000:1000 /app /data

# 4. Copy kemono-dl from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# 5. Copy ONLY the entrypoint script and requirements.txt for initial install
# The actual app code will be cloned by entrypoint.sh
COPY --chown=1000:1000 ./entrypoint.sh /entrypoint.sh
COPY --chown=1000:1000 ./app/requirements.txt /app/requirements.txt
RUN chmod +x /entrypoint.sh

# 6. Install Python dependencies (including uvicorn and pyinstaller for binary builds)
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir pyinstaller

# 7. Set up cron job
# Note: The updater.py will be downloaded by entrypoint.sh
RUN echo "0 3 * * * python3 /app/app/updater.py >> /data/status/cron_update.log 2>&1" > /etc/cron.d/updater_cron
RUN chmod 0644 /etc/cron.d/updater_cron
RUN crontab /etc/cron.d/updater_cron

# 8. Set PYTHONPATH
ENV PYTHONPATH /usr/local/lib/python3.11/site-packages

# 9. Switch to the non-root user
USER 1000

# 10. Expose port
EXPOSE 8000

# 11. Define volumes
VOLUME /data/downloads
VOLUME /data/archives
VOLUME /data/status

# 12. Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
