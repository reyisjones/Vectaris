#!/usr/bin/env bash
# Run Vectaris with Docker Compose (backend on :8000, frontend on :3000).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Install Docker Desktop first."
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose plugin not found. Install Docker Desktop or compose v2."
  exit 1
fi

[ -f "backend/.env" ] || cp backend/.env.example backend/.env

echo "==> Building and starting containers"
docker compose up --build "$@"
