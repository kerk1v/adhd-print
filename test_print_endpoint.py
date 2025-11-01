#!/usr/bin/env python
"""
Test the Django print view endpoint directly
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

def test_print_endpoint():
    """Test the /tasks/print/<id>/ endpoint"""
    
    # Create test client
    client = Client()
    
    # Get a user and task
    user = User.objects.first()
    if not user:
        print("No users found, creating test user...")
        user = User.objects.create_user(username='testuser', password='testpass')
    
    task = Task.objects.filter(owner=user).first()
    if not task:
        print("No tasks found, creating test task...")
        task = Task.objects.create(
            title="Test Print Task",
            description="Test task for endpoint testing",
            urgency="normal",
            priority=1,
            owner=user
        )
    
    print(f"Testing with user: {user.username}, task: {task.title} (ID: {task.id})")
    
    # Test 1: Unauthenticated request (should redirect)
    print("\n1. Testing unauthenticated request...")
    response = client.post(f'/tasks/print/{task.id}/', content_type='application/json')
    print(f"   Status: {response.status_code} (expected: 302 redirect)")
    
    # Test 2: Authenticated request
    print("\n2. Testing authenticated request...")
    client.login(username=user.username, password='testpass')
    
    response = client.post(f'/tasks/print/{task.id}/', content_type='application/json')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = json.loads(response.content)
            print(f"   Success: {data.get('success', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
        except json.JSONDecodeError:
            print(f"   Response content: {response.content}")
    else:
        print(f"   Response: {response.content}")
    
    # Test 3: Request with CSRF token (simulating AJAX)
    print("\n3. Testing request with CSRF token...")
    
    # Get CSRF token
    csrf_response = client.get('/tasks/')
    csrf_token = csrf_response.context['csrf_token']
    
    response = client.post(
        f'/tasks/print/{task.id}/',
        content_type='application/json',
        HTTP_X_CSRFTOKEN=str(csrf_token),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = json.loads(response.content)
            print(f"   Success: {data.get('success', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
            
            if data.get('success'):
                print("   ✅ Print endpoint working correctly!")
            else:
                print("   ❌ Print failed at backend level")
        except json.JSONDecodeError:
            print(f"   Response content: {response.content}")
    else:
        print(f"   Response: {response.content}")
        
    # Test 4: Try to print another user's task (should fail)
    print("\n4. Testing user isolation...")
    other_user = User.objects.exclude(id=user.id).first()
    if other_user:
        other_task = Task.objects.filter(owner=other_user).first()
        if other_task:
            response = client.post(
                f'/tasks/print/{other_task.id}/',
                content_type='application/json',
                HTTP_X_CSRFTOKEN=str(csrf_token),
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            print(f"   Status: {response.status_code} (expected: 404)")
        else:
            print("   No tasks from other users to test with")
    else:
        print("   No other users to test with")

if __name__ == "__main__":
    print("=== Testing Django Print Endpoint ===\n")
    test_print_endpoint()
    print("\nTest completed!")