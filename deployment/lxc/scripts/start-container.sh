#!/bin/bash
set -e

echo "Starting ADHD Print Task Management System..."

# Start nginx
echo "Starting nginx..."
systemctl start nginx

# Start supervisor (which will start Django and workers)
echo "Starting supervisor..."
systemctl start supervisor

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 5

# Check if Django is responding
echo "Checking Django health..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -f http://127.0.0.1:8000/ > /dev/null 2>&1; then
        echo "Django is ready!"
        break
    fi
    echo "Waiting for Django to start... (attempt $attempt/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -gt $max_attempts ]; then
    echo "Django failed to start within expected time"
    exit 1
fi

# Check if nginx is responding
echo "Checking nginx health..."
if curl -f http://127.0.0.1/ > /dev/null 2>&1; then
    echo "Nginx is ready!"
else
    echo "Warning: Nginx may not be responding correctly"
fi

echo "ADHD Print Task Management System started successfully!"
echo "Access the application at: http://[container-ip]/"
echo "Default admin credentials: admin / admin123"

# Keep container running
tail -f /var/log/adhd-print/django.log