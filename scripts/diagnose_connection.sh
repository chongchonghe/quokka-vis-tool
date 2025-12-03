#!/bin/bash

echo "=========================================="
echo "Connection Diagnosis"
echo "=========================================="
echo ""

echo "1. Checking if backend is running..."
if lsof -i :8000 > /dev/null 2>&1; then
    echo "   ✓ Something is listening on port 8000"
    lsof -i :8000
else
    echo "   ✗ Nothing listening on port 8000"
    echo "   Backend is NOT running!"
    exit 1
fi

echo ""
echo "2. Checking if frontend dev server is running..."
if lsof -i :5173 > /dev/null 2>&1; then
    echo "   ✓ Something is listening on port 5173"
    lsof -i :5173
else
    echo "   ✗ Nothing listening on port 5173"
fi

if lsof -i :5174 > /dev/null 2>&1; then
    echo "   ✓ Something is listening on port 5174"
    lsof -i :5174
fi

echo ""
echo "3. Testing backend connection..."
echo "   Trying http://localhost:8000/..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "   ✓ Backend responds!"
    echo "   Response:"
    curl -s http://localhost:8000/ | head -20
else
    echo "   ✗ Backend does not respond"
    echo "   This means backend is not running or not accessible"
fi

echo ""
echo "4. Testing test_path endpoint..."
echo "   Trying http://localhost:8000/api/test_path?path=/tmp..."
response=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/test_path?path=/tmp)
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

echo "   HTTP Status: $http_code"
if [ "$http_code" = "200" ]; then
    echo "   ✓ Endpoint works!"
    echo "$body" | head -20
elif [ "$http_code" = "500" ]; then
    echo "   ✗ Backend returns 500 error"
    echo "   First 300 chars of response:"
    echo "$body" | head -c 300
else
    echo "   ✗ Unexpected status: $http_code"
    echo "$body" | head -20
fi

echo ""
echo "=========================================="
echo "5. Where is the backend process?"
ps aux | grep -i uvicorn | grep -v grep
echo ""
echo "6. What ports are being used?"
netstat -an | grep LISTEN | grep -E ':(5173|5174|8000)' || lsof -i -P | grep -E ':(5173|5174|8000)'

echo ""
echo "=========================================="

