#!/usr/bin/env python
"""
Test the print endpoint with proper authentication using Django test client
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from tasks.models import Task
import json

def test_print_endpoint_with_auth():
    """Test print endpoint with proper authentication"""
    
    client = Client()
    
    # Get a user
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return False
    
    print(f"✅ Found user: {user.username}")
    
    # Get a task owned by this user
    task = Task.objects.filter(owner=user).first()
    if not task:
        print("❌ No tasks found for this user")
        return False
    
    print(f"✅ Found task: ID {task.id} - '{task.title}'")
    
    # Force login (bypassing password check for testing)
    client.force_login(user)
    print("✅ User logged in successfully")
    
    # Test the print endpoint
    print(f"\n🔄 Testing print endpoint: /tasks/print/{task.id}/")
    
    response = client.post(
        f'/tasks/print/{task.id}/',
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Simulate AJAX
    )
    
    print(f"📊 Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = json.loads(response.content.decode())
            print(f"📄 Response data: {json.dumps(data, indent=2)}")
            
            if data.get('success'):
                print("✅ Print endpoint working correctly!")
                return True
            else:
                print(f"❌ Print failed: {data.get('message', 'Unknown error')}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"📄 Raw response: {response.content.decode()[:200]}...")
            return False
    else:
        print(f"❌ HTTP error {response.status_code}")
        print(f"📄 Response content: {response.content.decode()[:200]}...")
        return False

def test_actual_printing():
    """Test if the printer actually receives the data"""
    from tasks.print_utils import print_task
    from django.conf import settings
    
    # Get a task
    task = Task.objects.first()
    if not task:
        print("❌ No tasks found for direct printing test")
        return False
    
    print(f"\n🖨️  Testing direct printing for task: {task.title}")
    print(f"🖨️  Printer settings: {settings.PRINTER_HOST}:{settings.PRINTER_PORT}")
    
    # Test text mode first (safer)
    success, message = print_task(task, use_graphics=False)
    print(f"📊 Text mode result: {success} - {message}")
    
    # Test graphics mode
    success, message = print_task(task, use_graphics=True)
    print(f"📊 Graphics mode result: {success} - {message}")
    
    return success

if __name__ == "__main__":
    print("🧪 Testing ADHD Print Modal Functionality")
    print("=" * 50)
    
    # Test 1: Print endpoint with authentication
    endpoint_works = test_print_endpoint_with_auth()
    
    print("\n" + "=" * 50)
    
    # Test 2: Direct printing
    printing_works = test_actual_printing()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY:")
    print(f"   Print Endpoint: {'✅ Working' if endpoint_works else '❌ Failed'}")
    print(f"   Direct Printing: {'✅ Working' if printing_works else '❌ Failed'}")
    
    if endpoint_works and printing_works:
        print("\n🎉 Backend is working! The issue is likely in the frontend JavaScript.")
        print("💡 Suggested debugging steps:")
        print("   1. Check browser console for JavaScript errors")
        print("   2. Verify the print modal JavaScript is loading")
        print("   3. Check if event handlers are properly bound")
        print("   4. Test the showPrintConfirmModal() function directly")
    elif endpoint_works and not printing_works:
        print("\n⚠️  Endpoint works but printing fails - check printer configuration")
    elif not endpoint_works:
        print("\n❌ Print endpoint has issues - this needs to be fixed first")
    
    print("=" * 50)