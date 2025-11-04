"""
Simplified tests for background job functionality.
Tests only the components that can be easily tested without complex mocking.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date
from tasks.models import Task, MaintenanceLog


class MaintenanceLogTests(TestCase):
    """Test maintenance log functionality."""

    def test_maintenance_log_creation(self):
        """Test creating maintenance log entries."""
        log = MaintenanceLog.objects.create(
            templates_processed=5,
            instances_created=10,
            instances_cleaned=2,
            runtime_seconds=1.5,
            success=True
        )

        self.assertEqual(log.templates_processed, 5)
        self.assertEqual(log.instances_created, 10)
        self.assertTrue(log.success)

    def test_log_string_representation(self):
        """Test log string representation."""
        log = MaintenanceLog.objects.create(
            instances_created=5,
            success=True
        )

        str_repr = str(log)
        self.assertIn('5 instances created', str_repr)
        self.assertIn('✅', str_repr)

    def test_failed_log_representation(self):
        """Test failed log representation."""
        log = MaintenanceLog.objects.create(
            instances_created=0,
            success=False,
            errors=['Test error']
        )

        str_repr = str(log)
        self.assertIn('❌', str_repr)
        self.assertFalse(log.success)
        self.assertEqual(log.errors, ['Test error'])

    def test_log_ordering(self):
        """Test that logs are ordered by timestamp (newest first)."""
        log1 = MaintenanceLog.objects.create(instances_created=1)
        log2 = MaintenanceLog.objects.create(instances_created=2)

        logs = MaintenanceLog.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)


class BackgroundJobsSimpleTests(TestCase):
    """Simple tests for background job related functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_periodic_task_for_maintenance(self):
        """Test creating periodic tasks that would be processed by maintenance."""
        task = Task.objects.create(
            title='Daily Maintenance Task',
            owner=self.user,
            is_periodic=True,
            periodicity_type='daily',
            start_date=date.today()
        )

        self.assertTrue(task.is_periodic)
        self.assertEqual(task.periodicity_type, 'daily')

        # Verify it would be found by maintenance queries
        periodic_tasks = Task.objects.filter(is_periodic=True)
        self.assertIn(task, periodic_tasks)

    def test_periodic_instance_identification(self):
        """Test identifying periodic instances."""
        # Create a periodic template
        template = Task.objects.create(
            title='Template Task',
            owner=self.user,
            is_periodic=True,
            periodicity_type='weekly',
            start_date=date.today()
        )

        # Create an instance (with dynamic approach, we test virtual instances)
        # Since we no longer create physical instances, test the template's virtual instance generation
        from datetime import timedelta
        virtual_instance = template.get_virtual_instance_for_date(date.today())

        # Test identification methods - template should be periodic
        self.assertTrue(template.is_periodic)
        # Virtual instance should not be periodic
        self.assertFalse(virtual_instance.is_periodic)
        # No more physical instances or periodic_parent relationships in dynamic approach
