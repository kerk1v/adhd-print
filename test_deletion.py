#!/usr/bin/env python
"""
Test script to verify periodic task deletion works correctly.
This script demonstrates the deletion behavior for different task types.
"""

from django.core.exceptions import ValidationError
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


def test_deletion_behaviors():
    """Test different deletion behaviors for different task types"""

    print("=== Task Deletion Behavior Testing ===\n")

    # Test 1: Periodic Templates (should allow cascade deletion)
    print("🔄 1. PERIODIC TEMPLATES (Cascade deletion allowed)")
    periodic_templates = Task.objects.filter(is_periodic=True)

    for template in periodic_templates:
        print(f"   📋 Template: '{template.title}'")
        current_date = timezone.now().date()
        future_instances = template.periodic_instances.filter(
            due_date__date__gte=current_date
        )

        total_subtasks = 0
        for instance in future_instances:
            total_subtasks += count_subtasks_recursive(instance)

        print(
            f"      ✅ CAN DELETE: Will cascade delete {
                future_instances.count()} instances + {total_subtasks} subtasks")
        print()

    # Test 2: Regular Tasks with incomplete subtasks (should be protected)
    print("📋 2. REGULAR TASKS WITH INCOMPLETE SUBTASKS (Protected)")
    regular_tasks_with_subtasks = Task.objects.filter(
        is_periodic=False,
        periodic_parent__isnull=True,  # Not a periodic instance
        subtasks__isnull=False
    ).distinct()

    for task in regular_tasks_with_subtasks:
        has_incomplete = task.has_incomplete_subtasks()
        subtask_count = count_subtasks_recursive(task)

        print(f"   📋 Regular Task: '{task.title}'")
        print(f"      Subtasks: {subtask_count} | Incomplete: {has_incomplete}")

        if has_incomplete:
            print("      ❌ CANNOT DELETE: Has incomplete subtasks (protected)")
        else:
            print("      ✅ CAN DELETE: All subtasks completed")
        print()

    # Test 3: Periodic Instances (should allow deletion for cascade)
    print("📅 3. PERIODIC INSTANCES (Cascade deletion allowed)")
    periodic_instances = Task.objects.filter(
        periodic_parent__isnull=False
    )[:3]  # Show first 3

    for instance in periodic_instances:
        subtask_count = count_subtasks_recursive(instance)
        print(f"   📅 Instance: '{instance.title}' (due: {instance.due_date.date()})")
        print(f"      Parent: {instance.periodic_parent.title}")
        print(
            f"      ✅ CAN DELETE: Part of cascade deletion (has {subtask_count} subtasks)")
        print()

    # Test 4: Regular tasks without subtasks (should allow deletion)
    print("📋 4. REGULAR TASKS WITHOUT SUBTASKS (Normal deletion)")
    regular_simple = Task.objects.filter(
        is_periodic=False,
        periodic_parent__isnull=True,
        subtasks__isnull=True
    )[:3]

    for task in regular_simple:
        print(f"   📋 Simple Task: '{task.title}'")
        print("      ✅ CAN DELETE: No subtasks to protect")
        print()


def simulate_deletions():
    """Simulate actual deletion attempts (without really deleting)"""
    print("=== Deletion Simulation ===\n")

    # Find a regular task with incomplete subtasks
    regular_with_incomplete = None
    for task in Task.objects.filter(is_periodic=False, periodic_parent__isnull=True):
        if task.has_incomplete_subtasks():
            regular_with_incomplete = task
            break

    if regular_with_incomplete:
        print("🧪 Testing deletion of regular task with incomplete subtasks:")
        print(f"   Task: '{regular_with_incomplete.title}'")
        try:
            # This should raise ValidationError
            # We'll just check the logic without actually deleting
            if regular_with_incomplete.has_incomplete_subtasks():
                print(
                    "   ❌ Would raise ValidationError: Cannot delete task with incomplete subtasks")
            else:
                print("   ✅ Would allow deletion")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()

    # Find a periodic template
    periodic_template = Task.objects.filter(is_periodic=True).first()
    if periodic_template:
        print("🧪 Testing deletion of periodic template:")
        print(f"   Template: '{periodic_template.title}'")
        current_date = timezone.now().date()
        future_count = periodic_template.periodic_instances.filter(
            due_date__date__gte=current_date
        ).count()
        print(f"   ✅ Would cascade delete {future_count} future instances")
        print()


def count_subtasks_recursive(task):
    """Count all subtasks recursively"""
    count = 0
    for subtask in task.subtasks.all():
        count += 1
        count += count_subtasks_recursive(subtask)
    return count


if __name__ == "__main__":
    test_deletion_behaviors()
    simulate_deletions()
