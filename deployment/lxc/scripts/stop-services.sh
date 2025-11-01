#!/bin/bash
set -e

echo "Stopping ADHD Print services..."

# Stop nginx
systemctl stop nginx || true

# Stop supervisor (which stops Django and workers)
systemctl stop supervisor || true

echo "Services stopped successfully!"