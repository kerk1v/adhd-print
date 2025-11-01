#!/usr/bin/env python
"""
Test script to verify that subtasks are automatically created for existing periodic instances
when new subtasks are added to periodic templates.
"""

from tasks.periodic_utils import generate_periodic_task_instances
from django.utils import timezone
from django.contrib.auth.models import User
from tasks.models import Task
import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/Users/volker/adhd-print')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()


def test_dynamic_subtask_creation():
    """Test that new subtasks are automatically created for existing periodic instances"""

    print("=== Dynamic Subtask Creation Test ===\n")

    # Find or create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )

    # Create a simple periodic template for testing
    periodic_template = Task.objects.create(
        title="Test Periodic Template",
        description="Testing dynamic subtask creation",
        owner=user,
        is_periodic=True,
        start_date=timezone.now().date(),
        periodicity_type='daily',
        urgency='normal'
    )

    print(f"✅ Created periodic template: '{periodic_template.title}'")

    # Generate some instances
    instances = generate_periodic_task_instances(periodic_template, days_ahead=5)
    print(f"✅ Generated {len(instances)} periodic instances")

    # Show initial state
    for i, instance in enumerate(instances[:3], 1):
        subtask_count = instance.subtasks.count()
        print(f"   Instance {i}: {instance.due_date.date()} - {subtask_count} subtasks")

    print()

    # Now add a new subtask to the periodic template
    print("🔧 Adding new subtask to periodic template...")
    new_subtask = Task.objects.create(
        title="New Dynamic Subtask",
        description="This should appear in all existing instances",
        owner=user,
        parent=periodic_template,
        urgency='normal'
    )

    print(f"✅ Created new subtask: '{new_subtask.title}'")
    print()

    # Check if the subtask was automatically added to existing instances
    print("📊 Checking existing instances after subtask creation:")

    # Refresh instances from database
    updated_instances = periodic_template.periodic_instances.filter(
        due_date__date__gte=timezone.now().date()
    ).order_by('due_date')

    for i, instance in enumerate(updated_instances[:3], 1):
        subtask_count = instance.subtasks.count()
        subtasks = list(instance.subtasks.values_list('title', flat=True))
        print(f"   Instance {i}: {instance.due_date.date()} - {subtask_count} subtasks")
        for subtask_title in subtasks:
            print(f"      • {subtask_title}")

    print()

    # Test adding a sub-subtask
    print("🔧 Adding sub-subtask to the new subtask...")
    sub_subtask = Task.objects.create(
        title="Sub-subtask Level 2",
        description="This should also appear in all instances",
        owner=user,
        parent=new_subtask,
        urgency='normal'
    )

    print(f"✅ Created sub-subtask: '{sub_subtask.title}'")
    print()

    # Check final state
    print("📊 Final state after sub-subtask creation:")

    # Refresh instances again
    final_instances = periodic_template.periodic_instances.filter(
        due_date__date__gte=timezone.now().date()
    ).order_by('due_date')

    for i, instance in enumerate(final_instances[:3], 1):
        print(f"   Instance {i}: {instance.due_date.date()}")
        show_subtask_hierarchy(instance, "      ")

    print()
    print("🧹 Cleaning up test data...")

    # Clean up test data
    periodic_template.delete()  # This should cascade delete all instances

    if created:
        user.delete()

    print("✅ Test completed successfully!")


def show_subtask_hierarchy(task, indent=""):
    """Recursively show subtask hierarchy"""
    for subtask in task.subtasks.all():
        print(f"{indent}• {subtask.title}")
        show_subtask_hierarchy(subtask, indent + "  ")


if __name__ == "__main__":
    test_dynamic_subtask_creation()
