#!/bin/bash
# Simple startup script for QUOKKA Viz Tool

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BACKEND_PORT=9010
VENV_PATH="$HOME/softwares-setonix/python-envs/uv-quokka-vis-tool"
LOG_DIR="$HOME/scripts/logs/quokka-vis-tool"

# Find script directory (works even when called from elsewhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
PID_FILE="$LOG_DIR/.pids"

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Create log directory
mkdir -p "$LOG_DIR"

# Cleanup function
cleanup() {
    print_info "Shutting down services..."
    if [ -f "$PID_FILE" ]; then
        while read pid; do
            kill $pid 2>/dev/null || true
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Activate Python virtual environment
print_info "Activating Python virtual environment..."
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
else
    print_error "Virtual environment not found at: $VENV_PATH"
    exit 1
fi

# Check npm is available (should be loaded from .bashrc)
if ! command -v npm &> /dev/null; then
    print_error "npm not found. Make sure nvm is loaded in your .bashrc"
    exit 1
fi

# Start backend
print_info "Starting backend on port $BACKEND_PORT..."
cd "$BACKEND_DIR"
uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID >> "$PID_FILE"
print_info "Backend started (PID: $BACKEND_PID)"

sleep 2

# Check backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    print_error "Backend failed to start. Check: $LOG_DIR/backend.log"
    exit 1
fi

# Start frontend
print_info "Starting frontend..."
cd "$FRONTEND_DIR"
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID >> "$PID_FILE"
print_info "Frontend started (PID: $FRONTEND_PID)"

sleep 3

# Check frontend is running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    print_error "Frontend failed to start. Check: $LOG_DIR/frontend.log"
    exit 1
fi

print_info "=================================="
print_info "QUOKKA Viz Tool is running!"
print_info "=================================="
print_info "Backend:  http://localhost:$BACKEND_PORT"
print_info "Frontend: http://localhost:5173"
print_info ""
print_info "Logs: $LOG_DIR"
print_info "  Backend:  $LOG_DIR/backend.log"
print_info "  Frontend: $LOG_DIR/frontend.log"
print_info ""
print_info "Press Ctrl+C to stop all services"
print_info "=================================="

# Tail logs
tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" 2>/dev/null &
TAIL_PID=$!
echo $TAIL_PID >> "$PID_FILE"

wait $BACKEND_PID $FRONTEND_PID
