from django.core.management.base import BaseCommand
import uvicorn
import os


class Command(BaseCommand):
    help = 'Run the ASGI server using uvicorn'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='127.0.0.1',
            help='Host to bind the server to (default: 127.0.0.1)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Port to bind the server to (default: 8000)'
        )
        parser.add_argument(
            '--reload',
            action='store_true',
            help='Enable auto-reload for development'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=1,
            help='Number of worker processes (default: 1)'
        )
        parser.add_argument(
            '--log-level',
            default='info',
            choices=['critical', 'error', 'warning', 'info', 'debug', 'trace'],
            help='Log level (default: info)'
        )

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        reload = options['reload']
        workers = options['workers']
        log_level = options['log_level']

        self.stdout.write(
            self.style.SUCCESS(f'Starting ASGI server on {host}:{port}')
        )

        if reload:
            self.stdout.write(self.style.WARNING(
                'Running with auto-reload enabled (development mode)'))

        # Set Django settings module if not already set
        if not os.environ.get('DJANGO_SETTINGS_MODULE'):
            os.environ.setdefault(
                'DJANGO_SETTINGS_MODULE',
                'adhd_print_project.settings')

        try:
            uvicorn.run(
                'adhd_print_project.asgi:application',
                host=host,
                port=port,
                reload=reload,
                workers=workers if not reload else 1,  # Reload mode only works with 1 worker
                log_level=log_level,
                access_log=True
            )
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\nASGI server stopped.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting ASGI server: {e}')
            )
