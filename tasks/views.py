from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from .models import Task
from .forms import TaskForm
from .print_utils import print_task
from .periodic_utils import (
    generate_periodic_task_instances,
    update_periodic_task_instances,
    handle_periodic_task_completion,
    get_periodic_task_summary,
    get_todays_periodic_tasks
)


def welcome(request):
    """Welcome page - redirects authenticated users to task list"""
    if request.user.is_authenticated:
        return redirect('task_list')
    return render(request, 'tasks/welcome.html')


@login_required
def task_list(request):
    """Display hierarchical task list in three columns"""
    # Get selected task IDs from URL parameters
    selected_level1 = request.GET.get('level1')
    selected_level2 = request.GET.get('level2')

    # Convert to integers for comparison
    try:
        selected_level1_int = int(selected_level1) if selected_level1 else None
    except (ValueError, TypeError):
        selected_level1_int = None

    try:
        selected_level2_int = int(selected_level2) if selected_level2 else None
    except (ValueError, TypeError):
        selected_level2_int = None

    # Column 1: Root tasks (no parent) - exclude periodic task instances
    root_tasks = Task.objects.filter(
        parent__isnull=True,
        owner=request.user,
        periodic_parent__isnull=True  # Exclude periodic instances from main list
    ).order_by('-created_at')

    # Add selection state to each task
    for task in root_tasks:
        task.is_selected = (selected_level1_int ==
                            task.id) if selected_level1_int else False
        # Add periodic task summary if it's a periodic task
        if task.is_periodic:
            task.periodic_summary = get_periodic_task_summary(task)

    # Column 2: Subtasks of selected level 1 task
    level2_tasks = []
    selected_level1_task = None
    if selected_level1_int:
        try:
            selected_level1_task = Task.objects.get(
                id=selected_level1_int, owner=request.user, parent__isnull=True)
            level2_tasks = selected_level1_task.subtasks.all().order_by('-created_at')
            # Add selection state to level 2 tasks
            for task in level2_tasks:
                task.is_selected = (
                    selected_level2_int == task.id) if selected_level2_int else False
        except Task.DoesNotExist:
            pass

    # Column 3: Sub-subtasks of selected level 2 task
    level3_tasks = []
    selected_level2_task = None
    if selected_level2_int and selected_level1_task:
        try:
            selected_level2_task = Task.objects.get(
                id=selected_level2_int,
                owner=request.user,
                parent=selected_level1_task
            )
            level3_tasks = selected_level2_task.subtasks.all().order_by('-created_at')
            # Level 3 tasks don't have selection highlighting
            for task in level3_tasks:
                task.is_selected = False
        except Task.DoesNotExist:
            pass

    # Get upcoming periodic task instances for sidebar
    upcoming_periodic = Task.objects.filter(
        owner=request.user,
        periodic_parent__isnull=False,
        due_date__gte=timezone.now(),
        done=False
    ).order_by('due_date')[:5]  # Show next 5 upcoming

    context = {
        'root_tasks': root_tasks,
        'level2_tasks': level2_tasks,
        'level3_tasks': level3_tasks,
        'selected_level1': selected_level1,
        'selected_level2': selected_level2,
        'selected_level1_task': selected_level1_task,
        'selected_level2_task': selected_level2_task,
        'selected_level1_int': selected_level1_int,
        'selected_level2_int': selected_level2_int,
        'upcoming_periodic': upcoming_periodic,
        'user': request.user
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create(request, parent_id=None):
    """Create a new task"""
    parent_task = None
    if parent_id:
        parent_task = get_object_or_404(Task, id=parent_id, owner=request.user)
        if not parent_task.can_add_subtask():
            messages.error(
                request,
                "Cannot add subtasks to this task. Maximum nesting level reached.")
            return redirect('task_list')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.parent = parent_task

            # Handle periodic task details
            if task.is_periodic:
                # Periodic tasks cannot be subtasks
                if parent_task:
                    messages.error(request, "Periodic tasks cannot be subtasks.")
                    return render(request,
                                  'tasks/task_form.html',
                                  {'form': form,
                                   'parent_task': parent_task,
                                   'action': 'Create'})

                # Save periodicity details from form
                if form.cleaned_data.get('periodicity_detail'):
                    task.periodicity_detail = form.cleaned_data['periodicity_detail']

            try:
                task.save()

                # Generate initial instances for periodic tasks
                if task.is_periodic:
                    instances = generate_periodic_task_instances(task, days_ahead=60)
                    messages.success(
                        request, f'Periodic task "{
                            task.title}" created successfully! Generated {
                            len(instances)} upcoming instances.')
                else:
                    messages.success(
                        request, f'Task "{
                            task.title}" created successfully!')

                return redirect('task_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TaskForm()

    context = {
        'form': form,
        'parent_task': parent_task,
        'action': 'Create'
    }
    return render(request, 'tasks/task_form.html', context)


@login_required
def task_edit(request, task_id):
    """Edit an existing task"""
    task = get_object_or_404(Task, id=task_id, owner=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            try:
                updated_task = form.save(commit=False)

                # Handle periodic task details
                if updated_task.is_periodic:
                    # Save periodicity details from form
                    if form.cleaned_data.get('periodicity_detail'):
                        updated_task.periodicity_detail = form.cleaned_data['periodicity_detail']

                updated_task.save()

                # Update existing instances if this is a periodic task
                if updated_task.is_periodic:
                    update_periodic_task_instances(updated_task)
                    # Generate any missing future instances
                    new_instances = generate_periodic_task_instances(
                        updated_task, days_ahead=60)
                    if new_instances:
                        messages.success(
                            request, f'Task "{
                                updated_task.title}" updated successfully! Generated {
                                len(new_instances)} new instances.')
                    else:
                        messages.success(
                            request, f'Task "{
                                updated_task.title}" updated successfully!')
                else:
                    messages.success(
                        request, f'Task "{
                            updated_task.title}" updated successfully!')

                return redirect('task_list')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TaskForm(instance=task)

    context = {
        'form': form,
        'task': task,
        'action': 'Edit'
    }
    return render(request, 'tasks/task_form.html', context)


@login_required
def task_edit_modal(request, task_id):
    """Handle task editing via AJAX modal"""
    task = get_object_or_404(Task, id=task_id, owner=request.user)

    if request.method == 'GET':
        # Return form HTML for modal
        form = TaskForm(instance=task)
        form_html = render_to_string('tasks/task_modal_form.html', {
            'form': form,
            'task': task,
            'action': 'Edit'
        }, request=request)

        return JsonResponse({
            'success': True,
            'form_html': form_html,
            'task_title': task.title
        })

    elif request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            try:
                updated_task = form.save(commit=False)
                updated_task.save()

                # Update existing instances if this is a periodic task
                if updated_task.is_periodic:
                    update_periodic_task_instances(updated_task)
                    # Generate any missing future instances
                    new_instances = generate_periodic_task_instances(
                        updated_task, days_ahead=60)
                    if new_instances:
                        message = f'Task "{
                            updated_task.title}" updated successfully! Generated {
                            len(new_instances)} new instances.'
                    else:
                        message = f'Task "{updated_task.title}" updated successfully!'
                else:
                    message = f'Task "{updated_task.title}" updated successfully!'

                return JsonResponse({
                    'success': True,
                    'message': message
                })
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


