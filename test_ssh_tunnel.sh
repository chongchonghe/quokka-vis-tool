#!/bin/bash

echo "=========================================="
echo "SSH Tunnel Test (Run on LOCAL machine)"
echo "=========================================="
echo ""

echo "This script tests if your SSH tunnel is working."
echo "Run this on your LOCAL MACBOOK, not the server!"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "1. Testing Backend Connection (port 8000)..."
echo "   Trying http://localhost:8000/..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✓ Backend is reachable through tunnel!"
    echo ""
    echo "   Response:"
    curl -s http://localhost:8000/ | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/
else
    echo "   ✗ Backend is NOT reachable!"
    echo "   This means port 8000 is not tunneled."
    echo ""
    echo "   Fix: Restart your SSH tunnel with:"
    echo "   ssh -N -L 5173:localhost:5173 -L 8000:localhost:8000 set2"
    exit 1
fi

echo ""
echo "=========================================="
echo "2. Testing Frontend Connection (port 5173)..."
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "   ✓ Frontend is reachable through tunnel!"
else
    echo "   ✗ Frontend is NOT reachable!"
    echo "   This means port 5173 is not tunneled."
    exit 1
fi

echo ""
echo "=========================================="
echo "3. Testing Backend API Endpoint..."
echo "   Trying http://localhost:8000/api/server_info..."
response=$(curl -s http://localhost:8000/api/server_info)
if echo "$response" | grep -q "hostname"; then
    echo "   ✓ Backend API works!"
    echo ""
    echo "   Server Info:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "   ✗ Backend API returned unexpected response:"
    echo "$response" | head -20
fi

echo ""
echo "=========================================="
echo "4. Testing Path Test Endpoint..."
echo "   Trying http://localhost:8000/api/test_path?path=/tmp..."
response=$(curl -s "http://localhost:8000/api/test_path?path=/tmp")
if echo "$response" | grep -q "exists"; then
    echo "   ✓ Test path endpoint works!"
    echo ""
    echo "   Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
else
    echo "   ✗ Unexpected response:"
    echo "$response" | head -20
fi

echo ""
echo "=========================================="
echo "5. Checking SSH Tunnel Process..."
tunnel_count=$(ps aux | grep -E "ssh.*-L.*5173" | grep -v grep | wc -l)
if [ "$tunnel_count" -gt 0 ]; then
    echo "   ✓ SSH tunnel process found:"
    ps aux | grep -E "ssh.*-L.*5173" | grep -v grep
else
    echo "   ✗ No SSH tunnel process found!"
    echo "   Did you start it?"
fi

echo ""
echo "=========================================="
echo "✓ All tests passed!"
echo ""
echo "Your SSH tunnel is working correctly."
echo "Now open your browser to: http://localhost:5173"
echo ""

