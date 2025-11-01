"""
Background Job Scheduler for Periodic Task Maintenance

This module sets up and manages background jobs within the Django application,
replacing the need for external cron jobs with an integrated solution.
"""

import logging
import atexit
from datetime import datetime
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from tasks.periodic_utils import nightly_periodic_task_maintenance

# Set up logging
logger = logging.getLogger('background_jobs')


class PeriodicTaskScheduler:
    """Manages background jobs for periodic task maintenance"""

    def __init__(self):
        self.scheduler = None
        self.is_running = False

    def start(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Background scheduler is already running")
            return

        try:
            from django.conf import settings

            # Get schedule configuration from Django settings
            schedule_hour = getattr(settings, 'MAINTENANCE_SCHEDULE_HOUR', 2)
            schedule_minute = getattr(settings, 'MAINTENANCE_SCHEDULE_MINUTE', 0)

            # Initialize the scheduler
            self.scheduler = BackgroundScheduler(
                timezone=timezone.get_current_timezone())

            # Schedule the nightly maintenance job
            self.scheduler.add_job(
                func=self._run_maintenance,
                trigger=CronTrigger(hour=schedule_hour, minute=schedule_minute),
                id='nightly_periodic_maintenance',
                name='Nightly Periodic Task Maintenance',
                replace_existing=True
            )

            # Add job event listeners
            self.scheduler.add_listener(
                self._job_executed_listener,
                EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
            )

            self.scheduler.start()
            self.is_running = True

            logger.info("Background scheduler started successfully")

            # Register shutdown handler
            atexit.register(self.shutdown)

        except Exception as e:
            logger.error(f"Failed to start background scheduler: {e}")
            raise

    def shutdown(self):
        """Shutdown the background scheduler"""
        if self.scheduler and self.is_running:
            try:
                self.scheduler.shutdown(wait=True)
                self.is_running = False
                logger.info("Background scheduler shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down scheduler: {e}")

    def _run_maintenance(self):
        """Execute the nightly maintenance job"""
        try:
            logger.info("Starting nightly periodic task maintenance")

            start_time = timezone.now()
            stats = nightly_periodic_task_maintenance()
            end_time = timezone.now()

            # Log successful completion
            gen_stats = stats.get('generation_stats', {})
            cleanup_stats = stats.get('cleanup_stats', {})

            logger.info(
                f"Nightly maintenance completed successfully. "
                f"Templates processed: {gen_stats.get('processed_templates', 0)}, "
                f"Instances created: {gen_stats.get('total_instances_created', 0)}, "
                f"Old instances cleaned: {cleanup_stats.get('deleted_instances', 0)}, "
                f"Runtime: {(end_time - start_time).total_seconds():.2f}s"
            )

            # Store stats for monitoring
            self._store_maintenance_stats(stats)

        except Exception as e:
            logger.error(f"Nightly maintenance failed: {e}", exc_info=True)
            raise

    def _job_executed_listener(self, event):
        """Handle job execution events"""
        if event.exception:
            logger.error(
                f"Job {event.job_id} failed: {event.exception}",
                exc_info=event.traceback
            )
        else:
            logger.info(f"Job {event.job_id} executed successfully")

    def _store_maintenance_stats(self, stats):
        """Store maintenance statistics for monitoring"""
        try:
            from .models import MaintenanceLog

            # Extract stats from nested structure
            generation_stats = stats.get('generation_stats', {})
            cleanup_stats = stats.get('cleanup_stats', {})

            # Calculate error count
            errors = generation_stats.get('errors', [])
            error_messages = [
                err.get(
                    'error',
                    str(err)) if isinstance(
                    err,
                    dict) else str(err) for err in errors]

            MaintenanceLog.objects.create(
                timestamp=stats.get('timestamp', timezone.now()),
                templates_processed=generation_stats.get('processed_templates', 0),
                instances_created=generation_stats.get('total_instances_created', 0),
                instances_cleaned=cleanup_stats.get('deleted_instances', 0),
                templates_cleaned=cleanup_stats.get('deleted_expired_templates', 0),
                runtime_seconds=stats.get('total_runtime_seconds', 0),
                errors=error_messages,
                success=len(errors) == 0
            )
        except Exception as e:
            logger.warning(f"Failed to store maintenance stats: {e}")

    def get_job_status(self):
        """Get current job status"""
        if not self.scheduler or not self.is_running:
            return {
                'scheduler_running': False,
                'jobs': []
            }

        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': next_run.isoformat() if next_run else None,
                'trigger': str(job.trigger)
            })

        return {
            'scheduler_running': self.is_running,
            'jobs': jobs
        }

    def run_maintenance_now(self):
        """Manually trigger maintenance job"""
        if not self.scheduler or not self.is_running:
            raise RuntimeError("Scheduler is not running")

        logger.info("Manual maintenance job triggered")
        self.scheduler.add_job(
            func=self._run_maintenance,
            trigger='date',  # Run once, immediately
            id='manual_maintenance',
            name='Manual Periodic Task Maintenance',
            replace_existing=True
        )


# Global scheduler instance
_scheduler = PeriodicTaskScheduler()


def start_background_jobs():
    """Start the background job scheduler"""
    _scheduler.start()


def shutdown_background_jobs():
    """Shutdown the background job scheduler"""
    _scheduler.shutdown()


def get_scheduler_status():
    """Get current scheduler status"""
    return _scheduler.get_job_status()


def trigger_manual_maintenance():
    """Manually trigger maintenance"""
    return _scheduler.run_maintenance_now()