@login_required
def task_delete(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id, owner=request.user)

    if request.method == 'POST':
        try:
            task_title = task.title
            task.delete()
            messages.success(request, f'Task "{task_title}" deleted successfully!')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('task_list')

    context = {
        'task': task,
        'incomplete_subtasks': task.has_incomplete_subtasks()
    }
    return render(request, 'tasks/task_confirm_delete.html', context)


@login_required
def task_delete_modal(request, task_id):
    """Handle task deletion via AJAX modal"""
    task = get_object_or_404(Task, id=task_id, owner=request.user)

    if request.method == 'GET':
        # Check if this is part of a periodic task hierarchy
        periodic_info = task.get_periodic_template_info()
        
        # Count how many instances would be affected
        affected_instances = 0
        if periodic_info['is_periodic_instance'] or (periodic_info['template'] and task.parent):
            # This is a subtask in a periodic hierarchy
            template = periodic_info['template']
            if template:
                # Count instances that have this subtask
                instances = Task.objects.filter(periodic_parent=template)
                for instance in instances:
                    # Check if this instance has a matching subtask
                    if _find_matching_subtask_in_instance(task, instance, template):
                        affected_instances += 1
        
        # Return task details for confirmation modal
        return JsonResponse({
            'success': True,
            'task_title': task.title,
            'task_description': task.description or '',
            'incomplete_subtasks': bool(task.has_incomplete_subtasks()),
            'subtask_count': int(task.subtasks.count()),
            'is_periodic_subtask': bool(periodic_info['is_periodic_instance'] or (periodic_info['template'] and task.parent)),
            'template_title': periodic_info['template'].title if periodic_info['template'] else '',
            'affected_instances': int(affected_instances),
        })

    elif request.method == 'DELETE':
        try:
            task_title = task.title
            
            # Check if this is part of a periodic hierarchy
            periodic_info = task.get_periodic_template_info()
            
            if periodic_info['is_periodic_instance'] or (periodic_info['template'] and task.parent):
                # This is a periodic subtask - do comprehensive cleanup
                return _delete_periodic_subtask_completely(task, periodic_info)
            else:
                # Regular task deletion
                task.delete()
                return JsonResponse({
                    'success': True,
                    'message': f'Task "{task_title}" deleted successfully!'
                })
                
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


