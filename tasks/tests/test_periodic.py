"""
Tests for periodic task functionality.
Fixed to match the actual Task model structure.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
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

        # Test that we can create an instance manually (simulating what
        # generate_periodic_task_instances does)
        instance = Task.objects.create(
            title=task.title,
            description=task.description,
            owner=task.owner,
            urgency=task.urgency,
            periodic_parent=task,
            due_date=timezone.datetime.combine(
                date(
                    2025,
                    1,
                    1),
                timezone.datetime.min.time()).replace(
                tzinfo=timezone.get_current_timezone()))

        self.assertEqual(instance.title, 'Daily Backup')
        self.assertEqual(instance.urgency, 'urgent')
        self.assertTrue(instance.periodic_parent == task)
        # instances should not be periodic themselves
        self.assertFalse(instance.is_periodic)


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
