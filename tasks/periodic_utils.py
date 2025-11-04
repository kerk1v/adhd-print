"""
Periodic Task Utilities

Functions for dynamically generating virtual periodic task instances 
and managing periodic task lifecycles.
"""

from django.utils import timezone
from django.db.models import Q
from datetime import timedelta


def get_todays_periodic_tasks(user):
    """
    Get virtual instances of periodic tasks that should occur today.

    Args:
        user: User object

    Returns:
        List of virtual task instances for today
    """
    from .models import Task
    
    today = timezone.now().date()
    virtual_instances = []
    
    # Get all active periodic templates for the user
    periodic_templates = Task.objects.filter(
        owner=user,
        is_periodic=True
    ).filter(
        # Only active templates (not ended)
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    )
    
    for template in periodic_templates:
        if template._should_occur_on_date(today):
            virtual_instance = template.get_virtual_instance_for_date(today)
            if virtual_instance:
                virtual_instances.append(virtual_instance)
    
    return virtual_instances


def get_upcoming_periodic_tasks(user, days_ahead=7):
    """
    Get virtual instances of periodic tasks due in the next N days.

    Args:
        user: User object
        days_ahead: Number of days to look ahead

    Returns:
        List of virtual task instances for the upcoming period
    """
    from .models import Task
    
    current_date = timezone.now().date()
    end_date = current_date + timedelta(days=days_ahead)
    virtual_instances = []
    
    # Get all active periodic templates for the user
    periodic_templates = Task.objects.filter(
        owner=user,
        is_periodic=True
    ).filter(
        # Only active templates (not ended)
        Q(end_date__isnull=True) | Q(end_date__gte=current_date)
    )
    
    for template in periodic_templates:
        occurrences = template.get_occurrences_in_range(current_date, end_date)
        for occurrence_date in occurrences:
            virtual_instance = template.get_virtual_instance_for_date(occurrence_date)
            if virtual_instance:
                virtual_instances.append(virtual_instance)
    
    # Sort by due date
    virtual_instances.sort(key=lambda x: x.due_date)
    return virtual_instances


def get_periodic_task_summary(periodic_task):
    """
    Get a summary of a periodic task's upcoming occurrences.

    Args:
        periodic_task: The periodic task template

    Returns:
        Dictionary with occurrence information and next occurrence
    """
    if not periodic_task.is_periodic:
        return None

    today = timezone.now().date()
    next_30_days = today + timedelta(days=30)
    
    # Get upcoming occurrences in the next 30 days
    upcoming_occurrences = periodic_task.get_occurrences_in_range(today, next_30_days)
    next_occurrence = periodic_task.get_next_occurrence(today)

    return {
        'upcoming_occurrences': len(upcoming_occurrences),
        'next_occurrence': next_occurrence,
        'is_active': next_occurrence is not None,
        'periodicity_type': periodic_task.periodicity_type
    }


def cleanup_expired_periodic_tasks():
    """
    Remove periodic task templates that have passed their end_date.
    """
    from .models import Task
    
    current_date = timezone.now().date()

    expired_tasks = Task.objects.filter(
        is_periodic=True,
        end_date__lt=current_date
    )

    deleted_count = 0
    for task in expired_tasks:
        task.delete()
        deleted_count += 1
        
    return deleted_count


def nightly_periodic_task_maintenance():
    """
    Perform nightly maintenance for periodic tasks.
    This replaces the old instance generation with cleanup of expired templates.

    Returns:
        Dictionary with maintenance statistics
    """
    from .models import MaintenanceLog
    
    start_time = timezone.now()
    
    try:
        # Clean up expired periodic templates
        templates_cleaned = cleanup_expired_periodic_tasks()
        
        end_time = timezone.now()
        runtime_seconds = (end_time - start_time).total_seconds()
        
        # Create maintenance log
        MaintenanceLog.objects.create(
            templates_processed=0,  # No longer relevant with dynamic approach
            instances_created=0,    # No longer creating instances
            instances_cleaned=0,    # No longer relevant
            templates_cleaned=templates_cleaned,
            runtime_seconds=runtime_seconds,
            success=True
        )
        
        return {
            'success': True,
            'templates_cleaned': templates_cleaned,
            'runtime_seconds': runtime_seconds,
            'errors': []
        }
        
    except Exception as e:
        end_time = timezone.now()
        runtime_seconds = (end_time - start_time).total_seconds()
        
        # Create error log
        MaintenanceLog.objects.create(
            templates_processed=0,
            instances_created=0,
            instances_cleaned=0,
            templates_cleaned=0,
            runtime_seconds=runtime_seconds,
            errors=[str(e)],
            success=False
        )
        
        return {
            'success': False,
            'templates_cleaned': 0,
            'runtime_seconds': runtime_seconds,
            'errors': [str(e)]
        }