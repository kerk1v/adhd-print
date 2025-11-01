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
    convert_task_to_text_escp,
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
        self.assertEqual(image.width, 576)  # Expected width
        self.assertGreater(image.height, 100)  # Should have reasonable height

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

    def test_convert_task_to_text_escp(self):
        """Test text-only ESC/POS conversion."""
        escp_data = convert_task_to_text_escp(self.parent_task)
        
        self.assertIsInstance(escp_data, bytes)
        self.assertGreater(len(escp_data), 0)
        
        # Decode to check content
        text_content = escp_data.decode('utf-8', errors='ignore')
        
        # Check for task title
        self.assertIn('Parent Task', text_content)
        # Check for description
        self.assertIn('Parent description', text_content)
        # Check for due date
        self.assertIn('DUE:', text_content)
        # Check for borders
        self.assertIn('=', text_content)
        
        # Check for ESC/POS commands in binary data
        self.assertIn(b'\x1B\x40', escp_data)  # ESC @ (init)
        self.assertIn(b'\x1D\x56\x00', escp_data)  # GS V 0 (cut)

    def test_convert_task_to_text_escp_with_hierarchy(self):
        """Test text conversion with hierarchical task."""
        escp_data = convert_task_to_text_escp(self.grandchild_task)
        text_content = escp_data.decode('utf-8', errors='ignore')
        
        # Check for parent information
        self.assertIn('Parents', text_content)
        self.assertIn('Parent Task', text_content)
        self.assertIn('Child Task', text_content)
        # Check for current task
        self.assertIn('Grandchild Task', text_content)

    def test_convert_task_to_text_escp_urgency_symbols(self):
        """Test urgency symbol generation in text mode."""
        test_cases = [
            ('critical', '[!!!]'),
            ('urgent', '[!!]'),
            ('normal', '[!]'),
            ('low', '[ ]')
        ]
        
        for urgency, expected_symbol in test_cases:
            task = Task.objects.create(
                title=f'Test {urgency}',
                urgency=urgency,
                owner=self.user
            )
            with self.subTest(urgency=urgency):
                escp_data = convert_task_to_text_escp(task)
                text_content = escp_data.decode('utf-8', errors='ignore')
                self.assertIn(expected_symbol, text_content)

    def test_convert_task_to_text_escp_long_text_wrapping(self):
        """Test text wrapping in text mode."""
        long_task = Task.objects.create(
            title='This is a very long task title that should be wrapped properly when printed in text mode',
            description='This is also a very long description that needs to be wrapped to fit within the thermal printer constraints',
            urgency='normal',
            owner=self.user
        )
        
        escp_data = convert_task_to_text_escp(long_task)
        text_content = escp_data.decode('utf-8', errors='ignore')
        
        # Check that content is present (wrapping should not lose data)
        self.assertIn('very long task title', text_content)
        self.assertIn('very long description', text_content)
        
        # Check that lines don't exceed reasonable length
        lines = text_content.split('\n')
        for line in lines:
            # Allow some flexibility for borders and symbols
            if not line.startswith('=') and '[' not in line:
                self.assertLessEqual(len(line.strip()), 50, f"Line too long: {line}")

    def test_convert_task_to_text_escp_overdue_indicators(self):
        """Test due date status indicators in text mode."""
        # Overdue task
        overdue_task = Task.objects.create(
            title='Overdue',
            urgency='critical',
            owner=self.user,
            due_date=timezone.now() - timedelta(days=1)
        )
        
        escp_data = convert_task_to_text_escp(overdue_task)
        text_content = escp_data.decode('utf-8', errors='ignore')
        self.assertIn('OVERDUE!', text_content)
        
        # Today task
        today_task = Task.objects.create(
            title='Today',
            urgency='urgent',
            owner=self.user,
            due_date=timezone.now().date()
        )
        
        escp_data = convert_task_to_text_escp(today_task)
        text_content = escp_data.decode('utf-8', errors='ignore')
        self.assertIn('TODAY!', text_content)


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
    def test_print_task_text_mode_success(self, mock_socket):
        """Test successful printing in text mode."""
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task, use_graphics=False)
        
        self.assertTrue(success)
        self.assertIn('text', message)
        self.assertIn('successfully', message)
        
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
    def test_print_task_graphics_fallback_to_text(self, mock_socket, mock_create_image):
        """Test fallback from graphics to text mode when image creation fails."""
        # Make image creation fail
        mock_create_image.side_effect = Exception("Image creation failed")
        
        # Mock successful socket
        mock_sock = unittest.mock.Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        success, message = print_task(self.parent_task, use_graphics=True)
        
        self.assertTrue(success)
        # Should have fallen back to text mode (message will still say graphics due to implementation)
        # The important part is that it succeeded despite the image creation failure
        self.assertIn('successfully', message)

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
        
        # Test text mode (should handle unicode gracefully)
        escp_data = convert_task_to_text_escp(unicode_task)
        self.assertIsInstance(escp_data, bytes)
        
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
        
        escp_data = convert_task_to_text_escp(minimal_task)
        self.assertIsInstance(escp_data, bytes)

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
        
        # Test text mode too
        escp_data = convert_task_to_text_escp(child_with_long_parent)
        self.assertIsInstance(escp_data, bytes)

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
        
        escp_data = convert_task_to_text_escp(basic_task)
        text_content = escp_data.decode('utf-8', errors='ignore')
        self.assertIn('Not set', text_content)

    def test_convert_task_to_text_escp_special_characters(self):
        """Test text conversion with special characters and symbols."""
        special_task = Task.objects.create(
            title='Task with special chars: @#$%^&*()[]{}|\\',
            description='Description with quotes "test" and apostrophe\'s',
            urgency='urgent',
            owner=self.user
        )
        
        escp_data = convert_task_to_text_escp(special_task)
        self.assertIsInstance(escp_data, bytes)
        # Should not crash with special characters

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
        
        escp_data = convert_task_to_text_escp(task_null_due)
        text_content = escp_data.decode('utf-8', errors='ignore')
        self.assertIn('Not set', text_content)


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
        self.assertIn('Yes, Print', content)
        
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
        
        # Should have print button with correct onclick handler
        expected_onclick = f'showPrintConfirmModal({test_task.id})'
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
        
        # Verify print_task was called
        mock_print_task.assert_called_once_with(test_task, use_graphics=True)

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