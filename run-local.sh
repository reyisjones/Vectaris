#!/usr/bin/env bash
# Run Vectaris locally without Docker.
# Starts the FastAPI backend (port 8000) and the Vite frontend (port 5173).
# Press Ctrl+C to stop both.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

command -v python3 >/dev/null 2>&1 || { echo "python3 not found. Install Python 3.10+."; exit 1; }
command -v npm     >/dev/null 2>&1 || { echo "npm not found. Install Node.js 20+ (e.g. 'brew install node')."; exit 1; }

# ---------- backend ----------
cd "$BACKEND_DIR"
if [ ! -d ".venv" ]; then
  echo "==> Creating Python virtual environment"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "==> Installing backend dependencies"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt -r requirements-dev.txt
[ -f ".env" ] || cp .env.example .env

echo "==> Starting backend on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cleanup() {
  echo ""
  echo "==> Shutting down"
  kill "$BACKEND_PID"      2>/dev/null || true
  kill "$FRONTEND_PID"     2>/dev/null || true
  wait                     2>/dev/null || true
}
trap cleanup INT TERM EXIT

# ---------- frontend ----------
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
  echo "==> Installing frontend dependencies"
  npm install --no-audit --no-fund
fi

echo "==> Starting frontend on http://localhost:5173"
npm run dev -- --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!

echo ""
echo "Backend : http://localhost:8000  (docs: /docs, metrics: /metrics)"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop."
wait
