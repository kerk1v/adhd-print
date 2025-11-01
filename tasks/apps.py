from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class TasksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tasks'

    def ready(self):
        """Initialize background jobs when Django starts"""
        # Only start background jobs in the main process
        # This prevents duplicate jobs in development when using runserver
        import os
        from django.conf import settings

        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        # Check if background jobs are enabled
        if not getattr(settings, 'BACKGROUND_JOBS_ENABLED', True):
            logger.info("Background jobs are disabled by configuration")
            return

        try:
            from .background_jobs import PeriodicTaskScheduler
            scheduler = PeriodicTaskScheduler()
            scheduler.start()
            logger.info("Background job scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start background job scheduler: {e}")
            # Don't raise the exception to prevent Django from failing to start
