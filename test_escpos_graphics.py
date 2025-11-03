#!/usr/bin/env python3
"""
Test the generate-escpos-graphics endpoint specifically.
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from tasks.models import Task

def test_escpos_graphics():
    print("🧪 Testing generate-escpos-graphics Endpoint")
    print("=" * 50)
    
    client = Client()
    
    # Get a user and login
    user = User.objects.first()
    if not user:
        print("❌ No users found")
        return
    
    client.force_login(user)
    print(f"✅ Logged in as: {user.username}")
    
    # Get a task
    task = Task.objects.first()
    if not task:
        print("❌ No tasks found")
        return
    
    print(f"✅ Using task: {task.title}")
    
    # Test data for ESC/POS graphics generation
    test_data = {
        'task': {
            'id': task.pk,
            'title': task.title,
            'description': task.description or '',
            'urgency': task.urgency,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat(),
            'hierarchy': [task.title]  # Should be a list, not an integer
        },
        'options': {
            'use_graphics': True,
            'format': 'bitmap',
            'printerWidth': '57mm'  # Test 57mm width
        }
    }
    
    print("\n🔄 Testing ESC/POS graphics generation with 57mm...")
    response = client.post(
        '/tasks/generate-escpos-graphics/',
        data=json.dumps(test_data),
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    print(f"📊 Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✅ Success: {result.get('success')}")
            if 'escpos_data' in result:
                print(f"📄 ESC/POS data length: {len(result['escpos_data'])}")
            if result.get('debug_info'):
                print(f"🐛 Debug info: {result['debug_info']}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"📄 Raw response: {response.content.decode()[:200]}...")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"📄 Response: {response.content.decode()[:200]}...")
    
    # Test with 80mm for comparison
    print("\n🔄 Testing ESC/POS graphics generation with 80mm...")
    test_data['options']['printerWidth'] = '80mm'
    
    response = client.post(
        '/tasks/generate-escpos-graphics/',
        data=json.dumps(test_data),
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    print(f"📊 Response status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"✅ Success: {result.get('success')}")
            if 'escpos_data' in result:
                print(f"📄 ESC/POS data length: {len(result['escpos_data'])}")
            if result.get('debug_info'):
                print(f"🐛 Debug info: {result['debug_info']}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print(f"📄 Raw response: {response.content.decode()[:200]}...")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(f"📄 Response: {response.content.decode()[:200]}...")
    
    print("\n" + "=" * 50)
    print("🏁 ESC/POS graphics test complete!")

if __name__ == '__main__':
    test_escpos_graphics()