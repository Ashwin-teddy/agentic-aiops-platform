#!/usr/bin/env bash
set -euo pipefail

echo "Starting ALL services with Docker Compose..."
docker compose up --build
# fallback
# docker-compose up --build
