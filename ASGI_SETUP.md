# ASGI Configuration Guide for ADHD Print Task Management

This document explains how to run the ADHD Print Task Management application using ASGI (Asynchronous Server Gateway Interface) for improved performance and modern deployment capabilities.

## Overview

The application has been configured to run with ASGI, providing:

- ✅ **Asynchronous Request Handling** - Better performance under load
- ✅ **Modern Server Support** - Compatible with uvicorn, daphne, and other ASGI servers
- ✅ **WebSocket Ready** - Foundation for future real-time features
- ✅ **Better Resource Utilization** - More efficient handling of concurrent requests
- ✅ **Production Ready** - Suitable for deployment with modern hosting platforms

## Quick Start

### 1. **Using the Startup Script (Recommended)**

```bash
# Development mode with auto-reload
ASGI_RELOAD=true ./start_asgi.sh

# Production mode
./start_asgi.sh

# Custom configuration
ASGI_HOST=0.0.0.0 ASGI_PORT=8080 ASGI_WORKERS=4 ./start_asgi.sh
```

### 2. **Using Django Management Command**

```bash
# Basic ASGI server
python manage.py runasgi

# Development with auto-reload
python manage.py runasgi --reload

# Production with multiple workers
python manage.py runasgi --host 0.0.0.0 --port 8000 --workers 4

# Custom log level
python manage.py runasgi --log-level debug
```

### 3. **Direct uvicorn Usage**

```bash
# Basic usage
uvicorn adhd_print_project.asgi:application

# Production configuration
uvicorn adhd_print_project.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Server Configuration
ASGI_HOST=127.0.0.1
ASGI_PORT=8000
ASGI_WORKERS=1
ASGI_LOG_LEVEL=info
ASGI_RELOAD=false

# Django Settings
DJANGO_SETTINGS_MODULE=adhd_print_project.settings

# Background Jobs
BACKGROUND_JOBS_ENABLED=true
MAINTENANCE_SCHEDULE_HOUR=2
MAINTENANCE_SCHEDULE_MINUTE=0

# Production Settings
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### Configuration Files

Copy and customize the example configuration:

```bash
cp .env.asgi.example .env
# Edit .env with your specific settings
```

## Features

### 1. **Integrated Background Jobs**

The ASGI setup includes the background job system:

- ✅ **Automatic Startup** - Background jobs start with the ASGI server
- ✅ **Configurable Schedule** - Environment-controlled maintenance timing
- ✅ **Graceful Shutdown** - Proper cleanup on server stop
- ✅ **Error Handling** - Robust error recovery and logging

### 2. **Lifespan Management**

The ASGI application properly handles:

- **Startup Events** - Initialize resources when server starts
- **Shutdown Events** - Clean up resources when server stops
- **Error Recovery** - Graceful handling of startup/shutdown failures

### 3. **Enhanced Error Handling**

- **HTTP Error Responses** - Proper 500 error pages for application failures
- **Detailed Logging** - Comprehensive error logging with stack traces
- **Graceful Degradation** - Server continues operation despite non-critical errors

## Production Deployment

### 1. **Basic Production Setup**

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start production server
ASGI_HOST=0.0.0.0 ASGI_PORT=8000 ASGI_WORKERS=4 ./start_asgi.sh
```

### 2. **With Process Manager (systemd)**

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
Environment=ASGI_LOG_LEVEL=info
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

### 3. **With Docker**

Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x start_asgi.sh

EXPOSE 8000
CMD ["./start_asgi.sh"]
```

Build and run:

```bash
docker build -t adhd-print .
docker run -p 8000:8000 -e ASGI_HOST=0.0.0.0 adhd-print
```

### 4. **Behind Reverse Proxy (nginx)**

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

## Performance Optimization

### 1. **Worker Configuration**

```bash
# CPU-bound tasks: workers = CPU cores
ASGI_WORKERS=4

# I/O-bound tasks: workers = 2 * CPU cores
ASGI_WORKERS=8

# Development: single worker with reload
ASGI_WORKERS=1 ASGI_RELOAD=true
```

### 2. **Resource Limits**

```bash
# Limit memory usage
ulimit -v 2097152  # 2GB virtual memory

# Increase file descriptor limit
ulimit -n 65536
```

### 3. **Database Optimization**

```python
# In settings.py for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'adhd_print',
        'USER': 'adhd_print_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}
```

## Monitoring and Logging

### 1. **Application Logs**

```bash
# View server logs
tail -f logs/asgi.log

# Monitor background jobs
python manage.py background_jobs status

# Check maintenance logs in admin interface
# Navigate to /admin/tasks/maintenancelog/
```

### 2. **Health Checks**

```bash
# Basic health check
curl http://localhost:8000/

# Admin interface check
curl -I http://localhost:8000/admin/

# Background jobs status
python manage.py background_jobs status
```

### 3. **Performance Monitoring**

Use tools like:

- **htop** - System resource monitoring
- **iotop** - Disk I/O monitoring  
- **netstat** - Network connection monitoring
- **Django Debug Toolbar** - Application performance (development only)

## Migration from WSGI

If migrating from WSGI (runserver):

### 1. **No Code Changes Required**
- All existing views and functionality work unchanged
- Background jobs continue operating normally
- Database and static files remain the same

### 2. **Update Deployment Scripts**
- Replace `python manage.py runserver` with `python manage.py runasgi`
- Update process managers (systemd, supervisor) to use ASGI
- Modify Docker containers to use ASGI startup

### 3. **Update Reverse Proxy Configuration**
- No changes needed for nginx/Apache reverse proxy
- Same proxy headers and configuration apply

## Troubleshooting

### 1. **Server Won't Start**

```bash
# Check port availability
netstat -tulpn | grep :8000

# Check permissions
ls -la start_asgi.sh

# Check Python path
which python
python --version
```

### 2. **Background Jobs Not Working**

```bash
# Check background jobs status
python manage.py background_jobs status

# Check Django apps configuration
python manage.py check

# Verify APScheduler installation
pip show APScheduler
```

### 3. **Performance Issues**

```bash
# Monitor resource usage
top -p $(pgrep -f "runasgi")

# Check database connections
python manage.py dbshell
# Run: SELECT * FROM pg_stat_activity; (PostgreSQL)

# Analyze logs
grep ERROR logs/asgi.log
```

### 4. **Connection Errors**

```bash
# Test connectivity
curl -v http://localhost:8000/

# Check firewall
sudo ufw status

# Verify DNS resolution
nslookup your-domain.com
```

## Security Considerations

### 1. **Environment Variables**
- Never commit `.env` files to version control
- Use secure secrets management in production
- Rotate SECRET_KEY regularly

### 2. **Network Security**
- Bind to 127.0.0.1 for local access only
- Use 0.0.0.0 only behind reverse proxy
- Configure firewall rules appropriately

### 3. **Process Security**
- Run as non-root user in production
- Use process isolation (containers/systemd)
- Monitor for unusual resource usage

## Future Enhancements

The ASGI foundation enables future features:

- 🔮 **WebSocket Support** - Real-time task updates
- 🔮 **Server-Sent Events** - Live progress notifications
- 🔮 **Async Views** - Even better performance
- 🔮 **Background Task Queues** - Distributed task processing

## Support

For issues related to ASGI configuration:

1. Check the troubleshooting section above
2. Review logs in `logs/` directory
3. Verify environment configuration
4. Test with minimal configuration first
5. Check Django and uvicorn documentation

The ASGI configuration provides a solid foundation for scalable, production-ready deployment of the ADHD Print Task Management system.