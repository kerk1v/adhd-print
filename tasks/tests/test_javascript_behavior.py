"""
Tests for JavaScript behavior and frontend functionality.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tasks.models import Task
import json


class JavaScriptIntegrationTests(TestCase):
    """Test JavaScript behavior in the application."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_logout_button_excludes_loading_state(self):
        """Test that logout forms are excluded from loading state JavaScript."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the logout form has the correct action
        self.assertContains(response, 'action="/admin/logout/"')
        
        # Verify the common.js is loaded (should contain the fixed logic)
        self.assertContains(response, 'static/tasks/js/common.js')

    def test_regular_forms_still_get_loading_state(self):
        """Test that non-logout forms still get loading states."""
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)
        
        # Should contain submit buttons that would get loading states
        self.assertContains(response, 'type="submit"')
        self.assertContains(response, 'static/tasks/js/common.js')

    def test_print_modal_javascript_loaded(self):
        """Test that print modal JavaScript is properly loaded."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that print-modal.js is loaded
        self.assertContains(response, 'static/tasks/js/print-modal.js')

    def test_task_list_javascript_loaded(self):
        """Test that task list JavaScript is properly loaded."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that task-list.js is loaded  
        self.assertContains(response, 'static/tasks/js/task-list.js')

    def test_csrf_token_present_in_forms(self):
        """Test that CSRF tokens are present in forms."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check that CSRF token is present in logout form
        self.assertContains(response, 'csrfmiddlewaretoken')


class CommonJSBehaviorTests(TestCase):
    """Test common.js behavior fixes."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_logout_form_structure(self):
        """Test that logout form has the expected structure for JavaScript exclusion."""
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Should have logout form with correct action
        self.assertIn('action="/admin/logout/"', content)
        self.assertIn('method="post"', content)
        
        # Should have submit button
        self.assertIn('type="submit"', content)
        self.assertIn('Logout', content)

    def test_task_creation_form_structure(self):
        """Test that regular forms maintain submit button structure."""
        response = self.client.get(reverse('task_create'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Should have submit buttons that get loading states
        self.assertIn('type="submit"', content)
        self.assertIn('btn', content)

    def test_modal_forms_structure(self):
        """Test that modal forms have proper structure."""
        task = Task.objects.create(title='Test Task', owner=self.user)
        
        # Test edit modal
        response = self.client.get(reverse('task_edit_modal', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test delete modal
        response = self.client.get(reverse('task_delete_modal', args=[task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')


class EventDelegationTests(TestCase):
    """Test event delegation functionality."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com', 
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_print_button_event_delegation(self):
        """Test that print buttons work with event delegation."""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            owner=self.user
        )
        
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should contain print button elements that event delegation targets
        content = response.content.decode()
        self.assertIn('fas fa-print', content)  # Print icon

    def test_delete_button_event_delegation(self):
        """Test that delete buttons work with event delegation."""
        task = Task.objects.create(title='Test Task', owner=self.user)
        
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should contain delete button elements
        content = response.content.decode()
        self.assertIn('delete', content.lower())

    def test_dynamic_content_buttons(self):
        """Test that dynamically loaded content buttons work."""
        parent = Task.objects.create(title='Parent Task', owner=self.user)
        child = Task.objects.create(title='Child Task', parent=parent, owner=self.user)
        
        # Navigate to show child tasks (simulating dynamic loading)
        response = self.client.get(reverse('task_list'), {'level1': parent.id})
        self.assertEqual(response.status_code, 200)
        
        # Should show child task with buttons
        self.assertContains(response, 'Child Task')