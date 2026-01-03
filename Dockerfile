# Stage 1: Build
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the Next.js application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Runtime
FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    unzip \
    ca-certificates \
    zstd \
    git \
    megatools \
    ffmpeg \
    python3 \
    python3-pip \
    python3-setuptools \
    && curl https://rclone.org/install.sh | bash \
    && rm -rf /var/lib/apt/lists/*

# Install python tools (gallery-dl, yt-dlp)
# Using --break-system-packages for modern debian/ubuntu or use a venv
RUN pip3 install --no-cache-dir gallery-dl yt-dlp --break-system-packages || \
    pip3 install --no-cache-dir gallery-dl yt-dlp

WORKDIR /app

# Create necessary data and logs directories
RUN mkdir -p /data/downloads /data/archives /data/status /app/logs

# Set environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=5492

# Copy built application from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/CHANGELOG.md ./CHANGELOG.md

# Setup permissions
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m appuser && \
    chown -R 1000:1000 /app /data

USER 1000

# Expose port
EXPOSE 5492

# Persist data
VOLUME /data/downloads
VOLUME /data/archives
VOLUME /data/status

# Start the application
CMD ["npm", "start"]
