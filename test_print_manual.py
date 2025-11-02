#!/usr/bin/env python
"""
Manual test script for print functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from tasks.models import Task
from django.contrib.auth.models import User
from tasks.print_utils import print_task
import socket

def test_printer_connection():
    """Test if we can connect to the printer"""
    from django.conf import settings
    
    print(f"Testing printer connection to {settings.PRINTER_HOST}:{settings.PRINTER_PORT}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        result = sock.connect_ex((settings.PRINTER_HOST, settings.PRINTER_PORT))
        sock.close()
        
        if result == 0:
            print("✅ Printer connection successful!")
            return True
        else:
            print(f"❌ Printer connection failed (error code: {result})")
            return False
    except Exception as e:
        print(f"❌ Printer connection error: {e}")
        return False

def test_print_function():
    """Test the print function with sample data"""
    
    # Check if we have any users
    users = User.objects.all()
    print(f"Found {users.count()} users")
    
    if users.count() == 0:
        print("Creating test user...")
        user = User.objects.create_user(username='testuser', password='testpass')
    else:
        user = users.first()
        print(f"Using existing user: {user.username}")
    
    # Check if we have any tasks
    tasks = Task.objects.filter(owner=user)
    print(f"Found {tasks.count()} tasks for user {user.username}")
    
    if tasks.count() == 0:
        print("Creating test task...")
        task = Task.objects.create(
            title="Test Print Task",
            description="This is a test task for printing",
            urgency="high",
            priority=1,
            owner=user
        )
    else:
        task = tasks.first()
        print(f"Using existing task: {task.title}")
    
    print(f"\nTesting print function with task ID {task.id}...")
    
    # Test graphics mode printing
    print("Testing graphics mode printing...")
    success, message = print_task(task, use_graphics=True)
    print(f"Graphics mode result: {success}, message: {message}")

if __name__ == "__main__":
    print("=== ADHD Print Manual Test ===\n")
    
    # Test 1: Printer connection
    print("1. Testing printer connection...")
    printer_connected = test_printer_connection()
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Print function
    print("2. Testing print function...")
    test_print_function()
    
    print("\n" + "="*50)
    print("Test completed!")
    
    if not printer_connected:
        print("\n⚠️  WARNING: Printer connection failed!")
        print("   - Check if printer is on and connected to network")
        print("   - Verify PRINTER_HOST and PRINTER_PORT in settings")
        print("   - Current settings: PRINTER_HOST=192.168.1.40, PRINTER_PORT=9100")