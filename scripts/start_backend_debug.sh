#!/bin/bash

echo "=========================================="
echo "Starting QUOKKA Viz Backend (DEBUG MODE)"
echo "=========================================="
echo ""
echo "Debugging features enabled:"
echo "  ✓ Detailed request/response logging"
echo "  ✓ Path validation logging"
echo "  ✓ Log file: backend_debug.log"
echo ""
echo "Server information:"
echo "  Hostname: $(hostname)"
echo "  Current directory: $(pwd)"
echo ""
echo "Watch this terminal for detailed logs!"
echo "=========================================="
echo ""

cd backend

# Check if virtual environment exists
if [ ! -d "../venv" ]; then
    echo "⚠️  Virtual environment not found at ../venv"
    echo "   Please create it first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source ../venv/bin/activate

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "⚠️  uvicorn not found. Installing dependencies..."
    pip install -r ../requirements.txt
fi

# Start the server
echo "Starting uvicorn server..."
echo ""
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

