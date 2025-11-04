"""
Management command to test email configuration and send test emails.
This helps verify that email settings are properly configured.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, get_connection
from django.conf import settings
from django.utils import timezone
import sys


class Command(BaseCommand):
    help = 'Test email configuration and send test emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to', 
            type=str, 
            help='Email address to send test email to (not required with --check-only)'
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='ADHD Print Task Manager - Email Configuration Test',
            help='Subject for the test email'
        )
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check email configuration without sending test email'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing email configuration...'))
        
        # Check email configuration
        self.check_email_configuration()
        
        if options['check_only']:
            self.stdout.write(self.style.SUCCESS('Email configuration check completed.'))
            return
        
        # Validate recipient email for sending test
        recipient_email = options.get('to')
        if not recipient_email:
            raise CommandError('--to argument is required when not using --check-only')
        
        subject = options['subject']
        
        try:
            self.send_test_email(recipient_email, subject)
            self.stdout.write(
                self.style.SUCCESS(f'Test email sent successfully to {recipient_email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to send test email: {str(e)}')
            )
            sys.exit(1)

    def check_email_configuration(self):
        """Check and display current email configuration"""
        self.stdout.write('\n=== Email Configuration ===')
        
        config_items = [
            ('EMAIL_BACKEND', settings.EMAIL_BACKEND),
            ('EMAIL_HOST', settings.EMAIL_HOST),
            ('EMAIL_PORT', settings.EMAIL_PORT),
            ('EMAIL_USE_TLS', settings.EMAIL_USE_TLS),
            ('EMAIL_USE_SSL', settings.EMAIL_USE_SSL),
            ('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
            ('EMAIL_HOST_PASSWORD', '***' if settings.EMAIL_HOST_PASSWORD else '(not set)'),
            ('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
        ]
        
        if hasattr(settings, 'EMAIL_TIMEOUT'):
            config_items.append(('EMAIL_TIMEOUT', settings.EMAIL_TIMEOUT))
        
        for key, value in config_items:
            self.stdout.write(f'{key}: {value}')
        
        # Check for common configuration issues
        self.stdout.write('\n=== Configuration Validation ===')
        
        issues = []
        warnings = []
        
        # Check backend
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
            warnings.append('Using console backend - emails will only appear in console')
        elif settings.EMAIL_BACKEND == 'django.core.mail.backends.dummy.EmailBackend':
            warnings.append('Using dummy backend - emails will be silently discarded')
        elif settings.EMAIL_BACKEND == 'django.core.mail.backends.filebased.EmailBackend':
            warnings.append('Using file-based backend - emails will be saved to files')
        
        # Check SMTP configuration
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
            if not settings.EMAIL_HOST:
                issues.append('EMAIL_HOST is not configured')
            if not settings.EMAIL_HOST_USER:
                warnings.append('EMAIL_HOST_USER is not set (may be required for authentication)')
            if not settings.EMAIL_HOST_PASSWORD:
                warnings.append('EMAIL_HOST_PASSWORD is not set (may be required for authentication)')
            if settings.EMAIL_USE_TLS and settings.EMAIL_USE_SSL:
                issues.append('Both EMAIL_USE_TLS and EMAIL_USE_SSL are enabled (should use only one)')
        
        # Check from email
        if not settings.DEFAULT_FROM_EMAIL or settings.DEFAULT_FROM_EMAIL == 'webmaster@localhost':
            warnings.append('DEFAULT_FROM_EMAIL should be set to a proper email address')
        
        # Display issues and warnings
        if issues:
            self.stdout.write(self.style.ERROR('\nConfiguration Issues:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  ❌ {issue}'))
        
        if warnings:
            self.stdout.write(self.style.WARNING('\nConfiguration Warnings:'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'  ⚠️  {warning}'))
        
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS('  ✅ Configuration looks good'))
        
        # Test connection
        self.test_email_connection()

    def test_email_connection(self):
        """Test email backend connection"""
        self.stdout.write('\n=== Connection Test ===')
        
        try:
            connection = get_connection()
            if hasattr(connection, 'open'):
                connection.open()
                self.stdout.write(self.style.SUCCESS('  ✅ Email connection successful'))
                if hasattr(connection, 'close'):
                    connection.close()
            else:
                self.stdout.write(self.style.WARNING('  ℹ️  Backend does not support connection testing'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Email connection failed: {str(e)}'))

    def send_test_email(self, recipient_email, subject):
        """Send a test email"""
        self.stdout.write(f'\n=== Sending Test Email to {recipient_email} ===')
        
        message = f"""
This is a test email from ADHD Print Task Manager.

Email Configuration Test Details:
- Sent at: {timezone.now()}
- Backend: {settings.EMAIL_BACKEND}
- Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
- TLS: {settings.EMAIL_USE_TLS}
- SSL: {settings.EMAIL_USE_SSL}
- From: {settings.DEFAULT_FROM_EMAIL}

If you received this email, your email configuration is working correctly!
"""
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False
        )