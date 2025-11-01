"""
Test settings for ADHD Print Task Management System.

This module provides test-specific Django settings to ensure
tests run in an isolated, controlled environment.
"""

import os
import tempfile
from .settings import *

# Test database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for faster tests
    }
}

# Disable migrations for faster test execution


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Test-specific settings
DEBUG = False
TESTING = True

# Disable background jobs during tests
BACKGROUND_JOBS_ENABLED = False

# Use a different data directory for tests
TEST_DATA_DIR = tempfile.mkdtemp()
DATA_DIR = TEST_DATA_DIR

# Simplified logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',  # Only show errors during tests
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'ERROR',
    },
}

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use a simple secret key for tests
SECRET_KEY = 'test-secret-key-not-for-production'

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Static files for tests
STATIC_ROOT = os.path.join(TEST_DATA_DIR, 'static')

# Media files for tests
MEDIA_ROOT = os.path.join(TEST_DATA_DIR, 'media')

# Timezone for consistent testing
USE_TZ = True
TIME_ZONE = 'UTC'
