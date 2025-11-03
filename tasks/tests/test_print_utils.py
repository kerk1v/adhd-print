"""
Tests for tasks/print_utils.py - Thermal Printer Utilities

This module tests all printing functionality including:
- Image creation and processing
- ESC/POS command generation
- Font loading and fallbacks
- Task hierarchy processing
- Color and urgency handling
- Graphics and text mode printing
- Error handling and edge cases
"""

import unittest.mock
import socket
import os
import unittest
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from tasks.models import Task
from tasks.print_utils import (
    get_urgency_color,
    get_task_hierarchy,
    create_task_image,
    convert_image_to_escp,
    convert_image_to_bitmap_escp,
    print_task,
)


class PrintUtilsTestCase(TestCase):
    """Base test case with common setup for print utilities tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Enable server printing for testing
        self.user.profile.printing_method = 'server'
        self.user.profile.server_printing_enabled = True
        self.user.profile.save()
        
        # Create test tasks with hierarchy
        self.parent_task = Task.objects.create(
            title='Parent Task',
            description='Parent description',
            urgency='normal',
            owner=self.user,
            due_date=timezone.now() + timedelta(days=1)
        )
        
        self.child_task = Task.objects.create(
            title='Child Task',
            description='Child description',
            urgency='urgent',
            owner=self.user,
            parent=self.parent_task,
            due_date=timezone.now() - timedelta(days=1)  # Overdue
        )
        
        self.grandchild_task = Task.objects.create(
            title='Grandchild Task with a Very Long Title That Should Wrap',
            description='Very long description that should test text wrapping functionality in both graphics and text modes',
            urgency='critical',
            owner=self.user,
            parent=self.child_task,
            due_date=timezone.now().date()  # Today
        )


class UrgencyColorTests(PrintUtilsTestCase):
    """Test urgency color mapping functionality."""

    def test_get_urgency_color_all_levels(self):
        """Test that all urgency levels return correct colors."""
        expected_colors = {
            'low': '#28a745',
            'normal': '#007bff',
            'urgent': '#ffc107',
            'critical': '#dc3545'
        }
        
        for urgency, expected_color in expected_colors.items():
            with self.subTest(urgency=urgency):
                color = get_urgency_color(urgency)
                self.assertEqual(color, expected_color)

    def test_get_urgency_color_unknown_urgency(self):
        """Test that unknown urgency levels return default color."""
        default_color = '#007bff'
        
        test_cases = ['unknown', '', None, 'invalid', 123]
        for test_urgency in test_cases:
            with self.subTest(urgency=test_urgency):
                color = get_urgency_color(test_urgency)
                self.assertEqual(color, default_color)


class TaskHierarchyTests(PrintUtilsTestCase):
    """Test task hierarchy path generation."""

    def test_get_task_hierarchy_single_task(self):
        """Test hierarchy for task with no parent."""
        hierarchy = get_task_hierarchy(self.parent_task)
        self.assertEqual(hierarchy, ['Parent Task'])

    def test_get_task_hierarchy_two_levels(self):
        """Test hierarchy for task with one parent."""
        hierarchy = get_task_hierarchy(self.child_task)
        self.assertEqual(hierarchy, ['Parent Task', 'Child Task'])

    def test_get_task_hierarchy_three_levels(self):
        """Test hierarchy for task with grandparent."""
        hierarchy = get_task_hierarchy(self.grandchild_task)
        expected = [
            'Parent Task',
            'Child Task',
            'Grandchild Task with a Very Long Title That Should Wrap'
        ]
        self.assertEqual(hierarchy, expected)

    def test_get_task_hierarchy_none_task(self):
        """Test hierarchy with None task (edge case)."""
        hierarchy = get_task_hierarchy(None)
        self.assertEqual(hierarchy, [])


class ImageCreationTests(PrintUtilsTestCase):
    """Test task image creation functionality."""

    def test_create_task_image_basic(self):
        """Test basic image creation with simple task."""
        image = create_task_image(self.parent_task)
        
        # Verify image properties
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.mode, '1')  # 1-bit black and white
        self.assertEqual(image.width, 576)  # Expected width for 80mm default
        self.assertGreater(image.height, 100)  # Should have reasonable height

    def test_create_task_image_80mm_width(self):
        """Test image creation with explicit 80mm width."""
        image = create_task_image(self.parent_task, printer_width='80mm')
        
        # Verify image properties
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.mode, '1')
        self.assertEqual(image.width, 576)  # Expected width for 80mm
        self.assertGreater(image.height, 100)

    def test_create_task_image_57mm_width(self):
        """Test image creation with 57mm width."""
        image = create_task_image(self.parent_task, printer_width='57mm')
        
        # Verify image properties
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.mode, '1')
        self.assertEqual(image.width, 375)  # Expected width for 57mm (reduced for physical margins)
        self.assertGreater(image.height, 100)

    def test_create_task_image_width_comparison(self):
        """Test that 57mm images are narrower than 80mm images."""
        image_80mm = create_task_image(self.parent_task, printer_width='80mm')
        image_57mm = create_task_image(self.parent_task, printer_width='57mm')
        
        # 57mm should be narrower
        self.assertLess(image_57mm.width, image_80mm.width)
        self.assertEqual(image_80mm.width, 576)
        self.assertEqual(image_57mm.width, 375)  # Updated to match implementation

    def test_create_task_image_with_hierarchy(self):
        """Test image creation with hierarchical task."""
        image = create_task_image(self.grandchild_task)
        
        self.assertIsInstance(image, Image.Image)
        self.assertEqual(image.mode, '1')
        self.assertEqual(image.width, 576)
        # Should be taller due to hierarchy display
        self.assertGreater(image.height, 200)

    def test_create_task_image_no_description(self):
        """Test image creation with task without description."""
        task_no_desc = Task.objects.create(
            title='No Description Task',
            urgency='low',
            owner=self.user
        )
        
        image = create_task_image(task_no_desc)
        self.assertIsInstance(image, Image.Image)

    def test_create_task_image_no_due_date(self):
        """Test image creation with task without due date."""
        task_no_due = Task.objects.create(
            title='No Due Date Task',
            description='No due date',
            urgency='normal',
            owner=self.user
        )
        
        image = create_task_image(task_no_due)
        self.assertIsInstance(image, Image.Image)

    @unittest.mock.patch('tasks.print_utils.os.path.join')
    def test_create_task_image_font_fallback_system(self, mock_path_join):
        """Test font fallback to system fonts when Roboto is unavailable."""
        # Make the Roboto font path invalid so it falls back
        mock_path_join.return_value = '/nonexistent/path/Roboto-Regular.ttf'
        
        image = create_task_image(self.parent_task)
        self.assertIsInstance(image, Image.Image)

    @unittest.mock.patch('tasks.print_utils.os.path.join')
    @override_settings(BASE_DIR='/nonexistent/path')
    def test_create_task_image_font_fallback_final(self, mock_path_join):
        """Test final fallback to default font when all fonts fail."""
        # Make all font paths invalid
        mock_path_join.return_value = '/nonexistent/path/font.ttf'
        
        image = create_task_image(self.parent_task)
        self.assertIsInstance(image, Image.Image)

    @unittest.mock.patch('tasks.print_utils.Image.open')
    def test_create_task_image_icon_fallback(self, mock_open):
        """Test fallback to generated icons when Material Design icons fail."""
        mock_open.side_effect = FileNotFoundError("Icon not found")
        
        # Test all urgency levels for fallback icons
        for urgency in ['critical', 'urgent', 'normal', 'low']:
            task = Task.objects.create(
                title=f'Test {urgency}',
                urgency=urgency,
                owner=self.user
            )
            with self.subTest(urgency=urgency):
                image = create_task_image(task)
                self.assertIsInstance(image, Image.Image)

    def test_create_task_image_icon_success(self):
        """Test successful material design icon loading."""
        # Test with an urgency that likely has an icon file
        for urgency in ['critical', 'urgent', 'normal', 'low']:
            task = Task.objects.create(
                title=f'Test {urgency}',
                urgency=urgency,
                owner=self.user
            )
            with self.subTest(urgency=urgency):
                image = create_task_image(task)
                self.assertIsInstance(image, Image.Image)

    @unittest.mock.patch('tasks.print_utils.Image.open')
    def test_create_task_image_icon_mode_conversion(self, mock_open):
        """Test icon mode conversion when icon is not 1-bit."""
        # Create a mock RGB icon that needs conversion
        rgb_icon = Image.new('RGB', (85, 85), (255, 255, 255))
        mock_open.return_value = rgb_icon
        
        image = create_task_image(self.parent_task)
        self.assertIsInstance(image, Image.Image)

    def test_create_task_image_long_title_wrapping(self):
        """Test image creation with very long title that requires wrapping."""
        long_task = Task.objects.create(
            title='This is an extremely long task title that should definitely require text wrapping across multiple lines when rendered in the thermal printer image format',
            urgency='urgent',
            owner=self.user
        )
        
        image = create_task_image(long_task)
        self.assertIsInstance(image, Image.Image)
        # Should be taller due to wrapped title
        self.assertGreater(image.height, 300)

    def test_create_task_image_overdue_task(self):
        """Test image creation with overdue task."""
        overdue_task = Task.objects.create(
            title='Overdue Task',
            urgency='critical',
            owner=self.user,
            due_date=timezone.now() - timedelta(days=5)
        )
        
        image = create_task_image(overdue_task)
        self.assertIsInstance(image, Image.Image)

    def test_create_task_image_today_task(self):
        """Test image creation with task due today."""
        today_task = Task.objects.create(
            title='Today Task',
            urgency='urgent',
            owner=self.user,
            due_date=timezone.now().date()
        )
        
        image = create_task_image(today_task)
        self.assertIsInstance(image, Image.Image)


class EscPosConversionTests(PrintUtilsTestCase):
    """Test ESC/POS command generation."""

    def test_convert_image_to_escp(self):
        """Test basic ESC/POS conversion from image."""
        # Create a simple test image
        test_image = Image.new('1', (100, 50), 1)
        draw = ImageDraw.Draw(test_image)
        draw.rectangle([10, 10, 90, 40], fill=0)
        
        escp_data = convert_image_to_escp(test_image)
        
        self.assertIsInstance(escp_data, bytes)
        self.assertGreater(len(escp_data), 0)
        # Check for ESC/POS initialization command
        self.assertIn(b'\x1B\x40', escp_data)  # ESC @
        # Check for graphics command
        self.assertIn(b'\x1B\x2A\x00', escp_data)  # ESC * 0
        # Check for cut command
        self.assertIn(b'\x1D\x56\x00', escp_data)  # GS V 0

    def test_convert_image_to_bitmap_escp(self):
        """Test bitmap ESC/POS conversion from image."""
        test_image = Image.new('1', (100, 50), 1)
        draw = ImageDraw.Draw(test_image)
        draw.ellipse([20, 10, 80, 40], fill=0)
        
        escp_data = convert_image_to_bitmap_escp(test_image)
        
        self.assertIsInstance(escp_data, bytes)
        self.assertGreater(len(escp_data), 0)
                # Check for ESC/POS initialization
        self.assertIn(b'\x1B\x40', escp_data)  # ESC @
        # Check for bitmap command
        self.assertIn(b'\x1D\x76\x30\x00', escp_data)  # GS v 0 0
        # Check for cut command
        self.assertIn(b'\x1D\x56\x00', escp_data)  # GS V 0


class PrintTaskTests(PrintUtilsTestCase):
    """Test the main print_task function."""

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_graphics_mode_success(self, mock_socket):
        """Test successful printing in graphics mode."""
        # Mock successful socket connection
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task, use_graphics=True)
        
        self.assertTrue(success)
        self.assertIn('graphics (bitmap)', message)
        self.assertIn('successfully', message)
        
        # Verify socket was used
        mock_socket.assert_called_once()
        mock_sock.connect.assert_called_once()
        mock_sock.sendall.assert_called_once()

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_socket_error(self, mock_socket):
        """Test print failure due to socket error."""
        mock_socket.side_effect = socket.error("Connection refused")
        
        success, message = print_task(self.parent_task)
        
        self.assertFalse(success)
        self.assertIn('Printer connection error', message)
        self.assertIn('Connection refused', message)

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_socket_timeout(self, mock_socket):
        """Test print failure due to socket timeout."""
        mock_sock = unittest.mock.Mock()
        mock_sock.connect.side_effect = socket.timeout("Connection timed out")
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task)
        
        self.assertFalse(success)
        self.assertIn('Printer connection error', message)

    @unittest.mock.patch('tasks.print_utils.create_task_image')
    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_graphics_mode_image_failure(self, mock_socket, mock_create_image):
        """Test graphics mode behavior when image creation fails."""
        # Make image creation fail
        mock_create_image.side_effect = Exception("Image creation failed")
        
        # Mock successful socket
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task, use_graphics=True)
        
        # Should fail when image creation fails since text mode fallback is removed
        self.assertFalse(success)
        self.assertIn('Image creation failed', message)

    @override_settings(PRINTER_HOST='test.printer.local', PRINTER_PORT=8080)
    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_custom_printer_settings(self, mock_socket):
        """Test that custom printer settings are used."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        print_task(self.parent_task)
        
        # Verify connection was made to custom settings
        mock_sock.connect.assert_called_with(('test.printer.local', 8080))

    def test_print_task_invalid_task(self):
        """Test print function with invalid task object."""
        # Test with None
        success, message = print_task(None)
        self.assertFalse(success)
        self.assertIn('error', message.lower())

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_with_all_urgency_levels(self, mock_socket):
        """Test printing tasks with all urgency levels."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        urgency_levels = ['low', 'normal', 'urgent', 'critical']
        
        for urgency in urgency_levels:
            task = Task.objects.create(
                title=f'Test {urgency}',
                urgency=urgency,
                owner=self.user
            )
            with self.subTest(urgency=urgency):
                success, message = print_task(task)
                self.assertTrue(success)

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_complex_hierarchy(self, mock_socket):
        """Test printing task with complex hierarchy."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.grandchild_task)
        self.assertTrue(success)
        
        # Verify data was sent (should be larger due to hierarchy)
        args, kwargs = mock_sock.sendall.call_args
        sent_data = args[0]
        self.assertIsInstance(sent_data, bytes)
        self.assertGreater(len(sent_data), 100)

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_with_80mm_width(self, mock_socket):
        """Test printing task with explicit 80mm width."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task, printer_width='80mm')
        self.assertTrue(success)
        self.assertIn('80mm', message)
        
        # Verify socket was called
        mock_sock.sendall.assert_called_once()

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_with_57mm_width(self, mock_socket):
        """Test printing task with 57mm width."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task, printer_width='57mm')
        self.assertTrue(success)
        self.assertIn('57mm', message)
        
        # Verify socket was called  
        mock_sock.sendall.assert_called_once()

    @unittest.mock.patch('tasks.print_utils.socket.socket')
    def test_print_task_width_backward_compatibility(self, mock_socket):
        """Test that print_task works without width parameter (backward compatibility)."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        # Call without width parameter (should default to 80mm)
        success, message = print_task(self.parent_task)
        self.assertTrue(success)
        
        # Verify socket was called
        mock_sock.sendall.assert_called_once()


class PrintUtilsEdgeCasesTests(PrintUtilsTestCase):
    """Test edge cases and error conditions."""

    def test_task_with_unicode_characters(self):
        """Test handling of unicode characters in task content."""
        unicode_task = Task.objects.create(
            title='Task with unicode: 🚀 ✓ ñáéíóú 中文',
            description='Description with émojis: 📋 ⚡ and accénts',
            urgency='normal',
            owner=self.user
        )
        
        # Test graphics mode
        image = create_task_image(unicode_task)
        self.assertIsInstance(image, Image.Image)

    def test_empty_task_fields(self):
        """Test handling of empty or minimal task fields."""
        minimal_task = Task.objects.create(
            title='Minimal',  # Non-empty title (required field)
            description='',  # Empty description
            urgency='normal',
            owner=self.user
        )
        
        # Should not crash with minimal fields
        image = create_task_image(minimal_task)
        self.assertIsInstance(image, Image.Image)

    def test_very_deep_hierarchy(self):
        """Test handling of deep task hierarchy within model limits."""
        # Create a 3-level deep hierarchy (the maximum allowed)
        current_parent = self.parent_task
        for i in range(2):  # Create 2 more levels (total 3)
            current_parent = Task.objects.create(
                title=f'Level {i+2} Task',
                urgency='normal',
                owner=self.user,
                parent=current_parent
            )
        
        hierarchy = get_task_hierarchy(current_parent)
        self.assertEqual(len(hierarchy), 3)
        
        # Should handle deep hierarchy gracefully
        image = create_task_image(current_parent)
        self.assertIsInstance(image, Image.Image)

    @override_settings(BASE_DIR='/nonexistent/path')
    def test_missing_static_resources(self):
        """Test graceful handling when static resources are missing."""
        # Should fall back to system fonts and generated icons
        image = create_task_image(self.parent_task)
        self.assertIsInstance(image, Image.Image)

    def test_parent_task_text_wrapping(self):
        """Test text wrapping for very long parent task names."""
        # Create a task with a very long parent name to trigger wrapping
        long_parent = Task.objects.create(
            title='This is an extremely long parent task name that definitely needs to be wrapped when displayed',
            urgency='normal',
            owner=self.user
        )
        
        child_with_long_parent = Task.objects.create(
            title='Child Task',
            urgency='urgent',
            owner=self.user,
            parent=long_parent
        )
        
        # Should handle long parent names gracefully
        image = create_task_image(child_with_long_parent)
        self.assertIsInstance(image, Image.Image)

    def test_task_with_no_attributes(self):
        """Test tasks that might have None values for optional attributes."""
        # Test with a task that has minimal required fields
        basic_task = Task.objects.create(
            title='Basic Task',
            urgency='normal',
            owner=self.user
        )
        # Manually set due_date to None (in case it's auto-populated)
        basic_task.due_date = None
        basic_task.save()
        
        image = create_task_image(basic_task)
        self.assertIsInstance(image, Image.Image)

    def test_large_image_dimensions(self):
        """Test that images don't become unreasonably large."""
        # Create task with reasonably long content (within model limits)
        large_task = Task.objects.create(
            title='Very Long Title That Tests Text Wrapping Functionality',  # Under 200 chars
            description='Very long description that tests text wrapping functionality in both graphics and text modes. This description is designed to test how the system handles longer text content.',
            urgency='critical',
            owner=self.user
        )
        
        image = create_task_image(large_task)
        
        # Image should be reasonable size (not bigger than 10MB when uncompressed)
        max_pixels = 10 * 1024 * 1024  # 10M pixels
        actual_pixels = image.width * image.height
        self.assertLess(actual_pixels, max_pixels)

    def test_null_due_date_edge_cases(self):
        """Test various due date edge cases."""
        # Task with null due_date
        task_null_due = Task.objects.create(
            title='No due date',
            urgency='normal',
            owner=self.user,
            due_date=None
        )
        
        # Should handle null due date gracefully
        image = create_task_image(task_null_due)
        self.assertIsInstance(image, Image.Image)


