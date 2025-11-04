"""
Tests for periodic task functionality.
Fixed to match the actual Task model structure.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from tasks.models import Task


class PeriodicTaskModelTests(TestCase):
    """Test periodic task model functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_periodic_task_creation(self):
        """Test creating a periodic task."""
        task = Task.objects.create(
            title='Weekly Meeting',
            description='Team standup meeting',
            is_periodic=True,
            periodicity_type='weekly',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            owner=self.user
        )

        self.assertTrue(task.is_periodic)
        self.assertEqual(task.periodicity_type, 'weekly')
        self.assertEqual(task.start_date, date(2025, 1, 1))
        self.assertEqual(task.end_date, date(2025, 12, 31))

    def test_next_occurrence_daily(self):
        """Test next occurrence calculation for daily tasks."""
        task = Task.objects.create(
            title='Daily Standup',
            owner=self.user,
            is_periodic=True,
            periodicity_type='daily',
            start_date=date(2025, 1, 1)
        )

        # Test from start date
        next_occurrence = task.get_next_occurrence(date(2025, 1, 1))
        self.assertEqual(next_occurrence, date(2025, 1, 1))

        # Test from future date
        next_occurrence = task.get_next_occurrence(date(2025, 1, 5))
        self.assertEqual(next_occurrence, date(2025, 1, 5))

    def test_next_occurrence_weekly(self):
        """Test next occurrence calculation for weekly tasks."""
        task = Task.objects.create(
            title='Weekly Review',
            owner=self.user,
            is_periodic=True,
            periodicity_type='weekly',
            start_date=date(2025, 1, 6)  # Monday
        )

        # Test next occurrence
        next_occurrence = task.get_next_occurrence(date(2025, 1, 6))
        self.assertEqual(next_occurrence, date(2025, 1, 6))

        # Test from middle of week
        next_occurrence = task.get_next_occurrence(date(2025, 1, 8))
        self.assertEqual(next_occurrence, date(2025, 1, 13))  # Next Monday

    def test_next_occurrence_monthly(self):
        """Test next occurrence calculation for monthly tasks."""
        task = Task.objects.create(
            title='Monthly Report',
            owner=self.user,
            is_periodic=True,
            periodicity_type='monthly',
            start_date=date(2025, 1, 15)  # 15th of the month
        )

        # Test next occurrence
        next_occurrence = task.get_next_occurrence(date(2025, 1, 15))
        self.assertEqual(next_occurrence, date(2025, 1, 15))

        # Test from later in month
        next_occurrence = task.get_next_occurrence(date(2025, 1, 20))
        self.assertEqual(next_occurrence, date(2025, 2, 15))

    def test_next_occurrence_with_end_date(self):
        """Test that tasks don't generate occurrences past end_date."""
        task = Task.objects.create(
            title='Limited Task',
            owner=self.user,
            is_periodic=True,
            periodicity_type='daily',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 10)
        )

        # Should return None after end date
        next_occurrence = task.get_next_occurrence(date(2025, 1, 15))
        self.assertIsNone(next_occurrence)

        # Should work before end date
        next_occurrence = task.get_next_occurrence(date(2025, 1, 5))
        self.assertEqual(next_occurrence, date(2025, 1, 5))


class PeriodicInstanceGenerationTests(TestCase):
    """Test generation of periodic task instances."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_generate_instances_daily_task(self):
        """Test generating instances for daily task."""
        task = Task.objects.create(
            title='Daily Backup',
            description='Daily system backup',
            owner=self.user,
            is_periodic=True,
            periodicity_type='daily',
            start_date=date(2025, 1, 1),
            urgency='urgent'
        )

        # Test dynamic generation instead of physical instances
        # Generate virtual instances for the next few days
        from datetime import timedelta
        test_date = date(2025, 1, 1)
        occurrence_dates = task.get_occurrences_in_range(
            test_date, 
            test_date + timedelta(days=3)
        )

        # Verify the occurrence dates are generated correctly
        self.assertEqual(len(occurrence_dates), 4)  # 4 days including start date
        
        # Test virtual instance generation for each occurrence
        for i, occurrence_date in enumerate(occurrence_dates):
            virtual_task = task.get_virtual_instance_for_date(occurrence_date)
            self.assertIsNotNone(virtual_task)
            self.assertEqual(virtual_task.title, task.title)
            self.assertEqual(virtual_task.description, task.description)
            self.assertEqual(virtual_task.owner, task.owner)
            self.assertEqual(virtual_task.urgency, task.urgency)
            # Virtual instances should not be periodic themselves
            self.assertFalse(virtual_task.is_periodic)


class BasicPeriodicTests(TestCase):
    """Basic tests for periodic functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_simple_periodic_task(self):
        """Test basic periodic task creation."""
        task = Task.objects.create(
            title='Simple Task',
            owner=self.user,
            is_periodic=True,
            periodicity_type='daily',
            start_date=date.today()
        )

        self.assertTrue(task.is_periodic)
        self.assertEqual(task.periodicity_type, 'daily')
        self.assertIsNotNone(task.start_date)