def _find_matching_subtask_in_instance(target_task, instance, template):
    """Find a matching subtask in an instance based on the target task's hierarchy path"""
    # If target is direct child of template/instance
    if target_task.parent and (target_task.parent == template or target_task.parent.periodic_parent == template):
        return instance.subtasks.filter(title=target_task.title).first()
    
    # If target is nested deeper, trace the path
    path = []
    current = target_task
    while current.parent and current.parent != template and not (hasattr(current.parent, 'periodic_parent') and current.parent.periodic_parent == template):
        path.insert(0, current.title)
        current = current.parent
    
    if current.parent:
        path.insert(0, current.title)
        
        # Follow the path in the instance
        current_instance = instance
        for title in path:
            current_instance = current_instance.subtasks.filter(title=title).first()
            if not current_instance:
                return None
        return current_instance
    
    return None


def _delete_periodic_subtask_completely(task, periodic_info):
    """Delete a subtask from template and all instances"""
    template = periodic_info['template']
    task_title = task.title
    
    # Count what we're going to delete
    deleted_from_template = 0
    deleted_from_instances = 0
    
    try:
        # 1. Find and delete from template if it exists there
        if template and task.parent:
            template_counterpart = periodic_info.get('template_counterpart')
            if template_counterpart:
                template_counterpart.delete()
                deleted_from_template = 1
        
        # 2. Find and delete from all instances
        if template:
            instances = Task.objects.filter(periodic_parent=template)
            for instance in instances:
                matching_subtask = _find_matching_subtask_in_instance(task, instance, template)
                if matching_subtask:
                    matching_subtask.delete()
                    deleted_from_instances += 1
        
        # 3. Delete the original task if it still exists
        if Task.objects.filter(id=task.id).exists():
            task.delete()
        
        # Prepare success message
        if deleted_from_template > 0 and deleted_from_instances > 0:
            message = f'Task "{task_title}" removed completely: deleted from template and {deleted_from_instances} instances.'
        elif deleted_from_instances > 0:
            message = f'Task "{task_title}" removed from {deleted_from_instances} periodic instances.'
        elif deleted_from_template > 0:
            message = f'Task "{task_title}" removed from template and this instance.'
        else:
            message = f'Task "{task_title}" deleted successfully!'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error during periodic cleanup: {str(e)}'
        })


