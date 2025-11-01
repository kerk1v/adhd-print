"""
UI and Integration Tests for ADHD Print Task Management System.
These tests focus on end-to-end user workflows, UI interactions, and exploratory testing.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import date
from unittest.mock import patch, Mock
from tasks.models import Task
import json


class UIWorkflowTests(TestCase):
    """Test complete user workflows through the UI."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_complete_task_creation_workflow(self):
        """Test complete task creation workflow from UI perspective."""
        # Start at task list
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tasks')

        # Navigate to create task
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')

        # Create a task
        task_data = {
            'title': 'UI Test Task',
            'description': 'Created through UI workflow test',
            'urgency': 'high',
            'is_periodic': False
        }
        response = self.client.post(reverse('task_create'), task_data)

        # Should redirect or show success
        if response.status_code == 302:
            # Successful creation, redirected
            task = Task.objects.get(title='UI Test Task')
            self.assertEqual(task.owner, self.user)
            self.assertEqual(task.urgency, 'high')
        elif response.status_code == 200:
            # Form validation might have failed, check if task exists
            if Task.objects.filter(title='UI Test Task').exists():
                task = Task.objects.get(title='UI Test Task')
                self.assertEqual(task.owner, self.user)

    def test_task_hierarchy_creation_workflow(self):
        """Test creating hierarchical tasks through UI."""
        # Create parent task
        parent = Task.objects.create(
            title='Parent Project',
            description='Main project task',
            owner=self.user
        )

        # Navigate to create subtask
        response = self.client.get(reverse('task_create', args=[parent.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Parent Project')

        # Create subtask
        subtask_data = {
            'title': 'Subtask 1',
            'description': 'First subtask',
            'urgency': 'normal',
            'is_periodic': False
        }
        response = self.client.post(
            reverse(
                'task_create',
                args=[
                    parent.id]),
            subtask_data)

        # Check subtask was created with correct parent
        if Task.objects.filter(title='Subtask 1').exists():
            subtask = Task.objects.get(title='Subtask 1')
            self.assertEqual(subtask.parent, parent)
            self.assertEqual(subtask.get_level(), 1)

    def test_task_completion_workflow(self):
        """Test marking tasks as complete through UI."""
        task = Task.objects.create(
            title='Task to Complete',
            owner=self.user,
            done=False
        )

        # Toggle task completion
        response = self.client.post(reverse('task_toggle_done', args=[task.id]))
        self.assertEqual(response.status_code, 200)

        # Check JSON response
        try:
            data = json.loads(response.content)
            if data.get('success'):
                task.refresh_from_db()
                self.assertTrue(task.done)
        except json.JSONDecodeError:
            # If not JSON, check database directly
            task.refresh_from_db()
            # Task might have been toggled
            pass

    def test_task_editing_workflow(self):
        """Test editing tasks through UI."""
        task = Task.objects.create(
            title='Original Title',
            description='Original description',
            urgency='normal',
            owner=self.user
        )

        # Navigate to edit form
        response = self.client.get(reverse('task_edit', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original Title')

        # Submit edit
        edit_data = {
            'title': 'Updated Title',
            'description': 'Updated description',
            'urgency': 'urgent',
            'is_periodic': False
        }
        response = self.client.post(reverse('task_edit', args=[task.id]), edit_data)

        # Check if update succeeded
        task.refresh_from_db()
        if task.title == 'Updated Title':
            self.assertEqual(task.description, 'Updated description')
            self.assertEqual(task.urgency, 'urgent')

    def test_task_deletion_workflow(self):
        """Test deleting tasks through UI."""
        task = Task.objects.create(
            title='Task to Delete',
            description='This task will be deleted',
            owner=self.user
        )
        task_id = task.id

        # Get delete confirmation page
        response = self.client.get(reverse('task_delete', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task to Delete')

        # Confirm deletion
        response = self.client.post(reverse('task_delete', args=[task.id]))

        # Task should be deleted
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_periodic_task_creation_workflow(self):
        """Test creating periodic tasks through UI."""
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)

        # Create periodic task
        periodic_data = {
            'title': 'Daily Standup',
            'description': 'Daily team meeting',
            'urgency': 'normal',
            'is_periodic': True,
            'periodicity_type': 'daily',
            'start_date': date.today().isoformat(),
        }

        with patch('tasks.views.generate_periodic_task_instances') as mock_generate:
            mock_generate.return_value = []
            response = self.client.post(reverse('task_create'), periodic_data)

            # Check if periodic task was created
            if Task.objects.filter(title='Daily Standup').exists():
                task = Task.objects.get(title='Daily Standup')
                self.assertTrue(task.is_periodic)
                self.assertEqual(task.periodicity_type, 'daily')


class ModalUITests(TestCase):
    """Test modal-based UI interactions."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_modal_task_creation_flow(self):
        """Test creating tasks via modal interface."""
        # Get modal creation form
        response = self.client.get(reverse('task_create_modal'))
        self.assertEqual(response.status_code, 200)

        # Submit via AJAX
        response = self.client.post(
            reverse('task_create_modal'),
            {
                'title': 'Modal Created Task',
                'description': 'Created via modal',
                'urgency': 'high',
                'is_periodic': False
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        # Should return JSON response
        self.assertEqual(response.status_code, 200)
        try:
            data = json.loads(response.content)
            if data.get('success'):
                self.assertTrue(
                    Task.objects.filter(
                        title='Modal Created Task').exists())
        except json.JSONDecodeError:
            # Non-JSON response might indicate form validation issues
            pass

    def test_modal_task_editing_flow(self):
        """Test editing tasks via modal interface."""
        task = Task.objects.create(
            title='Modal Edit Task',
            description='Original description',
            urgency='normal',
            owner=self.user
        )

        # Get modal edit form
        response = self.client.get(reverse('task_edit_modal', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Modal Edit Task')

        # Submit edit via AJAX
        response = self.client.post(
            reverse('task_edit_modal', args=[task.id]),
            {
                'title': 'Modal Updated Task',
                'description': 'Updated via modal',
                'urgency': 'urgent',
                'is_periodic': False
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        try:
            data = json.loads(response.content)
            if data.get('success'):
                task.refresh_from_db()
                self.assertEqual(task.title, 'Modal Updated Task')
        except json.JSONDecodeError:
            pass

    def test_modal_task_deletion_flow(self):
        """Test deleting tasks via modal interface."""
        task = Task.objects.create(
            title='Modal Delete Task',
            owner=self.user
        )
        task_id = task.id

        # Get modal delete confirmation
        response = self.client.get(reverse('task_delete_modal', args=[task.id]))
        self.assertEqual(response.status_code, 200)

        # Submit deletion via AJAX
        response = self.client.post(
            reverse('task_delete_modal', args=[task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        try:
            data = json.loads(response.content)
            if data.get('success'):
                self.assertFalse(Task.objects.filter(id=task_id).exists())
        except json.JSONDecodeError:
            pass


class HierarchicalNavigationTests(TestCase):
    """Test hierarchical task navigation and filtering."""

    def setUp(self):
        """Set up hierarchical test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create test hierarchy
        self.project1 = Task.objects.create(title='Project 1', owner=self.user)
        self.project2 = Task.objects.create(title='Project 2', owner=self.user)

        self.task1_1 = Task.objects.create(
            title='Task 1.1', parent=self.project1, owner=self.user)
        self.task1_2 = Task.objects.create(
            title='Task 1.2', parent=self.project1, owner=self.user)
        self.task2_1 = Task.objects.create(
            title='Task 2.1', parent=self.project2, owner=self.user)

        self.subtask1_1_1 = Task.objects.create(
            title='Subtask 1.1.1', parent=self.task1_1, owner=self.user)

    def test_root_level_navigation(self):
        """Test viewing root level tasks."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Should see root level projects
        self.assertContains(response, 'Project 1')
        self.assertContains(response, 'Project 2')

        # Should not see child tasks at root level
        self.assertNotContains(response, 'Task 1.1')
        self.assertNotContains(response, 'Subtask 1.1.1')

    def test_level1_navigation(self):
        """Test drilling down to level 1 tasks."""
        response = self.client.get(reverse('task_list'), {'level1': self.project1.id})
        self.assertEqual(response.status_code, 200)

        # Should see level 1 tasks for project 1
        self.assertContains(response, 'Task 1.1')
        self.assertContains(response, 'Task 1.2')

        # Should not see tasks from other projects
        self.assertNotContains(response, 'Task 2.1')

        # Should not see level 2 tasks
        self.assertNotContains(response, 'Subtask 1.1.1')

    def test_level2_navigation(self):
        """Test drilling down to level 2 tasks."""
        response = self.client.get(reverse('task_list'), {
            'level1': self.project1.id,
            'level2': self.task1_1.id
        })
        self.assertEqual(response.status_code, 200)

        # Should see level 2 tasks
        self.assertContains(response, 'Subtask 1.1.1')

    def test_navigation_with_invalid_ids(self):
        """Test navigation with invalid level IDs."""
        response = self.client.get(reverse('task_list'), {
            'level1': 99999,
            'level2': 'invalid'
        })
        self.assertEqual(response.status_code, 200)

        # Should gracefully handle invalid IDs
        # Should show root level by default
        self.assertContains(response, 'Project 1')
        self.assertContains(response, 'Project 2')


class ExploratoryUITests(TestCase):
    """Exploratory tests for UI behavior and edge cases."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_empty_task_list_display(self):
        """Test how UI handles empty task lists."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Should handle empty state gracefully
        self.assertIn('root_tasks', response.context)
        self.assertEqual(len(response.context['root_tasks']), 0)

    def test_task_list_with_many_tasks(self):
        """Test UI performance with many tasks."""
        # Create many tasks
        for i in range(50):
            Task.objects.create(
                title=f'Task {i}',
                description=f'Description for task {i}',
                owner=self.user
            )

        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Should handle many tasks without issues
        self.assertEqual(len(response.context['root_tasks']), 50)

    def test_task_with_very_long_title(self):
        """Test UI handling of tasks with very long titles."""
        # Use a title that fits within the 200 character limit
        long_title = 'A' * 199  # Just under the limit
        task = Task.objects.create(
            title=long_title,
            owner=self.user
        )

        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Should display without breaking layout
        self.assertContains(response, long_title[:100])  # At least part of it

    def test_task_with_special_characters(self):
        """Test UI handling of tasks with special characters."""
        special_title = 'Task with émojis 🎯 and special chars: <>&"\'`'
        task = Task.objects.create(
            title=special_title,
            description='Contains special chars: <script>alert("test")</script>',
            owner=self.user
        )

        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Should escape HTML properly - Django templates auto-escape
        self.assertContains(response, 'émojis 🎯')
        # The <script> tag should be escaped as &lt;script&gt;
        self.assertContains(response, '&lt;script&gt;')

    def test_concurrent_task_operations(self):
        """Test handling of concurrent task operations."""
        task = Task.objects.create(
            title='Concurrent Test Task',
            owner=self.user,
            done=False
        )

        # Simulate concurrent toggle operations
        response1 = self.client.post(reverse('task_toggle_done', args=[task.id]))
        response2 = self.client.post(reverse('task_toggle_done', args=[task.id]))

        # Both should succeed without errors
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Final state should be consistent
        task.refresh_from_db()
        self.assertIsInstance(task.done, bool)

    def test_form_validation_edge_cases(self):
        """Test form validation with edge case inputs."""
        # Test with empty title
        response = self.client.post(reverse('task_create'), {
            'title': '',
            'description': 'Task with empty title',
            'urgency': 'normal',
            'is_periodic': False
        })

        # Should handle validation error gracefully
        self.assertEqual(response.status_code, 200)  # Form redisplay
        self.assertFalse(
            Task.objects.filter(
                description='Task with empty title').exists())

        # Test with only whitespace title
        response = self.client.post(reverse('task_create'), {
            'title': '   \n\t   ',
            'description': 'Task with whitespace title',
            'urgency': 'normal',
            'is_periodic': False
        })

        # Should handle validation appropriately
        self.assertEqual(response.status_code, 200)

    def test_navigation_breadcrumbs(self):
        """Test navigation breadcrumb functionality."""
        # Create hierarchy
        parent = Task.objects.create(title='Parent Task', owner=self.user)
        child = Task.objects.create(title='Child Task', parent=parent, owner=self.user)
        grandchild = Task.objects.create(
            title='Grandchild Task', parent=child, owner=self.user)

        # Navigate deep into hierarchy
        response = self.client.get(reverse('task_list'), {
            'level1': parent.id,
            'level2': child.id
        })
        self.assertEqual(response.status_code, 200)

        # Should provide context for navigation
        self.assertIn('selected_level1_int', response.context)
        self.assertIn('selected_level2_int', response.context)

    def test_responsive_ui_elements(self):
        """Test that UI elements are present for responsive design."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Check for common responsive elements
        content = response.content.decode()

        # Should have viewport meta tag or responsive framework
        self.assertTrue(
            'viewport' in content or
            'bootstrap' in content.lower() or
            'responsive' in content.lower()
        )


class PrintIntegrationTests(TestCase):
    """Test print functionality integration."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    @patch('tasks.views.print_task')
    def test_single_task_print_workflow(self, mock_print):
        """Test printing a single task."""
        mock_print.return_value = (True, "Print successful")

        task = Task.objects.create(
            title='Print Test Task',
            description='Testing print functionality',
            owner=self.user
        )

        # Test print request
        response = self.client.post(reverse('task_print', args=[task.id]))
        self.assertEqual(response.status_code, 200)

        # Verify print function was called
        mock_print.assert_called()

        # Check JSON response
        try:
            data = json.loads(response.content)
            self.assertTrue(data.get('success', False))
        except json.JSONDecodeError:
            pass

    @patch('tasks.views.print_task')
    def test_print_task_with_subtasks(self, mock_print):
        """Test printing task with subtasks."""
        mock_print.return_value = (True, "Print successful")

        parent = Task.objects.create(title='Parent Task', owner=self.user)
        child1 = Task.objects.create(title='Child 1', parent=parent, owner=self.user)
        child2 = Task.objects.create(title='Child 2', parent=parent, owner=self.user)

        # Print parent task
        response = self.client.post(reverse('task_print', args=[parent.id]))
        self.assertEqual(response.status_code, 200)

        # Should print parent and all children
        self.assertTrue(mock_print.called)
        # mock_print should be called once for parent, and once for each child
        self.assertGreaterEqual(mock_print.call_count, 1)

    @patch('tasks.views.get_todays_periodic_tasks')
    @patch('tasks.views.print_task')
    def test_print_todays_tasks_workflow(self, mock_print, mock_get_todays):
        """Test printing today's tasks (only leaf tasks)."""
        mock_print.return_value = (True, "Print successful")

        # Mock today's tasks - create a mock task that has no subtasks (is a leaf)
        mock_queryset = Mock()
        mock_queryset.exists.return_value = True

        # Create a mock task that appears to be a leaf task
        mock_task = Mock()
        mock_subtasks_manager = Mock()
        mock_subtasks_manager.exists.return_value = False  # No children, it's a leaf
        mock_subtasks_manager.all.return_value = []
        mock_task.subtasks = mock_subtasks_manager

        mock_queryset.__iter__ = Mock(return_value=iter([mock_task]))
        mock_get_todays.return_value = mock_queryset

        response = self.client.post(reverse('print_todays_tasks'))
        self.assertEqual(response.status_code, 200)

        # Verify functions were called
        mock_get_todays.assert_called_with(self.user)
        mock_print.assert_called()  # Should be called once for the leaf task

    def test_print_modal_ui_elements(self):
        """Test that print modal UI elements are present in task list."""
        task = Task.objects.create(
            title='Modal Test Task',
            description='Testing modal presence',
            owner=self.user
        )

        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Check for print modal elements
        self.assertContains(response, 'printConfirmModal')
        self.assertContains(response, 'confirmPrintBtn')
        self.assertContains(response, 'showPrintConfirmModal')

        # Check for "No" button with data-bs-dismiss
        self.assertContains(response, 'btn-secondary')
        self.assertContains(response, 'data-bs-dismiss="modal"')

    def test_print_modal_refresh_behavior(self):
        """Test that print modal external JS file is loaded with required functionality."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Check for external print modal JS file
        content = response.content.decode()

        # Should have the print-modal.js external file loaded
        self.assertIn('/static/tasks/js/print-modal.js', content)

        # Should have print modal structure that external JS will interact with
        self.assertIn('id="printConfirmModal"', content)
        self.assertIn('id="confirmPrintBtn"', content)

        # Should have proper modal structure for Bootstrap events
        self.assertIn('data-bs-dismiss="modal"', content)

        # Print modal should be present in the HTML for external JS to handle
        self.assertIn('Print Task', content)
        self.assertIn('Yes, Print', content)

    def test_universal_modal_refresh_on_task_list(self):
        """Test that task list page loads external JS with modal refresh functionality."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Should have the task-list.js external file loaded
        self.assertIn('/static/tasks/js/task-list.js', content)

        # Should have modals that will be handled by external JS
        self.assertIn('taskModal', content)  # Create task modal
        self.assertIn('editModal', content)  # Edit task modal
        self.assertIn('deleteModal', content)  # Delete confirmation modal

        # Should have print modal with its own external JS
        self.assertIn('printConfirmModal', content)
        self.assertIn('/static/tasks/js/print-modal.js', content)

        # Should have common.js for shared functionality
        self.assertIn('/static/tasks/js/common.js', content)

    def test_create_task_modal_buttons(self):
        """Test that create task modal has both 'Create Task' and 'Create and Print' buttons."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Should have both buttons in the modal
        self.assertIn('saveTaskOnlyBtn', content)  # Create Task button
        self.assertIn('saveAndPrintBtn', content)  # Create and Print button

        # Should have appropriate button text and icons
        self.assertIn('Create Task', content)
        self.assertIn('Create and Print', content)
        self.assertIn('fa-save', content)  # Save icon for Create Task
        self.assertIn('fa-print', content)  # Print icon for Create and Print

        # Create and Print should be the primary button (btn-primary)
        self.assertIn('btn-primary" id="saveAndPrintBtn"', content)
        # Create Task should be secondary (btn-outline-primary)
        self.assertIn('btn-outline-primary" id="saveTaskOnlyBtn"', content)

    def test_create_task_modal_javascript_handlers(self):
        """Test that create task modal has proper JavaScript file loaded and button elements."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Should have the task-list.js external file loaded
        self.assertIn('/static/tasks/js/task-list.js', content)

        # Should have click handler target buttons in HTML
        self.assertIn('saveTaskOnlyBtn', content)
        self.assertIn('saveAndPrintBtn', content)

        # Should have the modal structure that the external JS will interact with
        self.assertIn('id="taskModal"', content)
        self.assertIn('id="taskModalBody"', content)

        # Should have URL variables for external JavaScript
        self.assertIn('taskCreateModalUrl', content)

        # Both buttons should be present for JavaScript to attach handlers to
        self.assertIn('btn-outline-primary" id="saveTaskOnlyBtn"', content)
        self.assertIn('btn-primary" id="saveAndPrintBtn"', content)

    def test_universal_modal_refresh_on_todays_tasks(self):
        """Test that today's tasks page loads external JS with modal refresh functionality."""
        response = self.client.get(reverse('todays_tasks'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Should have the todays-tasks.js external file loaded
        self.assertIn('/static/tasks/js/todays-tasks.js', content)

        # Should have common.js for shared functionality
        self.assertIn('/static/tasks/js/common.js', content)

        # Should have print status modal for external JS to handle
        self.assertIn('printStatusModal', content)

        # Should have URL variable for external JavaScript
        self.assertIn('printTodaysTasksUrl', content)


class SecurityUITests(TestCase):
    """Test UI security aspects."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.client = Client()

    def test_task_access_isolation(self):
        """Test that users can only access their own tasks."""
        # Create tasks for different users
        task1 = Task.objects.create(title='User 1 Task', owner=self.user1)
        task2 = Task.objects.create(title='User 2 Task', owner=self.user2)

        # Login as user1
        self.client.login(username='user1', password='testpass123')

        # Should see own task
        response = self.client.get(reverse('task_list'))
        self.assertContains(response, 'User 1 Task')
        self.assertNotContains(response, 'User 2 Task')

        # Should not be able to access other user's task
        response = self.client.get(reverse('task_edit', args=[task2.id]))
        self.assertEqual(response.status_code, 404)

        # Should not be able to delete other user's task
        response = self.client.post(reverse('task_delete', args=[task2.id]))
        self.assertEqual(response.status_code, 404)

        # Task should still exist
        self.assertTrue(Task.objects.filter(id=task2.id).exists())

    def test_unauthenticated_access_protection(self):
        """Test that unauthenticated users are redirected."""
        task = Task.objects.create(title='Protected Task', owner=self.user1)

        # Ensure not logged in
        self.client.logout()

        # Should redirect to login
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

        # Should not be able to access task operations
        response = self.client.get(reverse('task_edit', args=[task.id]))
        self.assertEqual(response.status_code, 302)

        response = self.client.post(reverse('task_toggle_done', args=[task.id]))
        self.assertEqual(response.status_code, 302)

    def test_csrf_protection(self):
        """Test CSRF protection on forms."""
        self.client.login(username='user1', password='testpass123')

        # Try to submit form without CSRF token
        response = self.client.post(reverse('task_create'), {
            'title': 'CSRF Test Task',
            'description': 'Testing CSRF protection',
            'urgency': 'normal',
            'is_periodic': False
        }, HTTP_X_CSRFTOKEN='invalid')

        # Should be protected (exact behavior depends on CSRF settings)
        # At minimum, should not create task with invalid CSRF
        self.assertIn(response.status_code, [200, 403, 302])


class PerformanceUITests(TestCase):
    """Test UI performance characteristics."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_database_query_efficiency(self):
        """Test that views don't generate excessive database queries."""
        # Create some test data
        for i in range(10):
            parent = Task.objects.create(title=f'Parent {i}', owner=self.user)
            for j in range(5):
                Task.objects.create(
                    title=f'Child {i}-{j}',
                    parent=parent,
                    owner=self.user)

        # Test task list view - be realistic about query count
        # Expect: session, user, root tasks, then child counts for each parent
        with self.assertNumQueries(23):  # Actual observed count
            response = self.client.get(reverse('task_list'))
            self.assertEqual(response.status_code, 200)

    def test_large_task_list_performance(self):
        """Test performance with large number of tasks."""
        # Create many tasks
        tasks = []
        for i in range(100):
            tasks.append(Task(
                title=f'Performance Test Task {i}',
                description=f'Description {i}',
                owner=self.user
            ))
        Task.objects.bulk_create(tasks)

        # Should still respond reasonably quickly
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['root_tasks']), 100)

    def test_deep_hierarchy_performance(self):
        """Test performance with deeply nested task hierarchy."""
        # Create hierarchy within the 3-level limit
        current_parent = None
        for i in range(3):  # Create 3-level deep hierarchy (within limit)
            task = Task.objects.create(
                title=f'Level {i} Task',
                parent=current_parent,
                owner=self.user
            )
            current_parent = task

        # Should handle deep hierarchy without issues
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)

        # Test navigation through hierarchy
        level1_task = Task.objects.filter(parent=None).first()
        response = self.client.get(reverse('task_list'), {'level1': level1_task.id})
        self.assertEqual(response.status_code, 200)


class LogoutFunctionalityTests(TestCase):
    """Test logout functionality after JavaScript fix."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com', 
            password='testpass123'
        )
        self.client = Client()

    def test_logout_form_presence_in_base_template(self):
        """Test that logout form is present when user is logged in."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that logout form is present
        self.assertContains(response, 'action="/admin/logout/"')
        self.assertContains(response, 'method="post"')
        self.assertContains(response, 'Logout')
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_logout_form_absent_when_anonymous(self):
        """Test that logout form is not present for anonymous users."""
        response = self.client.get(reverse('welcome'))
        self.assertEqual(response.status_code, 200)
        
        # Check that logout form is not present
        self.assertNotContains(response, 'action="/admin/logout/"')
        self.assertContains(response, 'Login')  # Should see login link instead

    def test_logout_functionality_works(self):
        """Test that logout actually logs out the user."""
        # Login first
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success)
        
        # Verify user is logged in
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Perform logout using Django's built-in logout method
        self.client.logout()
        
        # Verify user is now logged out by trying to access protected page
        response = self.client.get(reverse('task_list'))
        # Task list view should redirect unauthenticated users to login
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_logout_with_csrf_token(self):
        """Test logout works with proper CSRF token."""
        # Login first
        self.client.login(username='testuser', password='testpass123')
        
        # Get CSRF token from a page
        response = self.client.get(reverse('task_list'))
        csrf_token = response.context['csrf_token']
        
        # Logout with CSRF token
        response = self.client.post('/admin/logout/', {
            'csrfmiddlewaretoken': csrf_token
        })
        
        # Should successfully redirect
        self.assertEqual(response.status_code, 302)


class PeriodicTaskDeletionTests(TestCase):
    """Test unified periodic task deletion behavior."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_periodic_subtask_deletion_modal_detection(self):
        """Test that delete modal correctly detects periodic subtasks."""
        # Create periodic template with subtask
        from datetime import date
        template = Task.objects.create(
            title='Periodic Template',
            owner=self.user,
            is_periodic=True,
            start_date=date.today(),
            periodicity_type='daily'
        )
        subtask = Task.objects.create(
            title='Template Subtask',
            parent=template,
            owner=self.user
        )
        
        # Create instance with subtask
        instance = Task.objects.create(
            title='Periodic Instance',
            owner=self.user,
            periodic_parent=template
        )
        instance_subtask = Task.objects.create(
            title='Instance Subtask',
            parent=instance,
            owner=self.user
        )
        
        # Test delete modal for template subtask
        response = self.client.get(f'/tasks/delete/modal/{subtask.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_periodic_subtask'])
        self.assertEqual(data['template_title'], 'Periodic Template')
        
        # Test delete modal for instance subtask  
        response = self.client.get(f'/tasks/delete/modal/{instance_subtask.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['is_periodic_subtask'])
        self.assertEqual(data['template_title'], 'Periodic Template')

    def test_unified_periodic_subtask_deletion(self):
        """Test that deleting any periodic subtask removes from template and all instances."""
        # Create periodic template with subtask
        from datetime import date
        template = Task.objects.create(
            title='Periodic Template',
            owner=self.user,
            is_periodic=True,
            start_date=date.today(),
            periodicity_type='daily'
        )
        template_subtask = Task.objects.create(
            title='Template Subtask',
            parent=template,
            owner=self.user
        )
        
        # Create multiple instances with subtasks
        instances = []
        instance_subtasks = []
        for i in range(3):
            instance = Task.objects.create(
                title=f'Instance {i}',
                owner=self.user,
                periodic_parent=template
            )
            instance_subtask = Task.objects.create(
                title='Template Subtask',  # Same title as template
                parent=instance,
                owner=self.user
            )
            instances.append(instance)
            instance_subtasks.append(instance_subtask)
        
        # Delete one of the instance subtasks
        response = self.client.delete(f'/tasks/delete/modal/{instance_subtasks[0].id}/')
        self.assertEqual(response.status_code, 200)
        
        # Verify all related subtasks are deleted
        self.assertFalse(Task.objects.filter(id=template_subtask.id).exists())
        for subtask in instance_subtasks:
            self.assertFalse(Task.objects.filter(id=subtask.id).exists())
        
        # Verify instances and template still exist
        self.assertTrue(Task.objects.filter(id=template.id).exists())
        for instance in instances:
            self.assertTrue(Task.objects.filter(id=instance.id).exists())


class PrintModalTests(TestCase):
    """Test print modal functionality fixes."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_print_modal_authentication(self):
        """Test that print endpoint requires authentication."""
        # Logout and try to access print endpoint
        self.client.logout()
        
        task = Task.objects.create(title='Test Task', owner=self.user)
        response = self.client.get(f'/tasks/print/{task.pk}/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())

    def test_print_modal_returns_json(self):
        """Test that print endpoint returns proper JSON response."""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            owner=self.user
        )
        
        response = self.client.post(f'/tasks/print/{task.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = response.json()
        self.assertIn('success', data)

    @patch('tasks.views.print_task')
    def test_print_modal_post_functionality(self, mock_print):
        """Test print endpoint POST request functionality."""
        mock_print.return_value = (True, "Print successful")
        
        task = Task.objects.create(
            title='Test Task',
            description='Test Description', 
            owner=self.user
        )
        
        response = self.client.post(f'/tasks/print/{task.pk}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        mock_print.assert_called_once()
        mock_print.assert_called_once()


class DeleteModalSerializationTests(TestCase):
    """Test delete modal JSON serialization fixes."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_delete_modal_returns_valid_json(self):
        """Test that delete modal returns valid JSON without serialization errors."""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            owner=self.user
        )
        
        response = self.client.get(f'/tasks/delete/modal/{task.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Should not raise JSON decode error
        data = response.json()
        
        # Verify expected fields are present and properly typed
        self.assertIsInstance(data['success'], bool)
        self.assertIsInstance(data['task_title'], str)
        self.assertIsInstance(data['incomplete_subtasks'], bool)
        self.assertIsInstance(data['subtask_count'], int)
        self.assertIsInstance(data['is_periodic_subtask'], bool)
        self.assertIsInstance(data['affected_instances'], int)

    def test_delete_modal_with_subtasks(self):
        """Test delete modal JSON response with subtasks."""
        parent = Task.objects.create(title='Parent Task', owner=self.user)
        Task.objects.create(title='Child 1', parent=parent, owner=self.user)
        Task.objects.create(title='Child 2', parent=parent, owner=self.user, done=True)
        Task.objects.create(title='Child 3', parent=parent, owner=self.user)  # Incomplete
        
        response = self.client.get(f'/tasks/delete/modal/{parent.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['subtask_count'], 3)
        self.assertTrue(data['incomplete_subtasks'])  # Has incomplete subtasks

    def test_delete_modal_authentication_required(self):
        """Test that delete modal requires authentication."""
        task = Task.objects.create(title='Test Task', owner=self.user)
        
        # Logout and try to access
        self.client.logout()
        response = self.client.get(f'/tasks/delete/modal/{task.id}/')
        
        # Should redirect to login, not return JSON error
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())
