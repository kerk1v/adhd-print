#!/usr/bin/env python3
"""
Test script to specifically verify 57mm printer width support.
"""

import os
import sys
import django
import json
from django.test import Client

# Add the project directory to Python path
sys.path.append('/Users/volker/adhd-print')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from tasks.models import Task
from django.contrib.auth.models import User

def test_57mm_support():
    print("🧪 Testing 57mm Printer Width Support")
    print("=" * 50)
    
    # Get a user for the task
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return
    
    # Get or create a test task
    task, created = Task.objects.get_or_create(
        title="Test 57mm Printer",
        defaults={
            'description': "Testing 57mm printer width parameter flow",
            'urgency': 'normal',
            'owner': user
        }
    )
    
    if created:
        print(f"✅ Created test task: {task.id}")
    else:
        print(f"✅ Using existing task: {task.id}")
    
    client = Client()
    
    # Test 1: Server-side printing with 57mm
    print("\n🔄 Testing server-side printing with 57mm...")
    response = client.post(
        f'/tasks/print/{task.id}/',
        data=json.dumps({'printerWidth': '57mm'}),
        content_type='application/json'
    )
    
    print(f"📊 Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result.get('success')}")
        print(f"📄 Print method: {result.get('print_method')}")
    else:
        print(f"❌ Error: {response.content}")
    
    # Test 2: ESC/POS graphics generation with 57mm
    print("\n🔄 Testing ESC/POS graphics generation with 57mm...")
    test_data = {
        'task': {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'urgency': task.urgency,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat(),
            'hierarchy': 0
        },
        'options': {
            'use_graphics': True,
            'format': 'bitmap',
            'printerWidth': '57mm'
        }
    }
    
    response = client.post(
        '/tasks/generate-escpos-graphics/',
        data=json.dumps(test_data),
        content_type='application/json'
    )
    
    print(f"📊 Response status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: {result.get('success')}")
        if 'escpos_data' in result:
            print(f"📄 ESC/POS data length: {len(result['escpos_data'])}")
    else:
        print(f"❌ Error: {response.content}")
    
    # Test 3: Compare 57mm vs 80mm image sizes
    print("\n🔄 Testing image size differences...")
    
    # Test with both widths
    for width in ['57mm', '80mm']:
        test_data['options']['printerWidth'] = width
        
        response = client.post(
            '/tasks/generate-escpos-graphics/',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'escpos_data' in result:
                data_length = len(result['escpos_data'])
                print(f"📏 {width}: ESC/POS data length = {data_length}")
        else:
            print(f"❌ {width} failed: {response.content}")
    
    print("\n" + "=" * 50)
    print("🏁 Test complete!")

if __name__ == '__main__':
    test_57mm_support()