#!/bin/bash

echo "========================================"
echo "Backend Connection Test"
echo "========================================"
echo ""

# Test 1: Is backend running?
echo "Test 1: Checking if backend is running..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Backend is responding on port 8000"
    echo ""
    echo "Response:"
    curl -s http://localhost:8000/ | python3 -m json.tool
else
    echo "✗ Backend is NOT responding on port 8000"
    echo ""
    echo "Possible issues:"
    echo "  - Backend not started"
    echo "  - Wrong port"
    echo "  - SSH tunnel not working"
    exit 1
fi

echo ""
echo "========================================"

# Test 2: Server info
echo "Test 2: Getting server info..."
echo ""
curl -s http://localhost:8000/api/server_info | python3 -m json.tool

echo ""
echo "========================================"

# Test 3: Test path endpoint
echo "Test 3: Testing path endpoint with example path..."
echo ""
TEST_PATH="/tmp"
echo "Testing path: $TEST_PATH"
echo ""
curl -s "http://localhost:8000/api/test_path?path=${TEST_PATH}" | python3 -m json.tool

echo ""
echo "========================================"
echo "All tests complete!"
echo ""
echo "To test your own path:"
echo "  curl 'http://localhost:8000/api/test_path?path=/your/path/here'"
echo ""

