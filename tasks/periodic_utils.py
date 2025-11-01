"""
Periodic Task Utilities

Functions for generating task instances from periodic task templates
and managing periodic task lifecycles.
"""

from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import Task


def generate_periodic_task_instances(periodic_task, days_ahead=28):
    """
    Generate task instances for a periodic task template.

    Args:
        periodic_task: The periodic task template
        days_ahead: How many days ahead to generate instances
                   (default: 28 days = 4 weeks)

    Returns:
        List of created task instances
    """
    if not periodic_task.is_periodic:
        return []

    created_instances = []
    current_date = timezone.now().date()
    end_date = current_date + timedelta(days=days_ahead)

    # If periodic task has an end_date, don't generate beyond it
    if periodic_task.end_date and periodic_task.end_date < end_date:
        end_date = periodic_task.end_date

    # Start generating from the next occurrence
    next_date = periodic_task.get_next_occurrence(current_date)

    while next_date and next_date <= end_date:
        # Check if an instance for this date already exists
        existing_instance = Task.objects.filter(
            periodic_parent=periodic_task,
            due_date__date=next_date,
            owner=periodic_task.owner
        ).first()

        if not existing_instance:
            # Create new instance
            instance = Task(
                title=periodic_task.title,
                description=periodic_task.description,
                urgency=periodic_task.urgency,
                due_date=timezone.datetime.combine(
                    next_date, timezone.datetime.min.time().replace(
                        tzinfo=timezone.get_current_timezone())),
                owner=periodic_task.owner,
                periodic_parent=periodic_task,
                is_periodic=False  # Instances are not periodic themselves
            )
            instance.save()
            created_instances.append(instance)

            # Create subtask instances for this periodic instance
            _create_subtask_instances(periodic_task, instance, next_date)

        # Find next occurrence
        next_date = periodic_task.get_next_occurrence(next_date + timedelta(days=1))

    return created_instances


def _create_subtask_instances(periodic_parent, instance_parent, due_date):
    """
    Recursively create subtask instances for a periodic task instance.

    Args:
        periodic_parent: The original periodic task template
        instance_parent: The periodic instance to create subtasks for
        due_date: The due date for the subtasks
    """
    # Get all direct subtasks of the periodic parent
    subtasks = periodic_parent.subtasks.all()

    for subtask in subtasks:
        # Create subtask instance
        subtask_instance = Task(
            title=subtask.title,
            description=subtask.description,
            urgency=subtask.urgency,
            due_date=timezone.datetime.combine(
                due_date, timezone.datetime.min.time().replace(
                    tzinfo=timezone.get_current_timezone())),
            owner=subtask.owner,
            # Parent is the periodic instance, not the original periodic task
            parent=instance_parent,
            is_periodic=False
        )
        subtask_instance.save()

        # Recursively create sub-subtasks
        _create_subtask_instances(subtask, subtask_instance, due_date)


def update_periodic_task_instances(periodic_task):
    """
    Update existing instances when a periodic task template is modified.
    Only updates incomplete instances.

    Args:
        periodic_task: The periodic task template that was updated
    """
    if not periodic_task.is_periodic:
        return

    # Update incomplete instances
    incomplete_instances = Task.objects.filter(
        periodic_parent=periodic_task,
        done=False,
        due_date__gte=timezone.now()
    )

    for instance in incomplete_instances:
        instance.title = periodic_task.title
        instance.description = periodic_task.description
        instance.urgency = periodic_task.urgency
        instance.save()


def cleanup_expired_periodic_tasks():
    """
    Remove periodic task templates that have passed their end_date
    and have no incomplete instances.
    """
    current_date = timezone.now().date()

    expired_tasks = Task.objects.filter(
        is_periodic=True,
        end_date__lt=current_date
    )

    for task in expired_tasks:
        # Check if there are any incomplete instances
        incomplete_instances = task.periodic_instances.filter(done=False)
        if not incomplete_instances.exists():
            task.delete()


def get_periodic_task_summary(periodic_task):
    """
    Get a summary of a periodic task's instances.

    Args:
        periodic_task: The periodic task template

    Returns:
        Dictionary with instance counts and next occurrence
    """
    if not periodic_task.is_periodic:
        return None

    total_instances = periodic_task.periodic_instances.count()
    completed_instances = periodic_task.periodic_instances.filter(done=True).count()
    pending_instances = periodic_task.periodic_instances.filter(done=False).count()
    next_occurrence = periodic_task.get_next_occurrence()

    return {
        'total_instances': total_instances,
        'completed_instances': completed_instances,
        'pending_instances': pending_instances,
        'next_occurrence': next_occurrence,
        'completion_rate': (
            (completed_instances * 100) / total_instances
        ) if total_instances > 0 else 0}


