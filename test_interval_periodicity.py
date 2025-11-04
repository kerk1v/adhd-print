"""
Tests for new interval-based periodicity functionality
"""

import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from tasks.models import Task


class IntervalPeriodicityTestCase(TestCase):
    """Test cases for interval-based periodicity (every X days/weeks/months)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.base_date = datetime.date(2025, 1, 1)  # January 1, 2025 (Wednesday)
    
    def test_every_x_days_basic(self):
        """Test every X days periodicity"""
        task = Task.objects.create(
            title='Every 3 Days Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail={'interval': 3}
        )
        
        # Test dates that should occur
        self.assertTrue(task._should_occur_on_date(self.base_date))  # Day 0
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=3)))  # Day 3
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=6)))  # Day 6
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=9)))  # Day 9
        
        # Test dates that should not occur
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(days=1)))  # Day 1
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(days=2)))  # Day 2
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(days=4)))  # Day 4
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(days=5)))  # Day 5
        self.assertFalse(task._should_occur_on_date(self.base_date - datetime.timedelta(days=1)))  # Before start
    
    def test_every_x_weeks_basic(self):
        """Test every X weeks periodicity"""
        task = Task.objects.create(
            title='Every 2 Weeks Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,  # Wednesday
            periodicity_type='every_x_weeks',
            periodicity_detail={'interval': 2}
        )
        
        # Test dates that should occur (same weekday, every 2 weeks)
        self.assertTrue(task._should_occur_on_date(self.base_date))  # Week 0, Wednesday
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(weeks=2)))  # Week 2, Wednesday
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(weeks=4)))  # Week 4, Wednesday
        
        # Test dates that should not occur
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(weeks=1)))  # Week 1, Wednesday (wrong interval)
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(weeks=3)))  # Week 3, Wednesday (wrong interval)
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(days=1)))  # Thursday (wrong weekday)
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(weeks=2, days=1)))  # Week 2, Thursday (wrong weekday)
    
    def test_every_x_months_basic(self):
        """Test every X months periodicity"""
        task = Task.objects.create(
            title='Every 3 Months Task',
            owner=self.user,
            is_periodic=True,
            start_date=datetime.date(2025, 1, 15),  # January 15, 2025
            periodicity_type='every_x_months',
            periodicity_detail={'interval': 3}
        )
        
        # Test dates that should occur
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 1, 15)))  # Month 0
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 4, 15)))  # Month 3
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 7, 15)))  # Month 6
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 10, 15)))  # Month 9
        self.assertTrue(task._should_occur_on_date(datetime.date(2026, 1, 15)))  # Month 12
        
        # Test dates that should not occur
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 2, 15)))  # Month 1 (wrong interval)
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 3, 15)))  # Month 2 (wrong interval)
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 5, 15)))  # Month 4 (wrong interval)
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 4, 14)))  # April 14 (wrong day)
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 4, 16)))  # April 16 (wrong day)
    
    def test_every_x_months_end_of_month_handling(self):
        """Test every X months with month-end date handling"""
        # Task starting on January 31
        task = Task.objects.create(
            title='Monthly End Task',
            owner=self.user,
            is_periodic=True,
            start_date=datetime.date(2025, 1, 31),  # January 31, 2025
            periodicity_type='every_x_months',
            periodicity_detail={'interval': 1}
        )
        
        # January 31 should work (original date)
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 1, 31)))
        
        # February only has 28 days in 2025, so should occur on Feb 28
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 2, 28)))
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 2, 27)))
        
        # March 31 should work (has 31 days)
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 3, 31)))
        
        # April only has 30 days, so should occur on April 30
        self.assertTrue(task._should_occur_on_date(datetime.date(2025, 4, 30)))
        self.assertFalse(task._should_occur_on_date(datetime.date(2025, 4, 29)))
    
    def test_every_x_months_leap_year_handling(self):
        """Test every X months with leap year February"""
        # Task starting on January 31, leap year scenario
        task = Task.objects.create(
            title='Leap Year Task',
            owner=self.user,
            is_periodic=True,
            start_date=datetime.date(2024, 1, 31),  # January 31, 2024 (leap year)
            periodicity_type='every_x_months',
            periodicity_detail={'interval': 1}
        )
        
        # February 2024 has 29 days (leap year), so should occur on Feb 29
        self.assertTrue(task._should_occur_on_date(datetime.date(2024, 2, 29)))
        self.assertFalse(task._should_occur_on_date(datetime.date(2024, 2, 28)))
    
    def test_get_occurrences_in_range_every_x_days(self):
        """Test getting occurrences for every X days"""
        task = Task.objects.create(
            title='Every 5 Days Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail={'interval': 5}
        )
        
        # Get occurrences for 20 days
        end_date = self.base_date + datetime.timedelta(days=20)
        occurrences = task.get_occurrences_in_range(self.base_date, end_date)
        
        expected_dates = [
            self.base_date,  # Day 0
            self.base_date + datetime.timedelta(days=5),  # Day 5
            self.base_date + datetime.timedelta(days=10),  # Day 10
            self.base_date + datetime.timedelta(days=15),  # Day 15
            self.base_date + datetime.timedelta(days=20),  # Day 20
        ]
        
        self.assertEqual(len(occurrences), 5)
        self.assertEqual(occurrences, expected_dates)
    
    def test_get_occurrences_in_range_every_x_weeks(self):
        """Test getting occurrences for every X weeks"""
        task = Task.objects.create(
            title='Every 3 Weeks Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_weeks',
            periodicity_detail={'interval': 3}
        )
        
        # Get occurrences for 10 weeks
        end_date = self.base_date + datetime.timedelta(weeks=10)
        occurrences = task.get_occurrences_in_range(self.base_date, end_date)
        
        expected_dates = [
            self.base_date,  # Week 0
            self.base_date + datetime.timedelta(weeks=3),  # Week 3
            self.base_date + datetime.timedelta(weeks=6),  # Week 6
            self.base_date + datetime.timedelta(weeks=9),  # Week 9
        ]
        
        self.assertEqual(len(occurrences), 4)
        self.assertEqual(occurrences, expected_dates)
    
    def test_get_occurrences_in_range_every_x_months(self):
        """Test getting occurrences for every X months"""
        task = Task.objects.create(
            title='Every 4 Months Task',
            owner=self.user,
            is_periodic=True,
            start_date=datetime.date(2025, 1, 10),
            periodicity_type='every_x_months',
            periodicity_detail={'interval': 4}
        )
        
        # Get occurrences for 1 year
        start_date = datetime.date(2025, 1, 10)
        end_date = datetime.date(2026, 1, 10)
        occurrences = task.get_occurrences_in_range(start_date, end_date)
        
        expected_dates = [
            datetime.date(2025, 1, 10),  # Month 0
            datetime.date(2025, 5, 10),  # Month 4
            datetime.date(2025, 9, 10),  # Month 8
            datetime.date(2026, 1, 10),  # Month 12
        ]
        
        self.assertEqual(len(occurrences), 4)
        self.assertEqual(occurrences, expected_dates)
    
    def test_virtual_instance_creation_interval_types(self):
        """Test that virtual instances are created correctly for interval types"""
        task = Task.objects.create(
            title='Every 7 Days Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail={'interval': 7}
        )
        
        # Create virtual instance
        occurrence_date = self.base_date + datetime.timedelta(days=7)
        virtual_instance = task.get_virtual_instance_for_date(occurrence_date)
        
        self.assertIsNotNone(virtual_instance)
        self.assertEqual(virtual_instance.title, task.title)
        self.assertEqual(virtual_instance.owner, task.owner)
        self.assertEqual(virtual_instance.due_date.date(), occurrence_date)
        self.assertTrue(hasattr(virtual_instance, '_template_task'))
        self.assertEqual(virtual_instance._template_task, task)
    
    def test_interval_validation_edge_cases(self):
        """Test edge cases for interval validation"""
        # Test interval of 1 (should work like daily/weekly/monthly)
        task_days = Task.objects.create(
            title='Every 1 Day Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail={'interval': 1}
        )
        
        # Should occur every day
        self.assertTrue(task_days._should_occur_on_date(self.base_date))
        self.assertTrue(task_days._should_occur_on_date(self.base_date + datetime.timedelta(days=1)))
        self.assertTrue(task_days._should_occur_on_date(self.base_date + datetime.timedelta(days=2)))
        
        # Test large interval
        task_large = Task.objects.create(
            title='Every 100 Days Task',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail={'interval': 100}
        )
        
        # Should only occur every 100 days
        self.assertTrue(task_large._should_occur_on_date(self.base_date))
        self.assertFalse(task_large._should_occur_on_date(self.base_date + datetime.timedelta(days=99)))
        self.assertTrue(task_large._should_occur_on_date(self.base_date + datetime.timedelta(days=100)))
        self.assertFalse(task_large._should_occur_on_date(self.base_date + datetime.timedelta(days=199)))
        self.assertTrue(task_large._should_occur_on_date(self.base_date + datetime.timedelta(days=200)))
    
    def test_end_date_handling_with_intervals(self):
        """Test that end_date is respected for interval periodicities"""
        task = Task.objects.create(
            title='Every 2 Days Task with End Date',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            end_date=self.base_date + datetime.timedelta(days=10),
            periodicity_type='every_x_days',
            periodicity_detail={'interval': 2}
        )
        
        # Should occur within the range
        self.assertTrue(task._should_occur_on_date(self.base_date))  # Day 0
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=2)))  # Day 2
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=10)))  # Day 10 (end date)
        
        # Should not occur after end date
        self.assertFalse(task._should_occur_on_date(self.base_date + datetime.timedelta(days=12)))  # Day 12 (after end)
    
    def test_default_interval_handling(self):
        """Test that missing interval defaults to 1"""
        task = Task.objects.create(
            title='Task without interval detail',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail={}  # No interval specified
        )
        
        # Should default to interval of 1 (daily)
        self.assertTrue(task._should_occur_on_date(self.base_date))
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=1)))
        self.assertTrue(task._should_occur_on_date(self.base_date + datetime.timedelta(days=2)))
        
        # Test with None periodicity_detail
        task2 = Task.objects.create(
            title='Task with None periodicity detail',
            owner=self.user,
            is_periodic=True,
            start_date=self.base_date,
            periodicity_type='every_x_days',
            periodicity_detail=None
        )
        
        # Should also default to interval of 1
        self.assertTrue(task2._should_occur_on_date(self.base_date))
        self.assertTrue(task2._should_occur_on_date(self.base_date + datetime.timedelta(days=1)))