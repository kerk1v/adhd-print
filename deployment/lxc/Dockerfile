# LXC Container for ADHD Print Task Management System
# Based on Ubuntu 22.04 LTS
FROM ubuntu:22.04

LABEL maintainer="ADHD Print Task Management"
LABEL description="Django-based task management system with ESC/POS printer support"
LABEL version="1.0"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=adhd_print_project.settings

# Set timezone
ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    git \
    nginx \
    supervisor \
    sqlite3 \
    curl \
    wget \
    nano \
    systemctl \
    net-tools \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -m -s /bin/bash adhd && \
    usermod -aG sudo adhd

# Create application directory
RUN mkdir -p /opt/adhd-print && \
    chown adhd:adhd /opt/adhd-print

# Switch to application user
USER adhd
WORKDIR /opt/adhd-print

# Create Python virtual environment
RUN python3 -m venv venv

# Copy application files
COPY --chown=adhd:adhd . /opt/adhd-print/

# Install Python dependencies
RUN . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Switch back to root for system configuration
USER root

# Create necessary directories
RUN mkdir -p /var/log/adhd-print && \
    chown adhd:adhd /var/log/adhd-print

# Copy configuration files
COPY deployment/lxc/config/nginx.conf /etc/nginx/sites-available/adhd-print
COPY deployment/lxc/config/supervisor.conf /etc/supervisor/conf.d/adhd-print.conf
COPY deployment/lxc/config/systemd-service.conf /etc/systemd/system/adhd-print.service

# Configure Nginx
RUN rm /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/adhd-print /etc/nginx/sites-enabled/

# Make scripts executable
COPY deployment/lxc/scripts/ /opt/adhd-print/scripts/
RUN chmod +x /opt/adhd-print/scripts/*.sh

# Initialize database and collect static files
USER adhd
WORKDIR /opt/adhd-print
RUN . venv/bin/activate && \
    python manage.py migrate && \
    python manage.py collectstatic --noinput && \
    python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    print('Created admin user: admin/admin123')
"

# Switch back to root for final setup
USER root

# Enable services
RUN systemctl enable nginx && \
    systemctl enable supervisor && \
    systemctl enable adhd-print

# Expose ports
EXPOSE 80 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Start services
CMD ["/opt/adhd-print/scripts/start-container.sh"]