from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.background_jobs import PeriodicTaskScheduler
from tasks.models import MaintenanceLog
import time


class Command(BaseCommand):
    help = 'Manage background job scheduler for periodic tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'run_maintenance'],
            help='Action to perform on the background job scheduler'
        )
        parser.add_argument(
            '--foreground',
            action='store_true',
            help='Run in foreground (for testing)'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'start':
            self.start_scheduler(options.get('foreground', False))
        elif action == 'stop':
            self.stop_scheduler()
        elif action == 'status':
            self.show_status()
        elif action == 'run_maintenance':
            self.run_maintenance()

    def start_scheduler(self, foreground=False):
        """Start the background job scheduler"""
        try:
            scheduler = PeriodicTaskScheduler()
            scheduler.start()

            self.stdout.write(
                self.style.SUCCESS('Background job scheduler started successfully')
            )

            if foreground:
                self.stdout.write(
                    self.style.WARNING(
                        'Running in foreground mode. Press Ctrl+C to stop.'
                    )
                )
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.stdout.write('\nStopping scheduler...')
                    scheduler.stop()
                    self.stdout.write(
                        self.style.SUCCESS('Background job scheduler stopped')
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to start scheduler: {e}')
            )

    def stop_scheduler(self):
        """Stop the background job scheduler"""
        # This is primarily for demonstration - in practice, the scheduler
        # stops when the Django process stops
        self.stdout.write(
            self.style.WARNING(
                'Background jobs are integrated with Django. '
                'Stop the Django server to stop background jobs.'
            )
        )

    def show_status(self):
        """Show scheduler and recent job status"""
        self.stdout.write(self.style.HTTP_INFO('Background Job Status'))
        self.stdout.write('=' * 50)

        # Show recent maintenance logs
        recent_logs = MaintenanceLog.objects.order_by('-timestamp')[:10]

        if not recent_logs:
            self.stdout.write('No maintenance logs found.')
            return

        self.stdout.write(f'\nRecent Maintenance Runs ({recent_logs.count()}):\n')

        for log in recent_logs:
            status = '✅' if log.success else '❌'
            timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            runtime = f"{log.runtime_seconds:.2f}s"

            self.stdout.write(
                f'{status} {timestamp} - '
                f'Templates: {log.templates_processed}, '
                f'Created: {log.instances_created}, '
                f'Cleaned: {log.instances_cleaned}, '
                f'Expired: {log.templates_cleaned}, '
                f'Runtime: {runtime}'
            )

            if not log.success and log.errors:
                for error in log.errors:
                    self.stdout.write(
                        self.style.ERROR(f'    Error: {error}')
                    )

        # Show next scheduled run
        try:
            # This is a simplified status check
            self.stdout.write('Next scheduled maintenance: Daily at 2:00 AM')
            self.stdout.write(
                f'Current time: {
                    timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not get scheduler info: {e}')
            )

    def run_maintenance(self):
        """Manually run the periodic task maintenance"""
        self.stdout.write('Running periodic task maintenance manually...')

        try:
            from tasks.periodic_utils import nightly_periodic_task_maintenance

            start_time = time.time()
            result = nightly_periodic_task_maintenance()
            runtime = time.time() - start_time

            # Extract stats from the nested structure
            generation_stats = result.get('generation_stats', {})
            cleanup_stats = result.get('cleanup_stats', {})

            templates_processed = 0
            instances_created = 0

            # Count from generation stats
            for template_id, stats in generation_stats.items():
                if isinstance(stats, dict) and 'created_count' in stats:
                    templates_processed += 1
                    instances_created += stats['created_count']

            instances_cleaned = cleanup_stats.get('deleted_instances', 0)
            templates_cleaned = cleanup_stats.get('deleted_expired_templates', 0)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Maintenance completed in {runtime:.2f}s:\n'
                    f'  Templates processed: {templates_processed}\n'
                    f'  Instances created: {instances_created}\n'
                    f'  Instances cleaned: {instances_cleaned}\n'
                    f'  Expired templates cleaned: {templates_cleaned}'
                )
            )

            if result.get('error'):
                self.stdout.write(
                    self.style.ERROR(f'Error encountered: {result["error"]}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to run maintenance: {e}')
            )