class PrintModalIntegrationTests(PrintUtilsTestCase):
    """Test print modal integration and JavaScript functionality."""

    def test_print_modal_elements_present(self):
        """Test that print modal elements are present in task list."""
        from django.urls import reverse
        
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Check for print modal HTML structure
        self.assertIn('id="printConfirmModal"', content)
        self.assertIn('id="confirmPrintBtn"', content)
        self.assertIn('Print this task?', content)
        self.assertIn('Print Task', content)  # Updated button text
        
        # Check for print button in task items
        self.assertIn('showPrintConfirmModal', content)
        
        # Check for required JavaScript files
        self.assertIn('/static/tasks/js/print-modal.js', content)
        self.assertIn('/static/tasks/js/common.js', content)

    def test_print_modal_button_functionality(self):
        """Test that print buttons trigger the correct modal function."""
        from django.urls import reverse
        
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        
        # Create a task to test with
        test_task = Task.objects.create(
            title='Test Print Task',
            urgency='normal',
            owner=self.user
        )
        
        response = self.client.get(reverse('task_list'))
        content = response.content.decode()
        
        # Should have print button with correct onclick handler including task title
        expected_onclick = f"showPrintConfirmModal({test_task.id}, 'Test Print Task')"
        self.assertIn(expected_onclick, content)

    @unittest.mock.patch('tasks.views.print_task')
    def test_print_endpoint_integration(self, mock_print_task):
        """Test the print endpoint that the modal JavaScript calls."""
        from django.urls import reverse
        import json
        
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        
        # Mock successful printing
        mock_print_task.return_value = (True, 'Task printed successfully!')
        
        test_task = Task.objects.create(
            title='Test Print Task',
            urgency='normal',
            owner=self.user
        )
        
        # Test the print endpoint
        response = self.client.post(
            reverse('task_print', args=[test_task.id]),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('printed successfully', data['message'])
        
        # Verify print_task was called with default printer width
        mock_print_task.assert_called_once_with(test_task, use_graphics=True, printer_width='80mm')

    @unittest.mock.patch('tasks.views.print_task')
    def test_print_endpoint_failure(self, mock_print_task):
        """Test print endpoint when printing fails."""
        from django.urls import reverse
        import json
        
        # Mock failed printing
        mock_print_task.return_value = (False, 'Printer connection error')
        
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        
        test_task = Task.objects.create(
            title='Test Print Task',
            urgency='normal',
            owner=self.user
        )
        
        response = self.client.post(
            reverse('task_print', args=[test_task.id]),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('connection error', data['message'])

    def test_print_endpoint_authentication_required(self):
        """Test that print endpoint requires authentication."""
        from django.urls import reverse
        
        # Logout the user
        self.client.logout()
        
        test_task = Task.objects.create(
            title='Test Print Task',
            urgency='normal',
            owner=self.user
        )
        
        response = self.client.post(
            reverse('task_print', args=[test_task.id]),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_print_endpoint_user_isolation(self):
        """Test that users can only print their own tasks."""
        from django.urls import reverse
        import json
        
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        
        # Create another user and their task
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        other_task = Task.objects.create(
            title='Other User Task',
            urgency='normal',
            owner=other_user
        )
        
        # Try to print other user's task
        response = self.client.post(
            reverse('task_print', args=[other_task.id]),
            content_type='application/json'
        )
        
        # Should return 404 (task not found for this user)
        self.assertEqual(response.status_code, 404)

    def test_print_modal_javascript_functions_defined(self):
        """Test that required JavaScript functions are properly defined."""
        from django.urls import reverse
        
        # Log in the user first
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('task_list'))
        content = response.content.decode()
        
        # Check that print modal JavaScript is included
        self.assertIn('/static/tasks/js/print-modal.js', content)
        
        # Check that common.js is included (has showMessage function)
        self.assertIn('/static/tasks/js/common.js', content)
        
        # Check that showPrintConfirmModal function is called in print buttons
        self.assertIn('showPrintConfirmModal', content)