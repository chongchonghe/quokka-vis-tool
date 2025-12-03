#!/bin/bash
# Development mode - runs with live log output

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_PORT=9010
VENV_PATH="$HOME/softwares-setonix/python-envs/uv-quokka-vis-tool"

# Find script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

cleanup() {
    print_info "Shutting down..."
    jobs -p | xargs -r kill 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Activate Python venv
print_info "Activating Python virtual environment..."
source "$VENV_PATH/bin/activate"

print_info "Starting backend on port $BACKEND_PORT..."
cd "$BACKEND_DIR"
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload 2>&1 | sed "s/^/[${BLUE}BACKEND${NC}] /" &

sleep 2

print_info "Starting frontend..."
cd "$FRONTEND_DIR"
npm run dev 2>&1 | sed "s/^/[${YELLOW}FRONTEND${NC}] /" &

print_info "=================================="
print_info "Development mode - Live logs"
print_info "Press Ctrl+C to stop"
print_info "=================================="

wait