@login_required
@require_POST
def task_toggle_done(request, task_id):
    """Toggle task done status via AJAX"""
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    task.done = not task.done
    task.save()

    # Handle periodic task completion
    if task.done and task.periodic_parent:
        handle_periodic_task_completion(task)

    return JsonResponse({
        'success': True,
        'done': task.done,
        'message': f'Task "{task.title}" marked as {"complete" if task.done else "incomplete"}.'
    })


@login_required
def task_create_modal(request):
    """Create a new task via AJAX modal"""
    parent_id = request.GET.get('parent_id') or request.POST.get('parent_id')
    parent_task = None

    if parent_id:
        try:
            parent_task = get_object_or_404(Task, id=parent_id, owner=request.user)
            if not parent_task.can_add_subtask():
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot add subtasks to this task. Maximum nesting level reached.'
                })
        except (ValueError, Task.DoesNotExist):
            return JsonResponse({
                'success': False,
                'error': 'Invalid parent task.'
            })

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.owner = request.user
            task.parent = parent_task

            # Periodic tasks cannot be subtasks
            if task.is_periodic and parent_task:
                return JsonResponse({
                    'success': False,
                    'error': 'Periodic tasks cannot be subtasks.'
                })

            try:
                task.save()

                # Generate initial instances for periodic tasks
                if task.is_periodic:
                    instances = generate_periodic_task_instances(task, days_ahead=60)
                    message = f'Periodic task "{
                        task.title}" created successfully! Generated {
                        len(instances)} upcoming instances.'
                else:
                    message = f'Task "{task.title}" created successfully!'

                return JsonResponse({
                    'success': True,
                    'message': message,
                    'task_id': task.id,
                    'parent_id': parent_task.id if parent_task else None
                })
            except ValidationError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })

    # GET request - return the form HTML
    form = TaskForm()

    # Prepare hierarchy information if there's a parent task
    hierarchy_path = []
    if parent_task:
        hierarchy_path = parent_task.get_hierarchy_path()

    context = {
        'form': form,
        'parent_task': parent_task,
        'parent_id': parent_id,
        'hierarchy_path': hierarchy_path
    }

    form_html = render_to_string('tasks/task_modal_form.html', context, request=request)
    return JsonResponse({
        'success': True,
        'form_html': form_html
    })


@login_required
@require_POST
def task_print(request, task_id):
    """Print a task and all its child tasks to the configured ESC/P printer"""
    task = get_object_or_404(Task, id=task_id, owner=request.user)

    try:
        # Get user's printing method preference
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            effective_method = user_profile.get_effective_printing_method()
        else:
            effective_method = 'server'  # Default fallback
        
        # Check if user wants local printing but it's not available
        if effective_method == 'local':
            # For now, we'll implement server-side printing
            # Local printing will be implemented in JavaScript/frontend
            return JsonResponse({
                'success': False,
                'message': 'Local printing not yet implemented. Please use server printing method.',
                'print_method': 'local',
                'fallback_to_server': True
            })

        # Use server-side printing (existing implementation)
        use_graphics = getattr(settings, 'PRINTER_USE_GRAPHICS', True)

        # Print the main task first
        success, message = print_task(task, use_graphics=use_graphics)
        if not success:
            return JsonResponse({
                'success': False,
                'message': message,
                'print_method': 'server'
            })

        # Get all child tasks (subtasks at any level)
        child_tasks = task.get_all_subtasks()

        # Print each child task as a separate printout
        printed_count = 1  # Main task already printed
        failed_prints = []

        for child_task in child_tasks:
            child_success, child_message = print_task(
                child_task, use_graphics=use_graphics)
            if child_success:
                printed_count += 1
            else:
                failed_prints.append(f"{child_task.title}: {child_message}")

        # Prepare response message
        if failed_prints:
            failure_details = "; ".join(failed_prints)
            message = f'Printed {printed_count} of {
                len(child_tasks) + 1} task(s). Failed prints: {failure_details}'
            success = printed_count > 0  # Success if at least one task printed
        else:
            if printed_count == 1:
                message = f'Task "{task.title}" printed successfully (no child tasks)'
            else:
                message = f'Task "{
                    task.title}" and {
                    printed_count -
                    1} child task(s) printed successfully ({printed_count} total printouts)'
            success = True

        return JsonResponse({
            'success': success,
            'message': message,
            'print_method': 'server'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Print error: {str(e)}',
            'print_method': 'server'
        })


