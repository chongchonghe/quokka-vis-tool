#/Users/cche/git/vis-tool-3d/data/ParticleRadiation!/usr/bin/env bash
set -euo pipefail

source ~/rc/yt.rc

# Always run from the directory where this script lives
cd "$(dirname "$0")"

BACKEND_DIR="backend"
FRONTEND_DIR="frontend"

# Start backend (Uvicorn) in the background
cd "$BACKEND_DIR"
echo "Starting backend (uvicorn)..."
uvicorn main:app --reload --host 0.0.0.0 --port 9010 &
BACKEND_PID=$!

# Go back and start frontend in the foreground
cd "../$FRONTEND_DIR"
echo "Starting frontend (npm run dev)..."

# When you Ctrl-C npm, this trap will stop the backend too
cleanup() {
  echo ""
  echo "Shutting down dev servers..."
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup INT TERM EXIT

npm run dev