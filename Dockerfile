# ADHD Print Task Management System - Development Dockerfile
# Optimized Alpine multi-stage build for development and testing

# Stage 1: Builder with build dependencies
FROM python:3.13-alpine AS builder

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    linux-headers \
    freetype-dev \
    jpeg-dev \
    libpng-dev \
    libffi-dev \
    openssl-dev \
    git

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Development runtime with minimal dependencies
FROM python:3.13-alpine

# Install runtime dependencies
RUN apk add --no-cache \
    bash \
    freetype \
    jpeg \
    libpng \
    libffi \
    openssl \
    fontconfig \
    ttf-dejavu \
    ttf-liberation \
    curl \
    && apk add --no-cache --repository=http://dl-cdn.alpinelinux.org/alpine/edge/community \
    font-roboto

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

# Create application user
RUN adduser -D -s /bin/bash -u 1000 adhd_print

# Set work directory
WORKDIR /app

# Copy application code
COPY --chown=adhd_print:adhd_print . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/static /app/staticfiles /app/logs && \
    chown -R adhd_print:adhd_print /app

# Switch to non-root user
USER adhd_print

# Collect static files
RUN python manage.py collectstatic --noinput --settings=adhd_print_project.settings

# Health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/tasks/ || exit 1

# Expose port
EXPOSE 8000

# Default command for development (Django runserver)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]