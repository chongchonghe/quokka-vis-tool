#!/bin/bash
# Status check for QUOKKA Viz Tool

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

LOG_DIR="$HOME/scripts/logs/quokka-vis-tool"

print_running() { echo -e "${GREEN}✓${NC} $1"; }
print_stopped() { echo -e "${RED}✗${NC} $1"; }

check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -ti :$port)
        print_running "$name running on port $port (PID: $PID)"
        return 0
    else
        print_stopped "$name not running on port $port"
        return 1
    fi
}

echo "QUOKKA Viz Tool Status"
echo "======================"
check_port 9010 "Backend"
check_port 5173 "Frontend"

echo ""
echo "Testing connectivity..."
if curl -s http://localhost:9010/api/server_info >/dev/null 2>&1; then
    print_running "Backend API responding"
else
    print_stopped "Backend API not responding"
fi

if curl -s http://localhost:5173/ >/dev/null 2>&1; then
    print_running "Frontend responding"
else
    print_stopped "Frontend not responding"
fi

if [ -d "$LOG_DIR" ]; then
    echo ""
    echo "Logs: $LOG_DIR"
fi
