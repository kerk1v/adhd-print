# ADHD Print Task Management System - Complete Deployment Guide

## 🎯 Project Status: ✅ Production Ready

This Django-based task management system with thermal printing capabilities is fully configured and deployment-ready with multiple deployment options.

## 📋 Table of Contents

1. [Quick Start Deployment](#quick-start-deployment)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [ASGI Production Deployment](#asgi-production-deployment)
5. [Proxmox LXC Container Deployment](#proxmox-lxc-container-deployment)
6. [Traditional Server Deployment](#traditional-server-deployment)
7. [Printer Configuration](#printer-configuration)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start Deployment

### Prerequisites
- Python 3.8+
- At least 1GB RAM
- Network-connected ESC/POS thermal printer (optional)

### Basic Setup
```bash
# Clone and setup
git clone <repository>
cd adhd-print
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configuration (optional - defaults work)
cp .env.example .env

# Database setup
python manage.py migrate
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

Access at: http://127.0.0.1:8000/tasks/

---

## ⚙️ Environment Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ADHD_PRINT_DATA_DIR` | `./data` | Directory for database and data files |
| `ADHD_PRINT_DB_NAME` | `adhd_print.db` | Database filename |
| `ADHD_PRINT_PRINTER_HOST` | `192.168.1.40` | Thermal printer IP address |
| `ADHD_PRINT_PRINTER_PORT` | `9100` | Thermal printer port |
| `ADHD_PRINT_USE_GRAPHICS` | `True` | Enable graphics printing mode |

### Configuration Examples

#### Development (.env)
```bash
ADHD_PRINT_DATA_DIR=./data
ADHD_PRINT_DB_NAME=adhd_print.db
ADHD_PRINT_PRINTER_HOST=192.168.1.40
ADHD_PRINT_PRINTER_PORT=9100
ADHD_PRINT_USE_GRAPHICS=True
```

#### Production
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,localhost
ADHD_PRINT_DATA_DIR=/var/lib/adhd-print
ADHD_PRINT_DB_NAME=production.db
ADHD_PRINT_PRINTER_HOST=production-printer-ip
```

---

## 🐳 Docker Deployment

### Development with Docker

```bash
# Quick start
./docker_setup.sh dev

# Or manually
docker-compose up -d
```

Access at: http://localhost:8000

### Production with Docker

```bash
# Setup production environment
./docker_setup.sh prod

# Or manually with production compose
docker-compose -f docker-compose.prod.yml up -d
```

Access at: http://localhost

### Docker Services

#### Development (docker-compose.yml)
- **adhd-print-app**: Django development server
- **Volumes**: Code, data, static files, logs
- **Ports**: 8000:8000

#### Production (docker-compose.prod.yml)
- **adhd-print**: ASGI application server
- **postgres**: PostgreSQL database
- **redis**: Caching and session storage
- **nginx**: Reverse proxy and static file server

### Production Environment File
Create `.env.production`:
```bash
DB_PASSWORD=secure_database_password
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### Docker Management Commands
```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Backup data
./docker_setup.sh backup

# Restore from backup
./docker_setup.sh restore backup_file.tar.gz

# Complete cleanup
./docker_setup.sh clean
```

---

## ⚡ ASGI Production Deployment

### Why ASGI?
- **Better Performance**: Asynchronous request handling
- **Modern Architecture**: WebSocket-ready for future features
- **Scalability**: Multi-worker support
- **Production Ready**: Suitable for high-traffic deployments

### Quick ASGI Start

```bash
# Development with auto-reload
python manage.py runasgi --reload

# Production with multiple workers
ASGI_HOST=0.0.0.0 ASGI_WORKERS=4 ./start_asgi.sh
```

### ASGI Environment Configuration
```bash
# ASGI server settings
ASGI_HOST=0.0.0.0
ASGI_PORT=8000
ASGI_WORKERS=4
ASGI_LOG_LEVEL=info
ASGI_RELOAD=false

# Background jobs
BACKGROUND_JOBS_ENABLED=true
MAINTENANCE_SCHEDULE_HOUR=2
MAINTENANCE_SCHEDULE_MINUTE=0
```

### Production ASGI with systemd

Create `/etc/systemd/system/adhd-print.service`:
```ini
[Unit]
Description=ADHD Print Task Management ASGI Server
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/adhd-print
Environment=ASGI_HOST=0.0.0.0
Environment=ASGI_PORT=8000
Environment=ASGI_WORKERS=4
ExecStart=/path/to/adhd-print/start_asgi.sh
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable adhd-print
sudo systemctl start adhd-print
sudo systemctl status adhd-print
```

### ASGI with nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/adhd-print/static/;
    }
}
```

---

## 📦 Proxmox LXC Container Deployment

### Quick LXC Deployment

1. **Build Alpine Linux template:**
   ```bash
   sudo ./deployment/lxc/build-template.sh
   ```

2. **Upload to Proxmox:**
   ```bash
   scp adhd-print-taskmanager-1.0.tar.gz root@proxmox-host:/var/lib/vz/template/cache/
   ```

3. **Create container:**
   ```bash
   pct create 100 /var/lib/vz/template/cache/adhd-print-taskmanager-1.0.tar.gz \
     --hostname adhd-print \
     --memory 1024 \
     --rootfs local-lvm:4 \
     --net0 name=eth0,bridge=vmbr0,ip=dhcp \
     --onboot 1 \
     --start 1
   ```

### LXC Container Features
- **Alpine Linux 3.18**: Lightweight base (3.1MB vs 401MB Ubuntu)
- **Complete Setup**: Automatic installation and configuration
- **SSH Access**: root/alpine123, adhd/adhd
- **Autostart**: Configured for automatic startup
- **Resource Efficient**: 1GB RAM, 4GB storage

### LXC Management
```bash
# Container controls
pct start 100
pct stop 100
pct enter 100

# Application management (inside container)
systemctl status adhd-print nginx supervisor
tail -f /var/log/adhd-print/django.log
```

### Container Access
- **Web Interface**: `http://[container-ip]/`
- **Admin Panel**: `http://[container-ip]/admin/`
- **Default Credentials**: admin/admin123
- **SSH Access**: `ssh root@[container-ip]` or `ssh adhd@[container-ip]`

---

## 🖥️ Traditional Server Deployment

### Ubuntu/Debian Server

```bash
# System dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx supervisor sqlite3

# Application setup
cd /opt
sudo git clone <repository> adhd-print
cd adhd-print
sudo python3 -m venv venv
sudo ./venv/bin/pip install -r requirements.txt

# Database setup
sudo -u www-data ./venv/bin/python manage.py migrate
sudo -u www-data ./venv/bin/python manage.py collectstatic --noinput

# Create admin user
sudo -u www-data ./venv/bin/python manage.py createsuperuser
```

### nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /opt/adhd-print/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Supervisor Configuration
```ini
[program:adhd-print]
command=/opt/adhd-print/venv/bin/python manage.py runserver 127.0.0.1:8000
directory=/opt/adhd-print
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/adhd-print.log
```

---

## 🖨️ Printer Configuration

### Supported Hardware
- **Tested Model**: Qian QOP-T80UL-RI-02
- **Protocol**: ESC/POS
- **Connection**: TCP/IP (Ethernet)
- **Paper**: 80mm thermal paper
- **Graphics**: 576px width (72mm at 8 dots/mm)

### Network Setup
1. Connect printer to network
2. Note printer IP address (usually shown on test print)
3. Update environment variables:
   ```bash
   export ADHD_PRINT_PRINTER_HOST=192.168.1.100
   export ADHD_PRINT_PRINTER_PORT=9100
   ```
4. Test connection: `telnet <printer_ip> 9100`

### Print Features
- **Graphics Mode**: High-quality bitmap printing with Material Design icons
- **Text Mode**: ASCII fallback for basic printers
- **Professional Layout**: Roboto fonts, bordered output
- **Urgency Indicators**: Visual priority symbols
- **Error Handling**: Graceful degradation

---

## 📊 Monitoring & Maintenance

### Application Monitoring

#### Health Checks
```bash
# Check application status
curl http://localhost:8000/tasks/

# Background jobs status
python manage.py background_jobs status

# ASGI server status (if using ASGI)
ps aux | grep uvicorn
```

#### Log Monitoring
```bash
# Application logs
tail -f /var/log/adhd-print/django.log

# nginx logs
tail -f /var/log/nginx/access.log

# System logs
journalctl -u adhd-print -f
```

### Automated Maintenance

The application includes integrated background jobs that run automatically:
- **Nightly Maintenance**: 2:00 AM automatic task cleanup
- **Periodic Tasks**: Automatic generation of recurring task instances
- **Database Cleanup**: Removes old completed tasks
- **Admin Monitoring**: View maintenance logs at `/admin/tasks/maintenancelog/`

```bash
# Manual maintenance run
python manage.py background_jobs run_maintenance

# Check maintenance history
python manage.py background_jobs status
```

### Backup Procedures

#### Database Backup
```bash
# SQLite backup
cp data/adhd_print.db data/adhd_print.db.backup.$(date +%Y%m%d)

# PostgreSQL backup (if using)
pg_dump adhd_print > backup_$(date +%Y%m%d).sql
```

#### Complete System Backup
```bash
# Traditional deployment
tar czf adhd-print-backup-$(date +%Y%m%d).tar.gz /opt/adhd-print

# Docker deployment
./docker_setup.sh backup

# LXC deployment
vzdump 100 --mode snapshot --compress gzip
```

---

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Python dependencies
pip list | grep -E "(Django|Pillow|APScheduler)"

# Check database permissions
ls -la data/

# Check port availability
netstat -tulpn | grep :8000
```

#### Printing Issues
```bash
# Test printer connection
telnet 192.168.1.40 9100

# Check printer status
ping 192.168.1.40

# Test graphics mode
python -c "from tasks.print_utils import test_printer; test_printer()"
```

#### Database Issues
```bash
# Reset database (development only)
rm data/adhd_print.db
python manage.py migrate
python manage.py createsuperuser
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R www-data:www-data /opt/adhd-print
sudo chmod +x /opt/adhd-print/start_asgi.sh
```

### Performance Issues

#### High Memory Usage
```bash
# Check worker count
ps aux | grep -E "(python|uvicorn)"

# Reduce ASGI workers
export ASGI_WORKERS=2

# Monitor memory
htop
```

#### Slow Response Times
```bash
# Check database size
ls -lh data/adhd_print.db

# Check background jobs
python manage.py background_jobs status

# Monitor nginx logs
tail -f /var/log/nginx/access.log
```

### Debugging Tips

#### Enable Debug Mode
```bash
export DEBUG=True
export DJANGO_LOG_LEVEL=DEBUG
```

#### Check Configuration
```bash
# Verify environment variables
python -c "from django.conf import settings; print(settings.DATABASES)"

# Test database connection
python manage.py check --database default

# Validate static files
python manage.py collectstatic --dry-run
```

---

## ✅ Deployment Verification Checklist

Before going live, verify:

- [ ] Application starts without errors
- [ ] Database migrations completed
- [ ] Admin user created and accessible
- [ ] Static files loading correctly
- [ ] Printer responds to ping/telnet (if using)
- [ ] Environment variables configured correctly
- [ ] SSL/HTTPS configured (production)
- [ ] Backup procedures tested
- [ ] Monitoring tools configured
- [ ] Log rotation configured
- [ ] Firewall rules configured
- [ ] DNS configured (if using domain)
- [ ] Background jobs running
- [ ] Performance acceptable under load

---

## 📞 Support & Additional Resources

### Documentation Links
- **Features**: See FEATURES.md for detailed feature documentation
- **Testing**: See TESTING.md for comprehensive testing guide
- **Development**: See README.md for development setup

### Common Workflows
1. **Create Task**: Web interface → Add task with hierarchy
2. **Print Prompt**: After saving → Modal asks "Print this task?"
3. **Graphics Print**: High-quality output with Material Design icons
4. **Background Jobs**: Automatic nightly maintenance at 2:00 AM

### Architecture Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   nginx/proxy   │────│   Django/ASGI    │────│   Database      │
│   (port 80/443) │    │   (port 8000)    │    │   (SQLite/PG)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌──────────────────┐
                       │  Background Jobs │
                       │  (APScheduler)   │
                       └──────────────────┘
                                │
                       ┌──────────────────┐
                       │  Thermal Printer │
                       │  (ESC/POS TCP)   │
                       └──────────────────┘
```

The system is production-ready with multiple deployment options. Choose the approach that best fits your infrastructure and requirements.

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready