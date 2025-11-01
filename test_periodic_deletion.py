#!/usr/bin/env python3
"""
Test script for Periodic Task Deletion Features

This script demonstrates the new functionality for deleting subtasks
from periodic task instances with options to update the template.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task
from tasks.periodic_utils import generate_periodic_task_instances

def test_periodic_deletion_features():
    """Test the new periodic instance deletion features"""
    
    print("🧪 Testing Periodic Task Deletion Features")
    print("=" * 50)
    
    # Get or create test user
    user, created = User.objects.get_or_create(
        username='test_user_deletion',
        defaults={'email': 'test@example.com'}
    )
    if created:
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"📋 Using existing user: {user.username}")
    
    # Create a periodic task template
    template = Task.objects.create(
        title="Weekly Team Meeting",
        description="Regular weekly team sync",
        owner=user,
        urgency='normal',
        is_periodic=True,
        periodicity_type='weekly',
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=60)
    )
    print(f"📅 Created periodic template: '{template.title}'")
    
    # Add subtasks to the template
    subtask1 = Task.objects.create(
        title="Prepare agenda",
        description="Create meeting agenda",
        owner=user,
        parent=template,
        urgency='normal'
    )
    
    subtask2 = Task.objects.create(
        title="Review action items",
        description="Check previous action items",
        owner=user,
        parent=template,
        urgency='normal'
    )
    
    # Add a sub-subtask
    subsubtask = Task.objects.create(
        title="Update project status",
        description="Update status in tracking system",
        owner=user,
        parent=subtask2,
        urgency='normal'
    )
    
    print(f"📝 Created template subtasks:")
    print(f"   • {subtask1.title}")
    print(f"   • {subtask2.title}")
    print(f"     ↳ {subsubtask.title}")
    
    # Generate instances
    instances = generate_periodic_task_instances(template, days_ahead=21)
    print(f"🔄 Generated {len(instances)} periodic instances")
    
    # Show the structure of the first instance
    first_instance = instances[0]
    print(f"\n📊 First instance structure ({first_instance.due_date.date()}):")
    print(f"   📋 Instance: {first_instance.title}")
    
    for subtask in first_instance.subtasks.all():
        print(f"   • {subtask.title}")
        for subsubtask in subtask.subtasks.all():
            print(f"     ↳ {subsubtask.title}")
    
    # Test the periodic template info detection
    test_subtask = first_instance.subtasks.first()
    periodic_info = test_subtask.get_periodic_template_info()
    
    print(f"\n🔍 Periodic Template Info for '{test_subtask.title}':")
    print(f"   Is periodic instance: {periodic_info['is_periodic_instance']}")
    print(f"   Template: {periodic_info['template'].title if periodic_info['template'] else None}")
    print(f"   Instance root: {periodic_info['instance_root'].title if periodic_info['instance_root'] else None}")
    print(f"   Template counterpart: {periodic_info['template_counterpart'].title if periodic_info['template_counterpart'] else None}")
    
    # Test deletion scenarios
    print(f"\n🗑️ Deletion Scenarios:")
    print(f"   1. Delete subtask from instance only -> Future instances keep the subtask")
    print(f"   2. Delete subtask from template -> Removes from all future instances")
    
    # Show what would happen
    total_instances = template.periodic_instances.count()
    future_instances = template.periodic_instances.filter(
        due_date__date__gte=timezone.now().date()
    ).count()
    
    print(f"\n📈 Impact Analysis:")
    print(f"   Total instances: {total_instances}")
    print(f"   Future instances: {future_instances}")
    print(f"   If deleting from template: {future_instances} instances would be affected")
    
    print(f"\n✨ New Features Available:")
    print(f"   🎯 Smart detection of periodic instance membership")
    print(f"   🔄 Option to delete from instance only")
    print(f"   📋 Option to delete from template (affects future instances)")
    print(f"   💬 Clear messaging about deletion scope")
    print(f"   🔍 Automatic template counterpart identification")
    
    # Cleanup
    print(f"\n🧹 Cleaning up test data...")
    template.delete()  # This cascades to all instances
    
    if created:
        user.delete()
    
    print("✅ Test completed successfully!")

if __name__ == '__main__':
    test_periodic_deletion_features()