@login_required
def todays_tasks(request):
    """Display and optionally print today's recurring tasks"""

    # Get today's periodic task instances
    todays_tasks = get_todays_periodic_tasks(request.user)

    # Group tasks by their periodic parent to show hierarchy
    task_groups = {}
    for task in todays_tasks:
        parent = task.periodic_parent
        if parent not in task_groups:
            task_groups[parent] = {
                'parent': parent,
                'instances': [],
                'all_subtasks': []
            }
        task_groups[parent]['instances'].append(task)

        # Get all subtasks of this periodic instance
        subtasks = task.get_all_subtasks()
        task_groups[parent]['all_subtasks'].extend(subtasks)

    # Calculate totals
    total_parent_tasks = len(task_groups)
    total_instances = sum(len(group['instances']) for group in task_groups.values())
    total_subtasks = sum(len(group['all_subtasks']) for group in task_groups.values())

    context = {
        'task_groups': task_groups,
        'total_parent_tasks': total_parent_tasks,
        'total_instances': total_instances,
        'total_subtasks': total_subtasks,
        'total_printouts': total_instances + total_subtasks,
        'today': timezone.now().date()
    }

    return render(request, 'tasks/todays_tasks.html', context)


@login_required
def print_todays_tasks(request):
    """Print only the leaf tasks (final children) of today's recurring tasks.
    Since parent tasks are already shown in the hierarchy path of each task,
    we only need to print the final leaf tasks to avoid duplication."""

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests allowed'
        })

    try:
        # Check user's printing method preference
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            effective_method = user_profile.get_effective_printing_method()
        else:
            effective_method = 'server'  # Default fallback
        
        # Check if user wants local printing but it's not available
        if effective_method == 'local':
            return JsonResponse({
                'success': False,
                'message': 'Local printing not yet implemented. Please use server printing method.',
                'print_method': 'local',
                'fallback_to_server': True
            })

        # Get today's periodic task instances
        todays_tasks = get_todays_periodic_tasks(request.user)

        if not todays_tasks.exists():
            return JsonResponse({
                'success': True,
                'message': 'No recurring tasks due today',
                'print_method': 'server'
            })

        use_graphics = getattr(settings, 'PRINTER_USE_GRAPHICS', True)

        printed_count = 0
        failed_prints = []

        # Collect all leaf tasks (tasks with no children) from today's tasks
        leaf_tasks = []
        processed_ids = set()

        def collect_leaf_tasks(task):
            """Recursively collect tasks that have no children (leaf tasks)"""
            # Avoid processing the same task multiple times
            if task.id in processed_ids:
                return
            processed_ids.add(task.id)

            if not task.subtasks.exists():
                # This task has no children, it's a leaf
                leaf_tasks.append(task)
            else:
                # This task has children, recurse into them
                for subtask in task.subtasks.all():
                    collect_leaf_tasks(subtask)

        # Collect leaf tasks from all today's tasks
        for task in todays_tasks:
            collect_leaf_tasks(task)

        # Print only the leaf tasks
        for leaf_task in leaf_tasks:
            success, message = print_task(leaf_task, use_graphics=use_graphics)
            if success:
                printed_count += 1
            else:
                failed_prints.append(f"{leaf_task.title}: {message}")

        # Prepare response
        if failed_prints:
            failure_details = "; ".join(failed_prints)
            message = f'Printed {printed_count} leaf task(s). Failed prints: {failure_details}'
            success = printed_count > 0
        else:
            message = f"Successfully printed {printed_count} leaf task(s) for today"
            success = True

        return JsonResponse({
            'success': success,
            'message': message,
            'print_method': 'server'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error printing today\'s tasks: {str(e)}',
            'print_method': 'server'
        })
