#!/bin/bash
set -e

echo "Reloading ADHD Print services..."

# Reload nginx configuration
systemctl reload nginx

# Restart supervisor to pick up any changes
systemctl restart supervisor

echo "Services reloaded successfully!"