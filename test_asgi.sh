#!/bin/bash

# Simple test script for ASGI server functionality
echo "Testing ASGI server functionality..."

# Start ASGI server in background
echo "Starting ASGI server..."
python manage.py runasgi --host 127.0.0.1 --port 8001 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Test basic endpoints
echo "Testing endpoints..."

# Test admin page
echo -n "Admin page: "
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/admin/ | grep -q "200\|302"; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test tasks page (should redirect to login)
echo -n "Tasks page: "
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/tasks/ | grep -q "200\|302"; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Test static files
echo -n "Admin CSS: "
if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8001/static/admin/css/base.css | grep -q "200"; then
    echo "✅ OK"
else
    echo "❌ FAILED"
fi

# Cleanup
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo "Test completed!"