def get_todays_periodic_tasks(user):
    """
    Get all periodic task instances due today for a user.

    Args:
        user: User object

    Returns:
        QuerySet of today's periodic task instances
    """
    today = timezone.now().date()

    return Task.objects.filter(
        owner=user,
        periodic_parent__isnull=False,  # Only periodic instances
        due_date=today,
        done=False
    ).order_by('periodic_parent__title', 'title')


def get_upcoming_periodic_tasks(user, days_ahead=7):
    """
    Get all periodic task instances due in the next N days for a user.

    Args:
        user: User object
        days_ahead: Number of days to look ahead

    Returns:
        QuerySet of upcoming periodic task instances
    """
    current_date = timezone.now()
    future_date = current_date + timedelta(days=days_ahead)

    return Task.objects.filter(
        owner=user,
        periodic_parent__isnull=False,  # Only periodic instances
        due_date__range=(current_date, future_date),
        done=False
    ).order_by('due_date')


def handle_periodic_task_completion(task_instance):
    """
    Handle completion of a periodic task instance.
    Generate next occurrence if needed.

    Args:
        task_instance: The completed task instance
    """
    if not task_instance.periodic_parent:
        return

    periodic_task = task_instance.periodic_parent

    # Generate next occurrence if within reasonable timeframe
    next_occurrences = generate_periodic_task_instances(periodic_task, days_ahead=30)

    return next_occurrences


def create_subtask_instances_for_existing_periodic_instances(new_subtask):
    """
    When a new subtask is added to a periodic template, create corresponding
    subtask instances for all existing periodic instances.

    Args:
        new_subtask: The newly created subtask of a periodic template
    """
    # Find the periodic template by traversing up the hierarchy
    current_task = new_subtask
    periodic_template = None

    # Traverse up the parent chain to find the periodic template
    while current_task.parent:
        if current_task.parent.is_periodic:
            periodic_template = current_task.parent
            break
        current_task = current_task.parent

    # If we found a periodic template, create instances for existing periodic instances
    if periodic_template:
        # Get all existing instances of this periodic template
        current_date = timezone.now().date()
        existing_instances = periodic_template.periodic_instances.filter(
            due_date__date__gte=current_date,  # Only future instances
            done=False  # Only incomplete instances
        )

        # For each existing instance, find the corresponding parent for this subtask
        for instance in existing_instances:
            # Find the corresponding parent in the instance hierarchy
            instance_parent = _find_corresponding_parent_in_instance(
                new_subtask, instance, periodic_template)

            if instance_parent:
                _create_subtask_instance_for_specific_parent(
                    new_subtask, instance_parent, instance.due_date.date())


def _find_corresponding_parent_in_instance(
        template_subtask, instance, periodic_template):
    """
    Find the corresponding parent in the instance hierarchy for a template subtask.

    Args:
        template_subtask: The template subtask we want to create an instance for
        instance: The periodic instance we're working with
        periodic_template: The root periodic template

    Returns:
        The task in the instance hierarchy that should be the parent
    """
    # If the template subtask's parent is the periodic template itself,
    # then the instance should be the parent
    if template_subtask.parent == periodic_template:
        return instance

    # Otherwise, we need to find the corresponding subtask in the instance
    # by traversing the hierarchy path
    template_path = []
    current = template_subtask.parent

    # Build the path from template subtask up to (but not including) the
    # periodic template
    while current and current != periodic_template:
        template_path.append(current.title)
        current = current.parent

    # Now traverse down the instance hierarchy following the same path
    current_instance_parent = instance
    for title in reversed(template_path):
        # Find the subtask with this title under the current parent
        matching_subtask = current_instance_parent.subtasks.filter(title=title).first()
        if matching_subtask:
            current_instance_parent = matching_subtask
        else:
            # Path doesn't exist in instance, can't create this subtask yet
            return None

    return current_instance_parent


def _create_subtask_instance_for_specific_parent(
        template_subtask, instance_parent, due_date):
    """
    Create a subtask instance for a specific periodic instance parent.
    This mirrors the structure from the template.

    Args:
        template_subtask: The template subtask to replicate
        instance_parent: The periodic instance to attach the subtask to
        due_date: The due date for the new subtask instance
    """
    # Create the subtask instance
    subtask_instance = Task(
        title=template_subtask.title,
        description=template_subtask.description,
        urgency=template_subtask.urgency,
        due_date=timezone.datetime.combine(
            due_date,
            timezone.datetime.min.time().replace(
                tzinfo=timezone.get_current_timezone())),
        owner=template_subtask.owner,
        parent=instance_parent,
        is_periodic=False)
    subtask_instance.save()

    # Recursively create any sub-subtasks
    for sub_subtask in template_subtask.subtasks.all():
        _create_subtask_instance_for_specific_parent(
            sub_subtask, subtask_instance, due_date)

    return subtask_instance


