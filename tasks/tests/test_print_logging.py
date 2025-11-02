from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from tasks.models import Task, PrintLog, UserProfile
import json


class PrintLogTests(TestCase):
    """Test print logging functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='A test task for print logging',
            owner=self.user
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_print_log_model_creation(self):
        """Test PrintLog model creation and methods"""
        print_log = PrintLog.objects.create(
            user=self.user,
            task=self.task,
            print_method='server',
            print_type='single_task',
            success=True,
            tasks_attempted=1,
            tasks_successful=1,
            duration_ms=1500
        )
        
        self.assertEqual(print_log.user, self.user)
        self.assertEqual(print_log.task, self.task)
        self.assertEqual(print_log.print_method, 'server')
        self.assertEqual(print_log.print_type, 'single_task')
        self.assertTrue(print_log.success)
        self.assertEqual(print_log.tasks_attempted, 1)
        self.assertEqual(print_log.tasks_successful, 1)
        self.assertEqual(print_log.duration_ms, 1500)
        self.assertEqual(print_log.success_rate(), 100.0)
        
        # Test string representation
        str_repr = str(print_log)
        self.assertIn('✅', str_repr)
        self.assertIn('Server-based Printing', str_repr)
        self.assertIn('Single Task', str_repr)
        self.assertIn('Test Task', str_repr)

    def test_print_log_success_rate_calculation(self):
        """Test success rate calculation for various scenarios"""
        # 100% success
        log1 = PrintLog.objects.create(
            user=self.user,
            print_method='server',
            print_type='single_task',
            success=True,
            tasks_attempted=5,
            tasks_successful=5
        )
        self.assertEqual(log1.success_rate(), 100.0)
        
        # 80% success
        log2 = PrintLog.objects.create(
            user=self.user,
            print_method='server',
            print_type='task_hierarchy',
            success=False,
            tasks_attempted=5,
            tasks_successful=4
        )
        self.assertEqual(log2.success_rate(), 80.0)
        
        # 0% success
        log3 = PrintLog.objects.create(
            user=self.user,
            print_method='local',
            print_type='single_task',
            success=False,
            tasks_attempted=3,
            tasks_successful=0
        )
        self.assertEqual(log3.success_rate(), 0.0)
        
        # Edge case: 0 attempts
        log4 = PrintLog.objects.create(
            user=self.user,
            print_method='server',
            print_type='todays_tasks',
            success=True,
            tasks_attempted=0,
            tasks_successful=0
        )
        self.assertEqual(log4.success_rate(), 0.0)

    def test_single_task_print_creates_log(self):
        """Test that printing a single task creates a log entry"""
        initial_count = PrintLog.objects.count()
        
        response = self.client.post(
            reverse('task_print', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that a log entry was created
        self.assertEqual(PrintLog.objects.count(), initial_count + 1)
        
        # Check the log entry details
        log_entry = PrintLog.objects.latest('timestamp')
        self.assertEqual(log_entry.user, self.user)
        self.assertEqual(log_entry.task, self.task)
        self.assertEqual(log_entry.print_type, 'single_task')
        self.assertIsNotNone(log_entry.duration_ms)
        self.assertGreater(log_entry.duration_ms or 0, -1)  # Handle None case

    def test_local_printing_handled_client_side_log(self):
        """Test that local printing works correctly and logs appropriately"""
        # Set user profile to local printing (which is now the default)
        profile = self.user.profile
        profile.printing_method = 'local'  # This is now the default anyway
        profile.save()
        
        initial_count = PrintLog.objects.count()
        
        response = self.client.post(
            reverse('task_print', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check response indicates local printing succeeded (new behavior)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['print_method'], 'local')
        # use_client_side field may or may not be present depending on implementation
        
        # Check that a log entry was created
        self.assertEqual(PrintLog.objects.count(), initial_count + 1)
        
        # Check the log entry details
        log_entry = PrintLog.objects.latest('timestamp')
        self.assertEqual(log_entry.user, self.user)
        self.assertEqual(log_entry.task, self.task)
        self.assertEqual(log_entry.print_method, 'local')
        self.assertTrue(log_entry.success)  # Local printing now works
        self.assertEqual(log_entry.tasks_successful, 1)  # Should be 1 since it succeeded
        # No error message expected since printing works now

    def test_task_hierarchy_print_log(self):
        """Test logging for task with subtasks (now prints only single task)"""
        # Create a subtask
        subtask = Task.objects.create(
            title='Subtask',
            description='Subtask description',
            urgency='normal',
            owner=self.user,
            parent=self.task
        )
        
        # Set user to server printing and enable it
        profile = self.user.profile
        profile.printing_method = 'server'
        profile.server_printing_enabled = True  # Need to enable server printing
        profile.save()
        
        initial_count = PrintLog.objects.count()
        
        response = self.client.post(
            reverse('task_print', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check that a log entry was created
        self.assertEqual(PrintLog.objects.count(), initial_count + 1)
        
        # Check the log entry details - now prints single task only
        log_entry = PrintLog.objects.latest('timestamp')
        self.assertEqual(log_entry.print_type, 'single_task')  # Changed from 'task_hierarchy'
        self.assertEqual(log_entry.tasks_attempted, 1)  # Only main task, no subtasks
        # includes_subtasks indicates if the task HAS subtasks, not if they were printed
        self.assertIn('includes_subtasks', log_entry.print_settings)
        self.assertTrue(log_entry.print_settings['includes_subtasks'])  # Task has subtasks
        self.assertEqual(log_entry.print_settings['subtask_count'], 1)  # But only 1 subtask exists

    def test_print_log_admin_display_methods(self):
        """Test admin display methods work correctly"""
        # Create log with various settings
        print_log = PrintLog.objects.create(
            user=self.user,
            task=self.task,
            print_method='server',
            print_type='todays_tasks',
            success=True,
            tasks_attempted=5,
            tasks_successful=4,
            duration_ms=2500,
            print_settings={'use_graphics': True, 'paper_size': 'A4'},
            printer_config={'ip': '192.168.1.100', 'port': 9100}
        )
        
        # Test success rate calculation
        self.assertEqual(print_log.success_rate(), 80.0)
        
        # Verify settings and config are stored properly
        self.assertIn('use_graphics', print_log.print_settings)
        self.assertIn('ip', print_log.printer_config)

    def test_print_error_handling_creates_log(self):
        """Test that print errors are properly logged"""
        # Delete the task to force an error
        task_id = self.task.id
        self.task.delete()
        
        initial_count = PrintLog.objects.count()
        
        response = self.client.post(
            reverse('task_print', args=[task_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Should return 404
        self.assertEqual(response.status_code, 404)
        
        # No log should be created for 404 errors (task not found)
        # The view doesn't get to the logging part
        self.assertEqual(PrintLog.objects.count(), initial_count)

    def test_print_log_ordering(self):
        """Test that print logs are ordered by timestamp descending"""
        # Create multiple log entries
        log1 = PrintLog.objects.create(
            user=self.user,
            print_method='server',
            print_type='single_task',
            success=True
        )
        
        log2 = PrintLog.objects.create(
            user=self.user,
            print_method='local',
            print_type='todays_tasks',
            success=False
        )
        
        # Get all logs and verify ordering
        logs = list(PrintLog.objects.all())
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)

    def test_print_log_str_method_with_no_task(self):
        """Test string representation when no task is associated"""
        print_log = PrintLog.objects.create(
            user=self.user,
            print_method='server',
            print_type='todays_tasks',
            success=True,
            tasks_attempted=3,
            tasks_successful=3
        )
        
        str_repr = str(print_log)
        self.assertIn('✅', str_repr)
        self.assertIn('Server-based Printing', str_repr)
        self.assertIn("Today's Tasks", str_repr)
        # Should not have task name since task is None
        self.assertNotIn(' - ', str_repr)

    def test_server_printing_not_enabled_log(self):
        """Test that server printing fails when not enabled for user"""
        # Set user profile to server printing but don't enable it
        profile = self.user.profile
        profile.printing_method = 'server'
        profile.server_printing_enabled = False  # Explicitly disable server printing
        profile.save()
        
        initial_count = PrintLog.objects.count()
        
        response = self.client.post(
            reverse('task_print', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        
        # Check response indicates server printing not enabled
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['print_method'], 'server')
        self.assertTrue(response_data.get('fallback_to_local', False))
        self.assertIn('Server printing not enabled', response_data['message'])
        
        # Check that a log entry was created
        self.assertEqual(PrintLog.objects.count(), initial_count + 1)
        
        # Check the log entry details
        log_entry = PrintLog.objects.latest('timestamp')
        self.assertEqual(log_entry.user, self.user)
        self.assertFalse(log_entry.success)
        self.assertEqual(log_entry.print_method, 'server')
        self.assertEqual(log_entry.task, self.task)
        self.assertEqual(log_entry.print_type, 'single_task')
        self.assertIsNotNone(log_entry.duration_ms)
        self.assertIn('Server printing not enabled', log_entry.error_message)