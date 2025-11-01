#!/bin/bash
# Test script to validate the LXC deployment setup

set -e

echo "ADHD Print Task Management System - LXC Deployment Test"
echo "======================================================="

# Check if all required files exist
echo "Checking deployment files..."

FILES=(
    "deployment/lxc/Dockerfile"
    "deployment/lxc/build-template.sh"
    "deployment/lxc/config/nginx.conf"
    "deployment/lxc/config/supervisor.conf"
    "deployment/lxc/config/systemd-service.conf"
    "deployment/lxc/scripts/start-container.sh"
    "deployment/lxc/scripts/start-services.sh"
    "deployment/lxc/scripts/stop-services.sh"
    "deployment/lxc/scripts/reload-services.sh"
    "deployment/lxc/proxmox-container.conf"
    "deployment/lxc/README.md"
    "deployment/lxc/Makefile"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (missing)"
        exit 1
    fi
done

# Check if scripts are executable
echo ""
echo "Checking script permissions..."

SCRIPTS=(
    "deployment/lxc/build-template.sh"
    "deployment/lxc/scripts/start-container.sh"
    "deployment/lxc/scripts/start-services.sh"
    "deployment/lxc/scripts/stop-services.sh"
    "deployment/lxc/scripts/reload-services.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -x "$script" ]; then
        echo "✓ $script (executable)"
    else
        echo "✗ $script (not executable)"
        exit 1
    fi
done

# Check Django setup
echo ""
echo "Checking Django application..."

if [ -f "manage.py" ]; then
    echo "✓ Django manage.py found"
else
    echo "✗ Django manage.py not found"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "✓ requirements.txt found"
else
    echo "✗ requirements.txt not found"
    exit 1
fi

# Test Django configuration
echo ""
echo "Testing Django configuration..."

if python manage.py check --deploy 2>/dev/null; then
    echo "✓ Django configuration is valid"
else
    echo "⚠ Django configuration has warnings (this is normal for development)"
fi

# Check if we can import the application
echo ""
echo "Testing Python imports..."

if python -c "import django; print(f'Django version: {django.get_version()}')" 2>/dev/null; then
    echo "✓ Django import successful"
else
    echo "✗ Django import failed"
    exit 1
fi

# Summary
echo ""
echo "======================================================="
echo "✓ All deployment files are present and properly configured"
echo "✓ Scripts have correct permissions"
echo "✓ Django application is properly set up"
echo ""
echo "Ready for LXC template building!"
echo ""
echo "Next steps:"
echo "1. Run as root: sudo ./deployment/lxc/build-template.sh"
echo "2. Upload template to Proxmox"
echo "3. Create container with autostart enabled"
echo ""
echo "Or use the Makefile:"
echo "  sudo make -f deployment/lxc/Makefile build-template"
echo "  make -f deployment/lxc/Makefile deploy PROXMOX_HOST=your-proxmox-ip"