def update_existing_periodic_instances_with_new_subtask(periodic_template):
    """
    When a periodic template is modified, ensure all existing instances
    have the complete subtask hierarchy.

    Args:
        periodic_template: The periodic task template that was updated
    """
    if not periodic_template.is_periodic:
        return

    current_date = timezone.now().date()
    existing_instances = periodic_template.periodic_instances.filter(
        due_date__date__gte=current_date,
        done=False
    )

    for instance in existing_instances:
        # Get all template subtasks
        template_subtasks = periodic_template.subtasks.all()

        # For each template subtask, check if instance has corresponding subtask
        for template_subtask in template_subtasks:
            # Check if this subtask already exists for the instance
            existing_instance_subtask = instance.subtasks.filter(
                title=template_subtask.title
            ).first()

            if not existing_instance_subtask:
                # Create the missing subtask hierarchy
                _create_subtask_instance_for_specific_parent(
                    template_subtask,
                    instance,
                    instance.due_date.date()
                )


def generate_all_periodic_instances(days_ahead=28):
    """
    Generate instances for all active periodic tasks.
    This function is designed to be run by scheduled jobs.

    Args:
        days_ahead: How many days ahead to generate instances
                   (default: 28 days = 4 weeks)

    Returns:
        Dictionary with statistics about generated instances
    """
    stats = {
        'processed_templates': 0,
        'total_instances_created': 0,
        'templates_processed': [],
        'errors': []
    }

    # Get all active periodic templates
    current_date = timezone.now().date()
    active_periodic_tasks = Task.objects.filter(
        is_periodic=True
    ).filter(
        # Only process templates that haven't ended or end in the future
        Q(end_date__isnull=True) | Q(end_date__gte=current_date)
    )

    for periodic_task in active_periodic_tasks:
        try:
            # Generate instances for this template
            created_instances = generate_periodic_task_instances(
                periodic_task, days_ahead)

            stats['processed_templates'] += 1
            stats['total_instances_created'] += len(created_instances)
            stats['templates_processed'].append({
                'template_id': periodic_task.id,
                'template_title': periodic_task.title,
                'owner': periodic_task.owner.username,
                'instances_created': len(created_instances)
            })

        except Exception as e:
            stats['errors'].append({
                'template_id': periodic_task.id,
                'template_title': periodic_task.title,
                'error': str(e)
            })

    return stats


def cleanup_old_periodic_instances(days_to_keep=30):
    """
    Clean up old completed periodic instances to prevent database bloat.
    Keeps recent completed instances for reference but removes very old ones.

    Args:
        days_to_keep: How many days of completed instances to keep

    Returns:
        Number of instances deleted
    """
    cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)

    # Find old completed periodic instances
    old_instances = Task.objects.filter(
        periodic_parent__isnull=False,  # Only periodic instances
        done=True,  # Only completed instances
        due_date__date__lt=cutoff_date  # Older than cutoff
    )

    deleted_count = 0
    for instance in old_instances:
        try:
            # Use the model's delete method to handle subtask cleanup
            instance.delete()
            deleted_count += 1
        except Exception:
            # Skip instances that can't be deleted (e.g., with constraints)
            pass

    return deleted_count


def nightly_periodic_task_maintenance():
    """
    Main function for nightly maintenance of periodic tasks.
    This should be called by the scheduled job system.

    Returns:
        Dictionary with maintenance statistics
    """
    maintenance_stats = {
        'timestamp': timezone.now(),
        'generation_stats': None,
        'cleanup_stats': None,
        'total_runtime_seconds': 0
    }

    start_time = timezone.now()

    try:
        # Generate new instances (4 weeks ahead)
        maintenance_stats['generation_stats'] = generate_all_periodic_instances(
            days_ahead=28)

        # Clean up old completed instances (keep last 30 days)
        deleted_count = cleanup_old_periodic_instances(days_to_keep=30)

        # Clean up expired periodic task templates
        expired_tasks_before = Task.objects.filter(
            is_periodic=True,
            end_date__lt=timezone.now().date()
        ).count()
        cleanup_expired_periodic_tasks()
        expired_tasks_after = Task.objects.filter(
            is_periodic=True,
            end_date__lt=timezone.now().date()
        ).count()
        expired_templates_deleted = expired_tasks_before - expired_tasks_after

        maintenance_stats['cleanup_stats'] = {
            'deleted_instances': deleted_count,
            'deleted_expired_templates': expired_templates_deleted
        }

    except Exception as e:
        maintenance_stats['error'] = str(e)

    end_time = timezone.now()
    maintenance_stats['total_runtime_seconds'] = (end_time - start_time).total_seconds()

    return maintenance_stats
