#!/bin/bash
# Stop script for QUOKKA Viz Tool

GREEN='\033[0;32m'
NC='\033[0m'

LOG_DIR="$HOME/scripts/logs/quokka-vis-tool"
PID_FILE="$LOG_DIR/.pids"

print_info() { echo -e "${GREEN}[INFO]${NC} $1"; }

# Stop from PID file
if [ -f "$PID_FILE" ]; then
    print_info "Stopping services..."
    while read pid; do
        kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null || true
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi

# Kill any remaining processes on ports
for port in 9010 5173; do
    PIDS=$(lsof -ti :$port 2>/dev/null || true)
    if [ ! -z "$PIDS" ]; then
        print_info "Killing processes on port $port"
        echo $PIDS | xargs kill 2>/dev/null || true
    fi
done

print_info "All services stopped"
