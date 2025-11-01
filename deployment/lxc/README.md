# ADHD Print Task Management System - Proxmox LXC Deployment Guide

## Overview

This guide provides instructions for deploying the ADHD Print Task Management System as an LXC container on Proxmox with autostart capabilities.

## Prerequisites

- Proxmox VE 7.0 or later
- At least 2GB RAM available for the container
- 8GB storage space
- Network access for the container

## Quick Deployment

### Option 1: Automated Build and Deploy

1. **Build the LXC template:**
   ```bash
   cd /path/to/adhd-print
   sudo ./deployment/lxc/build-template.sh
   ```

2. **Upload to Proxmox:**
   ```bash
   scp adhd-print-taskmanager-1.0.tar.gz root@your-proxmox-host:/var/lib/vz/template/cache/
   ```

3. **Create container via CLI:**
   ```bash
   pct create 100 /var/lib/vz/template/cache/adhd-print-taskmanager-1.0.tar.gz \
     --hostname adhd-print \
     --cores 2 \
     --memory 2048 \
     --rootfs local-lvm:8 \
     --net0 name=eth0,bridge=vmbr0,ip=dhcp \
     --onboot 1 \
     --unprivileged 1 \
     --features nesting=1 \
     --start 1
   ```

### Option 2: Manual Setup via Proxmox Web Interface

1. **Upload Template:**
   - Login to Proxmox web interface
   - Go to: Datacenter → Storage → Templates
   - Upload the `adhd-print-taskmanager-1.0.tar.gz` file

2. **Create Container:**
   - Click "Create CT"
   - Choose the uploaded template
   - Configure as follows:
     - **General:** CT ID, hostname: `adhd-print`, password
     - **Template:** Select the uploaded template
     - **Root Disk:** 8GB minimum
     - **CPU:** 2 cores
     - **Memory:** 2048MB RAM, 512MB swap
     - **Network:** Bridge=vmbr0, IP=DHCP (or static)
     - **DNS:** Use host settings
     - **Confirm:** Start after created ✓

## Container Configuration

### Resource Allocation
- **CPU:** 2 cores (minimum 1)
- **RAM:** 2048MB (minimum 1024MB)
- **Disk:** 8GB (minimum for app + OS)
- **Swap:** 512MB

### Network Setup
- **Default:** DHCP on vmbr0 bridge
- **Static IP Example:**
  ```
  net0: name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1
  ```

### Autostart Configuration
The container is configured to start automatically with Proxmox:
- `onboot: 1` - Start on Proxmox boot
- `startup: order=3,up=30,down=30` - Start order and delays

## Post-Deployment Setup

### 1. Container First Boot
After container creation, it will automatically:
- Install system dependencies
- Set up Python virtual environment
- Configure nginx and supervisor
- Initialize database
- Create admin user
- Start all services

### 2. Access the Application
- **Web Interface:** `http://[container-ip]/`
- **Default Credentials:** `admin` / `admin123`
- **Admin Panel:** `http://[container-ip]/admin/`

### 3. Configure Printer (Optional)
If using ESC/POS printer:
1. SSH into container: `ssh adhd@[container-ip]`
2. Edit settings: `nano /opt/adhd-print/adhd_print_project/settings.py`
3. Update printer IP: `PRINTER_IP = "YOUR_PRINTER_IP"`
4. Restart services: `sudo systemctl restart adhd-print`

## Management Commands

### Container Management
```bash
# Start container
pct start 100

# Stop container  
pct stop 100

# Enter container
pct enter 100

# Container status
pct status 100

# Container configuration
pct config 100
```

### Application Management (inside container)
```bash
# Check service status
sudo systemctl status adhd-print
sudo systemctl status nginx
sudo systemctl status supervisor

# View logs
sudo tail -f /var/log/adhd-print/django.log
sudo tail -f /var/log/nginx/adhd-print-access.log

# Restart application
sudo systemctl restart adhd-print

# Django management
cd /opt/adhd-print
source venv/bin/activate
python manage.py createsuperuser  # Create additional admin user
python manage.py migrate          # Run database migrations
python manage.py collectstatic    # Update static files
```

## Backup and Restore

### Backup Container
```bash
# Create backup
vzdump 100 --mode snapshot --compress gzip

# Backup to external storage
vzdump 100 --storage backup-storage --mode snapshot
```

### Restore Container
```bash
# Restore from backup
qmrestore /var/lib/vz/dump/vzdump-lxc-100-*.tar.gz 101
```

## Troubleshooting

### Common Issues

1. **Container won't start:**
   ```bash
   # Check container config
   pct config 100
   
   # Check Proxmox logs
   journalctl -u pve-container@100
   ```

2. **Application not accessible:**
   ```bash
   # Enter container and check services
   pct enter 100
   systemctl status adhd-print nginx supervisor
   
   # Check logs
   tail -f /var/log/adhd-print/django.log
   ```

3. **Database issues:**
   ```bash
   # Reset database (inside container)
   cd /opt/adhd-print
   source venv/bin/activate
   rm db.sqlite3
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Log Locations
- **Application:** `/var/log/adhd-print/django.log`
- **Worker:** `/var/log/adhd-print/worker.log`
- **Nginx:** `/var/log/nginx/adhd-print-access.log`
- **System:** `journalctl -u adhd-print`

## Security Considerations

1. **Change default password:** Login and change admin password immediately
2. **Firewall:** Configure Proxmox firewall to restrict access
3. **Updates:** Regularly update container packages:
   ```bash
   apt update && apt upgrade
   ```
4. **Backup:** Set up regular automated backups
5. **Network:** Use isolated network if possible

## Resource Monitoring

### Inside Container
```bash
# System resources
htop
df -h
free -h

# Application processes
ps aux | grep python
supervisorctl status
```

### From Proxmox
- Web Interface: Container → Summary
- CLI: `pct status 100`

## Scaling Options

### Vertical Scaling (within container)
- Increase CPU cores
- Add more RAM
- Expand disk space

### Horizontal Scaling
- Load balancer in front of multiple containers
- Shared database setup
- Redis/cache layer

## Advanced Configuration

### Custom Environment Variables
Edit `/opt/adhd-print/adhd_print_project/settings.py` or create `.env` file:
```bash
DEBUG=False
ALLOWED_HOSTS=your-domain.com,192.168.1.100
PRINTER_IP=192.168.1.50
SECRET_KEY=your-secret-key
```

### HTTPS Setup
1. Install certbot in container
2. Configure nginx SSL
3. Update Proxmox port forwarding

### External Database
1. Install PostgreSQL/MySQL client in container
2. Update Django database settings
3. Migrate data if needed

## Support

For issues and questions:
- Check application logs: `/var/log/adhd-print/`
- Review this documentation
- Consult Proxmox documentation for container management

---

**Note:** This deployment provides a complete, self-contained ADHD Print Task Management System ready for production use with minimal manual configuration required.