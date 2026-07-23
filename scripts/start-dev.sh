#!/usr/bin/env bash
set -euo pipefail

echo "Starting local development environment..."
docker-compose up -d postgres redis qdrant
echo "Waiting for services..."
sleep 5
echo "Services started. Run: uvicorn backend.app.main:app --reload"
