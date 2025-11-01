#!/bin/bash
set -e

echo "Starting ADHD Print services..."

# Start supervisor (which manages Django and workers)
systemctl start supervisor
sleep 2

# Start nginx
systemctl start nginx
sleep 1

echo "Services started successfully!"
systemctl status supervisor --no-pager
systemctl status nginx --no-pager