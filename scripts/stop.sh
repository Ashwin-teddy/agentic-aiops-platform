#!/usr/bin/env bash
set -euo pipefail

echo "Stopping all services..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null
echo "All services stopped."
