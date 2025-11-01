#!/bin/bash
set -e

# ADHD Print Task Management System - LXC Template Builder
# This script builds an LXC template for Proxmox deployment

TEMPLATE_NAME="adhd-print-taskmanager"
TEMPLATE_VERSION="1.0"
TEMPLATE_FILE="${TEMPLATE_NAME}-${TEMPLATE_VERSION}.tar.gz"
BUILD_DIR="/tmp/lxc-build-$$"
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
APP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

echo "Building LXC template for ADHD Print Task Management System..."
echo "Source directory: $APP_DIR"
echo "Build directory: $BUILD_DIR"
echo "Template file: $TEMPLATE_FILE"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root (required for LXC template creation)"
    exit 1
fi

# Clean up any previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create container filesystem structure
echo "Creating container filesystem structure..."
mkdir -p "$BUILD_DIR/rootfs"

# Download and extract Alpine Linux base
echo "Downloading Alpine Linux 3.18 base..."
cd "$BUILD_DIR"
wget -O alpine-base.tar.gz "https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/x86_64/alpine-minirootfs-3.18.4-x86_64.tar.gz"
cd rootfs
tar -xf ../alpine-base.tar.gz
cd ..

# Copy application files
echo "Copying application files..."
mkdir -p "$BUILD_DIR/rootfs/opt/adhd-print"
rsync -av --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='venv' \
    "$APP_DIR/" "$BUILD_DIR/rootfs/opt/adhd-print/"

# Copy deployment files
cp -r "$SCRIPT_DIR/config" "$BUILD_DIR/rootfs/tmp/"
cp -r "$SCRIPT_DIR/scripts" "$BUILD_DIR/rootfs/opt/adhd-print/"

# Create setup script that will run on first boot
cat > "$BUILD_DIR/rootfs/root/setup-adhd-print.sh" << 'EOF'
#!/bin/sh
set -e

echo "Setting up ADHD Print Task Management System on Alpine Linux..."

# Update package index
apk update

# Install system dependencies
apk add --no-cache \
    python3 \
    py3-pip \
    python3-dev \
    build-base \
    pkgconfig \
    cairo-dev \
    gobject-introspection-dev \
    git \
    nginx \
    supervisor \
    sqlite \
    curl \
    wget \
    nano \
    openrc \
    net-tools \
    iputils \
    openssh \
    openssl \
    bash \
    shadow \
    sudo

# Enable OpenRC (Alpine's init system)
rc-update add nginx default
rc-update add supervisor default
rc-update add sshd default

# Create application user
adduser -D -s /bin/bash adhd 2>/dev/null || true
echo 'adhd:adhd' | chpasswd
addgroup adhd wheel 2>/dev/null || true

# Configure sudo for wheel group
echo '%wheel ALL=(ALL) ALL' >> /etc/sudoers

# Set ownership
chown -R adhd:adhd /opt/adhd-print
chmod +x /opt/adhd-print/scripts/*.sh

# Create Python virtual environment
cd /opt/adhd-print
sudo -u adhd python3 -m venv venv

# Install Python dependencies
sudo -u adhd sh -c '. venv/bin/activate && pip install --upgrade pip'
sudo -u adhd sh -c '. venv/bin/activate && pip install -r requirements.txt'

# Create log directory
mkdir -p /var/log/adhd-print
chown adhd:adhd /var/log/adhd-print

# Configure nginx
cp /tmp/config/nginx.conf /etc/nginx/http.d/adhd-print.conf
rm -f /etc/nginx/http.d/default.conf

# Configure supervisor
cp /tmp/config/supervisor.conf /etc/supervisor.d/adhd-print.ini

# Configure OpenRC service (Alpine's init system)
cp /tmp/config/openrc-service /etc/init.d/adhd-print
chmod +x /etc/init.d/adhd-print
rc-update add adhd-print default

# Configure SSH
ssh-keygen -A
echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config

# Initialize database
cd /opt/adhd-print
sudo -u adhd sh -c '. venv/bin/activate && python manage.py migrate'
sudo -u adhd sh -c '. venv/bin/activate && python manage.py collectstatic --noinput'

# Create admin user
sudo -u adhd sh -c '. venv/bin/activate && python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username=\"admin\").exists():
    User.objects.create_superuser(\"admin\", \"admin@localhost\", \"admin123\")
    print(\"Created admin user: admin/admin123\")
"'

# Set root password for SSH access
echo 'root:alpine123' | chpasswd

# Clean up
rm -rf /tmp/config

echo "ADHD Print Task Management System setup completed!"
echo "The container is ready for deployment."
echo "SSH access: root/alpine123, adhd/adhd"
EOF

chmod +x "$BUILD_DIR/rootfs/root/setup-adhd-print.sh"

# Create LXC template metadata
cat > "$BUILD_DIR/metadata.yaml" << EOF
architecture: amd64
creation_date: $(date +%s)
properties:
  description: "ADHD Print Task Management System - Django-based task management with ESC/POS printer support (Alpine Linux)"
  os: alpine
  release: "3.18"
  variant: default
  name: ${TEMPLATE_NAME}
  version: ${TEMPLATE_VERSION}
templates:
  /root/setup-adhd-print.sh:
    when:
      - create
      - copy
    create_only: false
EOF

# Create template tarball
echo "Creating template archive..."
cd "$BUILD_DIR"
tar -czf "$TEMPLATE_FILE" metadata.yaml rootfs/

# Move template to output location
mv "$TEMPLATE_FILE" "$APP_DIR/"

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "=========================================="
echo "Alpine Linux LXC Template created successfully!"
echo "=========================================="
echo "Template file: $APP_DIR/$TEMPLATE_FILE"
echo "Base OS: Alpine Linux 3.18 (much smaller than Ubuntu!)"
echo ""
echo "To deploy on Proxmox:"
echo "1. Copy $TEMPLATE_FILE to your Proxmox server"
echo "2. Upload via Proxmox web interface: Datacenter > Storage > Templates"
echo "3. Or via command line:"
echo "   scp $TEMPLATE_FILE root@proxmox-host:/var/lib/vz/template/cache/"
echo ""
echo "To create container:"
echo "1. In Proxmox web interface: Create CT > Choose this template"
echo "2. Or via command line:"
echo "   pct create 100 /var/lib/vz/template/cache/$TEMPLATE_FILE \\"
echo "     --hostname adhd-print \\"
echo "     --memory 1024 \\"
echo "     --rootfs local-lvm:4 \\"
echo "     --net0 name=eth0,bridge=vmbr0,ip=dhcp \\"
echo "     --onboot 1 \\"
echo "     --start 1"
echo ""
echo "Container credentials:"
echo "  Admin user: admin / admin123"
echo "  SSH root: root / alpine123"
echo "  SSH user: adhd / adhd"
echo ""
echo "Application will be available at: http://[container-ip]/"
echo "SSH access: ssh root@[container-ip] or ssh adhd@[container-ip]"
echo "Memory usage: Much lower due to Alpine Linux base!"
echo "=========================================="