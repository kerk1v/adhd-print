# ADHD Print Task Management System - Dockerfile
# Multi-stage build for production optimization

# Stage 1: Base Python image with system dependencies
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libjpeg-dev \
    libpng-dev \
    libffi-dev \
    libssl-dev \
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash adhd_print

# Stage 2: Python dependencies
FROM base as python-deps

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 3: Application
FROM python-deps as application

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=adhd_print:adhd_print . /app/

# Create necessary directories
RUN mkdir -p /app/data /app/static /app/staticfiles /app/logs && \
    chown -R adhd_print:adhd_print /app

# Switch to non-root user
USER adhd_print

# Collect static files
RUN python manage.py collectstatic --noinput --settings=adhd_print_project.settings

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/tasks/ || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]