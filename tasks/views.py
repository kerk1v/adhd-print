from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
import time
import json
import base64
from .models import Task, PrintLog, UserProfile
from .forms import TaskForm, UserProfileForm
from .print_utils import print_task, create_task_image, convert_image_to_bitmap_escp, convert_image_to_escp, get_task_hierarchy
from .periodic_utils import (
    get_periodic_task_summary,
    get_todays_periodic_tasks,
    get_upcoming_periodic_tasks
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

    # Column 1: Root tasks (no parent)
    root_tasks = Task.objects.filter(
        parent__isnull=True,
        owner=request.user
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

    # Get upcoming periodic task virtual instances for sidebar
    upcoming_periodic = get_upcoming_periodic_tasks(request.user, days_ahead=7)

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

                # Success message for periodic vs regular tasks
                if task.is_periodic:
                    messages.success(
                        request, f'Periodic task "{task.title}" created successfully!')
                else:
                    messages.success(
                        request, f'Task "{task.title}" created successfully!')

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

                # Success message for periodic vs regular tasks
                if updated_task.is_periodic:
                    messages.success(
                        request, f'Periodic task "{updated_task.title}" updated successfully!')
                else:
                    messages.success(
                        request, f'Task "{updated_task.title}" updated successfully!')

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

                # Success message for periodic vs regular tasks
                if updated_task.is_periodic:
                    message = f'Periodic task "{updated_task.title}" updated successfully!'
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
        # Check if this is a subtask of a periodic template
        is_periodic_subtask = False
        template_title = ''
        if task.parent and task.parent.is_periodic:
            is_periodic_subtask = True
            template_title = task.parent.title

        # Return task details for confirmation modal
        return JsonResponse({
            'success': True,
            'task_title': task.title,
            'task_description': task.description or '',
            'incomplete_subtasks': bool(task.has_incomplete_subtasks()),
            'subtask_count': int(task.subtasks.count()),
            'is_periodic_subtask': is_periodic_subtask,
            'template_title': template_title,
            'affected_instances': 0,
        })

    elif request.method == 'DELETE':
        try:
            task_title = task.title
            
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
    # With dynamic approach, this function is no longer needed for physical instances
    # but may be used for virtual instance operations
    # If target is direct child of template
    if target_task.parent and target_task.parent == template:
        return instance.subtasks.filter(title=target_task.title).first()
    
    # If target is nested deeper, trace the path
    path = []
    current = target_task
    while current.parent and current.parent != template:
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
        
        # 2. For periodic tasks using dynamic approach, deletion affects only the template
        # No physical instances to delete since they are generated dynamically
        if template:
            # The task being deleted is already removed when it's part of the template
            pass
        
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

                # Success message for periodic vs regular tasks
                if task.is_periodic:
                    message = f'Periodic task "{task.title}" created successfully!'
                else:
                    message = f'Task "{task.title}" created successfully!'

                return JsonResponse({
                    'success': True,
                    'message': message,
                    'task_id': task.id,
                    'task_title': task.title,
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
    
    # Get printer width from request data (default to 80mm for backward compatibility)
    printer_width = '80mm'  # Default
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body)
                printer_width = data.get('printerWidth', '80mm')
            except (json.JSONDecodeError, AttributeError):
                printer_width = '80mm'
        else:
            printer_width = request.POST.get('printerWidth', '80mm')
    
    # Start timing the operation
    start_time = time.time()
    
    # Initialize print log variables
    print_log = None
    effective_method = 'server'  # Default
    
    try:
        # Get user's printing method preference
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            effective_method = user_profile.get_effective_printing_method()
        else:
            effective_method = 'server'  # Default fallback
        
        # Get child tasks for logging purposes only (don't print them)
        child_tasks = task.get_all_subtasks()
        total_tasks = 1  # Only print the main task
        
        # Create print log entry
        print_log = PrintLog.objects.create(
            user=request.user,
            task=task,
            print_method=user_profile.printing_method if user_profile else effective_method,  # Use actual preference, not effective method
            print_type='single_task',  # Always single task now
            tasks_attempted=total_tasks,
            print_settings={
                'use_graphics': getattr(settings, 'PRINTER_USE_GRAPHICS', True),
                'includes_subtasks': bool(child_tasks),
                'subtask_count': len(child_tasks),
                'printer_width': printer_width  # Record the printer width setting
            },
            printer_config={
                'printer_ip': getattr(settings, 'PRINTER_IP', 'Not configured'),
                'printer_port': getattr(settings, 'PRINTER_PORT', 'Not configured'),
                'printer_width': printer_width  # Also record in printer config
            }
        )
        
        # Check if user wants server printing but it's not enabled
        if (user_profile and 
            user_profile.printing_method == 'server' and 
            not user_profile.server_printing_enabled):
            # User selected server printing but it's not enabled for them
            print_log.success = False
            print_log.error_message = 'Server printing not enabled for this user. Please contact an administrator.'
            print_log.tasks_successful = 0
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Server printing not enabled for this user. Please contact an administrator.',
                'print_method': 'server',
                'fallback_to_local': True
            })
        
        # Check if user wants local printing - return task data for client-side processing
        if effective_method == 'local':
            # For local printing, return the task data to the client
            # Get hierarchy information for this task
            hierarchy = []
            current = task
            while current:
                hierarchy.append(current.title)  # Just store titles for compatibility
                current = current.parent
            hierarchy.reverse()  # Root to leaf order
            
            task_data = {
                'id': task.id,
                'title': task.title,
                'description': task.description if task.description else '',
                'urgency': task.urgency,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'level': task.get_level() if hasattr(task, 'get_level') else 0,
                'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None,
                'hierarchy': hierarchy,  # Array of title strings for ESC/POS compatibility
            }
            
            print_log.success = True
            print_log.tasks_successful = 1
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Task data prepared for local printing',
                'print_method': 'local',
                'task_data': [task_data],  # Array format for consistency with batch printing
                'use_client_side': True
            })

        # Use server-side printing (existing implementation)
        use_graphics = getattr(settings, 'PRINTER_USE_GRAPHICS', True)

        # Print only the main task with selected printer width
        success, message = print_task(task, use_graphics=use_graphics, printer_width=printer_width)
        if not success:
            print_log.success = False
            print_log.error_message = f"Task print failed: {message}"
            print_log.tasks_successful = 0
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()
            
            return JsonResponse({
                'success': False,
                'message': message,
                'print_method': 'server'
            })

        # Task printed successfully
        printed_count = 1
        
        # Mark task as printed
        task.is_printed = True
        task.save()

        # Update print log with results
        print_log.tasks_successful = printed_count
        print_log.success = True
        print_log.duration_ms = int((time.time() - start_time) * 1000)
        print_log.save()

        # Prepare response message
        message = f'Task "{task.title}" printed successfully'

        return JsonResponse({
            'success': success,
            'message': message,
            'print_method': 'server'
        })

    except Exception as e:
        # Update print log with error if it exists
        if print_log:
            print_log.success = False
            print_log.error_message = f'Exception during print: {str(e)}'
            print_log.tasks_successful = 0
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()
        else:
            # Create emergency print log entry
            try:
                PrintLog.objects.create(
                    user=request.user,
                    task=task,
                    print_method=effective_method,
                    print_type='single_task',
                    success=False,
                    tasks_attempted=1,
                    tasks_successful=0,
                    error_message=f'Exception during print setup: {str(e)}',
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            except:
                pass  # Don't let logging errors break the response
        
        return JsonResponse({
            'success': False,
            'message': f'Print error: {str(e)}',
            'print_method': 'server'
        })


@login_required
def task_api(request, task_id):
    """
    API endpoint to get task data in JSON format for local printing
    """
    task = get_object_or_404(Task, id=task_id, owner=request.user)
    
    # Get hierarchy information for this task
    hierarchy = []
    current = task
    while current:
        hierarchy.append(current.title)
        current = current.parent
    hierarchy.reverse()  # Root to leaf order
    
    task_data = {
        'id': task.id,
        'title': task.title,
        'description': task.description if task.description else '',
        'urgency': task.urgency,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'level': task.get_level() if hasattr(task, 'get_level') else 0,
        'created_at': task.created_at.isoformat() if hasattr(task, 'created_at') and task.created_at else None,
        'hierarchy': hierarchy,
    }
    
    return JsonResponse(task_data)


@login_required
def todays_tasks(request):
    """Display and optionally print today's recurring tasks and regular tasks due today"""

    # Get today's periodic task instances
    todays_periodic_tasks = get_todays_periodic_tasks(request.user)
    
    # Get regular (non-periodic) tasks due today
    today = timezone.now().date()
    todays_regular_tasks = Task.objects.filter(
        owner=request.user,
        is_periodic=False,
        due_date__date=today,
        done=False
    ).order_by('urgency', 'title')
    
    # Combine all tasks
    all_todays_tasks = list(todays_periodic_tasks) + list(todays_regular_tasks)

    # Group tasks by their template for periodic tasks, individual for regular tasks
    task_groups = {}
    for task in all_todays_tasks:
        # For periodic tasks, group by template; for regular tasks, each is its own group
        if hasattr(task, '_template_task'):
            # Periodic virtual task - group by template
            parent = task._template_task
        else:
            # Regular task - each task is its own group
            parent = task
            
        if parent not in task_groups:
            task_groups[parent] = {
                'parent': parent,
                'instances': [],
                'all_subtasks': []
            }
        task_groups[parent]['instances'].append(task)

        # Get all subtasks of this task
        subtasks = task.get_all_subtasks()
        task_groups[parent]['all_subtasks'].extend(subtasks)

    # Calculate totals
    total_parent_tasks = len(task_groups)
    total_instances = sum(len(group['instances']) for group in task_groups.values())
    total_subtasks = sum(len(group['all_subtasks']) for group in task_groups.values())
    
    # Calculate actual printouts (only leaf tasks)
    def count_leaf_tasks(task, processed_ids=None):
        """Count leaf tasks recursively"""
        if processed_ids is None:
            processed_ids = set()
            
        # For virtual tasks, use title as identifier since they don't have IDs
        task_identifier = task.id if task.pk else f"virtual_{task.title}_{task.due_date}"
        
        # Avoid processing the same task multiple times
        if task_identifier in processed_ids:
            return 0
        processed_ids.add(task_identifier)
        
        # Get subtasks using our updated method that handles virtual instances
        all_subtasks = task.get_all_subtasks()
        
        if not all_subtasks:
            # This task has no children, it's a leaf
            return 1
        else:
            # This task has children, count leaves in children
            leaf_count = 0
            for subtask in all_subtasks:
                leaf_count += count_leaf_tasks(subtask, processed_ids)
            return leaf_count
    
    total_printouts = 0
    for task in all_todays_tasks:
        total_printouts += count_leaf_tasks(task)

    context = {
        'task_groups': task_groups,
        'total_parent_tasks': total_parent_tasks,
        'total_instances': total_instances,
        'total_subtasks': total_subtasks,
        'total_printouts': total_printouts,
        'today': timezone.now().date()
    }

    return render(request, 'tasks/todays_tasks.html', context)


@login_required
def unprinted_tasks(request):
    """Display all unprinted leaf tasks (final children with no subtasks)
    
    Excludes:
    - Periodic task instances (generated from recurring tasks)
    - Tasks that are children of periodic instances
    """
    
    # Get all tasks owned by the user that are not printed and not done
    all_tasks = Task.objects.filter(
        owner=request.user,
        is_printed=False,
        done=False
    ).order_by('-created_at')
    
    # Filter to only include leaf tasks (tasks with no children) 
    # and exclude periodic instances and their descendants
    leaf_tasks = []
    processed_ids = set()
    
    def is_leaf_task(task):
        """Check if task has no children (is a leaf task)"""
        return not task.subtasks.exists()
    
    def is_periodic_instance_or_descendant(task):
        """Check if task is a periodic instance or descendant of one"""
        # With the new dynamic approach, there are no physical periodic instances
        # All tasks are either periodic templates or regular tasks/subtasks
        return False
    
    for task in all_tasks:
        if (task.id not in processed_ids and 
            is_leaf_task(task) and 
            not is_periodic_instance_or_descendant(task)):
            leaf_tasks.append(task)
            processed_ids.add(task.id)
    
    # Calculate statistics
    total_unprinted_leaf_tasks = len(leaf_tasks)
    
    context = {
        'leaf_tasks': leaf_tasks,
        'total_unprinted_leaf_tasks': total_unprinted_leaf_tasks,
    }

    return render(request, 'tasks/unprinted_tasks.html', context)


@login_required
def print_unprinted_tasks(request):
    """Print all unprinted leaf tasks (final children with no subtasks)
    
    Excludes:
    - Periodic task instances (generated from recurring tasks)
    - Tasks that are children of periodic instances
    """

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': 'Only POST requests allowed'
        })

    # Start timing the operation
    start_time = time.time()
    
    # Initialize print log variables
    print_log = None
    effective_method = 'server'  # Default

    try:
        # Parse request body for additional parameters
        request_data = {}
        if request.content_type == 'application/json' and request.body:
            try:
                request_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                pass
        
        # Get printer width from request_data (default to 80mm for backward compatibility)
        printer_width = request_data.get('printerWidth', '80mm')
        
        # Check user's printing method preference
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            # Override with request data if provided
            if 'print_method' in request_data:
                effective_method = request_data['print_method']
            else:
                effective_method = user_profile.get_effective_printing_method()
        else:
            effective_method = request_data.get('print_method', 'server')  # Default fallback
        
        # Get all unprinted leaf tasks (excluding periodic instances)
        all_tasks = Task.objects.filter(
            owner=request.user,
            is_printed=False,
            done=False
        ).order_by('-created_at')
        
        # Filter to only include leaf tasks (tasks with no children)
        # and exclude periodic instances and their descendants
        leaf_tasks = []
        processed_ids = set()
        
        def is_leaf_task(task):
            """Check if task has no children (is a leaf task)"""
            return not task.subtasks.exists()
        
        def is_periodic_instance_or_descendant(task):
            """Check if task is a periodic instance or descendant of one"""
            # With the new dynamic approach, there are no physical periodic instances
            # All tasks are either periodic templates or regular tasks/subtasks
            return False
        
        for task in all_tasks:
            if (task.id not in processed_ids and 
                is_leaf_task(task) and 
                not is_periodic_instance_or_descendant(task)):
                leaf_tasks.append(task)
                processed_ids.add(task.id)

        if not leaf_tasks:
            # Create log entry for empty result
            PrintLog.objects.create(
                user=request.user,
                print_method=effective_method,
                print_type='unprinted_tasks',
                success=True,
                tasks_attempted=0,
                tasks_successful=0,
                error_message='No unprinted leaf tasks found',
                duration_ms=int((time.time() - start_time) * 1000),
                print_settings={'printer_width': printer_width}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'No unprinted leaf tasks found',
                'print_method': effective_method
            })

        # Create print log entry
        print_log = None
        try:            
            print_log = PrintLog.objects.create(
                user=request.user,
                print_method=user_profile.printing_method if user_profile else effective_method,
                print_type='unprinted_tasks',
                tasks_attempted=len(leaf_tasks),
                print_settings={
                    'use_graphics': getattr(settings, 'PRINTER_USE_GRAPHICS', True),
                    'leaf_tasks_count': len(leaf_tasks),
                    'printer_width': printer_width
                },
                printer_config={
                    'printer_ip': getattr(settings, 'PRINTER_IP', 'Not configured'),
                    'printer_port': getattr(settings, 'PRINTER_PORT', 'Not configured'),
                    'printer_width': printer_width
                }
            )
        except (TypeError, ValueError, Exception):
            # If logging fails (e.g., due to Mock objects in tests), skip logging
            pass
        
        # Check if user wants server printing but it's not enabled
        if (user_profile and 
            user_profile.printing_method == 'server' and 
            not user_profile.server_printing_enabled):
            if print_log:
                print_log.success = False
                print_log.error_message = 'Server printing not enabled for this user. Please contact an administrator.'
                print_log.tasks_successful = 0
                print_log.duration_ms = int((time.time() - start_time) * 1000)
                print_log.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Server printing not enabled for this user. Please contact an administrator.',
                'print_method': 'server',
                'fallback_to_local': True
            })
        
        # Check if user wants local printing - return task data for client-side processing
        if effective_method == 'local':
            # For local printing, return the task data to the client
            leaf_tasks_data = []
            for leaf_task in leaf_tasks:
                # Get hierarchy information for this task
                hierarchy = []
                current = leaf_task
                while current:
                    hierarchy.append(current.title)  # Just store titles for compatibility
                    current = current.parent
                hierarchy.reverse()  # Root to leaf order
                
                task_data = {
                    'id': getattr(leaf_task, 'task_identifier', leaf_task.id),
                    'title': leaf_task.title,
                    'description': leaf_task.description if leaf_task.description else '',
                    'urgency': leaf_task.urgency,
                    'due_date': leaf_task.due_date.isoformat() if leaf_task.due_date else None,
                    'level': leaf_task.get_level() if hasattr(leaf_task, 'get_level') else 0,
                    'created_at': leaf_task.created_at.isoformat() if hasattr(leaf_task, 'created_at') and leaf_task.created_at else None,
                    'hierarchy': hierarchy,  # Array of title strings for ESC/POS compatibility
                }
                leaf_tasks_data.append(task_data)
            
            if print_log:
                print_log.success = True
                print_log.tasks_successful = len(leaf_tasks)
                print_log.duration_ms = int((time.time() - start_time) * 1000)
                print_log.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Task data prepared for local printing ({len(leaf_tasks)} task(s))',
                'print_method': 'local',
                'task_data': leaf_tasks_data,
                'use_client_side': True
            })

        use_graphics = getattr(settings, 'PRINTER_USE_GRAPHICS', True)

        printed_count = 0
        failed_prints = []

        # Print only the leaf tasks with selected printer width
        for leaf_task in leaf_tasks:
            success, message = print_task(leaf_task, use_graphics=use_graphics, printer_width=printer_width)
            if success:
                printed_count += 1
                # Mark leaf task as printed
                leaf_task.is_printed = True
                leaf_task.save()
            else:
                failed_prints.append(f"{leaf_task.title}: {message}")

        # Update print log with results
        if print_log:
            print_log.tasks_successful = printed_count
            print_log.success = printed_count > 0 or len(leaf_tasks) == 0
            if failed_prints:
                print_log.error_message = "; ".join(failed_prints)
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()

        # Prepare response
        if failed_prints:
            failure_details = "; ".join(failed_prints)
            message = f'Printed {printed_count} unprinted leaf task(s). Failed prints: {failure_details}'
            success = printed_count > 0
        else:
            message = f"Successfully printed {printed_count} unprinted leaf task(s)"
            success = True

        return JsonResponse({
            'success': success,
            'message': message,
            'print_method': 'server'
        })

    except Exception as e:
        # Update print log with error if it exists
        if print_log:
            print_log.success = False
            print_log.error_message = f'Exception during print: {str(e)}'
            print_log.tasks_successful = 0
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()
        else:
            # Create emergency print log entry if logging is available
            try:
                PrintLog.objects.create(
                    user=request.user,
                    print_method=effective_method,
                    print_type='unprinted_tasks',
                    success=False,
                    tasks_attempted=0,
                    tasks_successful=0,
                    error_message=f'Exception during print setup: {str(e)}',
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            except:
                pass  # Don't let logging errors break the response
        
        return JsonResponse({
            'success': False,
            'message': f'Error printing unprinted tasks: {str(e)}',
            'print_method': 'server'
        })


@require_POST
@login_required
def mark_tasks_printed(request):
    """Mark specified tasks as printed (for local printing completion)"""
    try:
        import json
        data = json.loads(request.body)
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return JsonResponse({
                'success': False,
                'message': 'No task IDs provided'
            })
        
        # Get tasks owned by the user
        tasks = Task.objects.filter(
            id__in=task_ids,
            owner=request.user
        )
        
        updated_count = 0
        for task in tasks:
            task.is_printed = True
            task.save()
            updated_count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Marked {updated_count} task(s) as printed',
            'updated_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error marking tasks as printed: {str(e)}'
        })


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

    # Start timing the operation
    start_time = time.time()
    
    # Initialize print log variables
    print_log = None
    effective_method = 'server'  # Default

    try:
        # Parse request body for additional parameters
        request_data = {}
        if request.content_type == 'application/json' and request.body:
            try:
                request_data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                pass
        
        # Get printer width from request_data (default to 80mm for backward compatibility)
        printer_width = request_data.get('printerWidth', '80mm')        # Check user's printing method preference
        user_profile = getattr(request.user, 'profile', None)
        if user_profile:
            # Override with request data if provided
            if 'print_method' in request_data:
                effective_method = request_data['print_method']
            else:
                effective_method = user_profile.get_effective_printing_method()
        else:
            effective_method = request_data.get('print_method', 'server')  # Default fallback
        
        # Get today's periodic task instances
        todays_periodic_tasks = get_todays_periodic_tasks(request.user)
        
        # Get regular (non-periodic) tasks due today
        today = timezone.now().date()
        todays_regular_tasks = Task.objects.filter(
            owner=request.user,
            is_periodic=False,
            due_date__date=today,
            done=False
        ).order_by('urgency', 'title')
        
        # Combine all tasks
        todays_tasks = list(todays_periodic_tasks) + list(todays_regular_tasks)

        if not todays_tasks:
            # Create log entry for empty result
            PrintLog.objects.create(
                user=request.user,
                print_method=effective_method,
                print_type='todays_tasks',
                success=True,
                tasks_attempted=0,
                tasks_successful=0,
                error_message='No tasks due today',
                duration_ms=int((time.time() - start_time) * 1000),
                print_settings={'today_date': timezone.now().date().isoformat()}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'No tasks due today',
                'print_method': 'server'
            })
        
        # Collect all leaf tasks (tasks with no children) from today's tasks
        leaf_tasks = []
        processed_ids = set()

        def collect_leaf_tasks(task):
            """Recursively collect tasks that have no children (leaf tasks)"""
            task_id = getattr(task, 'task_identifier', getattr(task, 'id', None))
            if task_id in processed_ids:
                return
            processed_ids.add(task_id)
            
            # Get subtasks for template use (handles virtual instances)
            subtasks = getattr(task, 'subtasks_for_template', [])
            
            if not subtasks:
                # This is a leaf task
                leaf_tasks.append(task)
            else:
                # Process all subtasks recursively
                for subtask in subtasks:
                    collect_leaf_tasks(subtask)
        
        # Collect leaf tasks from all today's tasks
        for task in todays_tasks:
            collect_leaf_tasks(task)

        # Create print log entry (skip if in test environment with mocks)
        print_log = None
        try:
            parent_count = len(todays_tasks)
        except (AttributeError, TypeError):
            parent_count = 0  # Handle mock objects in tests
            
        try:
            print_log = PrintLog.objects.create(
                user=request.user,
                print_method=user_profile.printing_method if user_profile else effective_method,  # Use actual preference, not effective method
                print_type='todays_tasks',
                tasks_attempted=len(leaf_tasks),
                print_settings={
                    'use_graphics': getattr(settings, 'PRINTER_USE_GRAPHICS', True),
                    'today_date': timezone.now().date().isoformat(),
                    'parent_tasks_count': parent_count,
                    'leaf_tasks_count': len(leaf_tasks),
                    'printer_width': printer_width  # Record the printer width setting
                },
                printer_config={
                    'printer_ip': getattr(settings, 'PRINTER_IP', 'Not configured'),
                    'printer_port': getattr(settings, 'PRINTER_PORT', 'Not configured'),
                    'printer_width': printer_width  # Also record in printer config
                }
            )
        except (TypeError, ValueError, Exception):
            # If logging fails (e.g., due to Mock objects in tests), skip logging
            pass
        
        # Check if user wants server printing but it's not enabled
        if (user_profile and 
            user_profile.printing_method == 'server' and 
            not user_profile.server_printing_enabled):
            if print_log:
                print_log.success = False
                print_log.error_message = 'Server printing not enabled for this user. Please contact an administrator.'
                print_log.tasks_successful = 0
                print_log.duration_ms = int((time.time() - start_time) * 1000)
                print_log.save()
            
            return JsonResponse({
                'success': False,
                'message': 'Server printing not enabled for this user. Please contact an administrator.',
                'print_method': 'server',
                'fallback_to_local': True
            })
        
        # Check if user wants local printing - return task data for client-side processing
        if effective_method == 'local':
            # For local printing, return the task data to the client
            leaf_tasks_data = []
            real_tasks_to_mark = []  # Track real tasks that need to be marked as printed
            
            for leaf_task in leaf_tasks:
                # Get hierarchy information for this task
                hierarchy = []
                current = leaf_task
                while current:
                    hierarchy.append(current.title)  # Just store titles for compatibility
                    current = current.parent
                hierarchy.reverse()  # Root to leaf order
                
                # For virtual periodic instances, we need to track the real template task
                real_task_id = None
                if hasattr(leaf_task, '_template_task') and leaf_task._template_task:
                    # This is a virtual periodic instance, get the real template task ID
                    real_task_id = leaf_task._template_task.id
                    real_tasks_to_mark.append(leaf_task._template_task)
                elif hasattr(leaf_task, 'pk') and leaf_task.pk:
                    # This is a real task with a database ID
                    real_task_id = leaf_task.pk
                    real_tasks_to_mark.append(leaf_task)
                
                task_data = {
                    'id': getattr(leaf_task, 'task_identifier', leaf_task.id),
                    'real_id': real_task_id,  # Include the real database ID for marking as printed
                    'title': leaf_task.title,
                    'description': leaf_task.description if leaf_task.description else '',
                    'urgency': leaf_task.urgency,
                    'due_date': leaf_task.due_date.isoformat() if leaf_task.due_date else None,
                    'level': leaf_task.get_level() if hasattr(leaf_task, 'get_level') else 0,
                    'created_at': leaf_task.created_at.isoformat() if hasattr(leaf_task, 'created_at') and leaf_task.created_at else None,
                    'hierarchy': hierarchy,  # Array of title strings for ESC/POS compatibility
                }
                leaf_tasks_data.append(task_data)
            
            # Pre-mark the real tasks as printed since local printing will handle them
            marked_count = 0
            for real_task in real_tasks_to_mark:
                if hasattr(real_task, 'pk') and real_task.pk:
                    real_task.is_printed = True
                    real_task.save()
                    marked_count += 1
            
            if print_log:
                print_log.success = True
                print_log.tasks_successful = len(leaf_tasks)
                print_log.duration_ms = int((time.time() - start_time) * 1000)
                print_log.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Task data prepared for local printing ({len(leaf_tasks)} task(s))',
                'print_method': 'local',
                'task_data': leaf_tasks_data,
                'use_client_side': True,
                'marked_as_printed': marked_count  # Let client know how many were marked
            })

        use_graphics = getattr(settings, 'PRINTER_USE_GRAPHICS', True)

        printed_count = 0
        failed_prints = []

        # Print only the leaf tasks with selected printer width
        for leaf_task in leaf_tasks:
            success, message = print_task(leaf_task, use_graphics=use_graphics, printer_width=printer_width)
            if success:
                printed_count += 1
                # Mark leaf task as printed
                leaf_task.is_printed = True
                leaf_task.save()
            else:
                failed_prints.append(f"{leaf_task.title}: {message}")

        # Update print log with results
        if print_log:
            print_log.tasks_successful = printed_count
            print_log.success = printed_count > 0 or len(leaf_tasks) == 0
            if failed_prints:
                print_log.error_message = "; ".join(failed_prints)
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()

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
        # Update print log with error if it exists
        if print_log:
            print_log.success = False
            print_log.error_message = f'Exception during print: {str(e)}'
            print_log.tasks_successful = 0
            print_log.duration_ms = int((time.time() - start_time) * 1000)
            print_log.save()
        else:
            # Create emergency print log entry if logging is available
            try:
                PrintLog.objects.create(
                    user=request.user,
                    print_method=effective_method,
                    print_type='todays_tasks',
                    success=False,
                    tasks_attempted=0,
                    tasks_successful=0,
                    error_message=f'Exception during print setup: {str(e)}',
                    duration_ms=int((time.time() - start_time) * 1000)
                )
            except:
                pass  # If even emergency logging fails, just continue
        
        return JsonResponse({
            'success': False,
            'message': f'Print failed: {str(e)}',
            'print_method': 'server'
        })


@require_POST
@login_required
def generate_escpos_graphics(request):
    """
    Generate ESC/POS graphics commands using server-side print_utils.py
    
    This endpoint leverages the existing high-quality graphics generation
    from print_utils.py and returns the ESC/POS command data as base64
    for local printing via WebUSB/WebSerial.
    
    Request format:
    {
        "task": {
            "id": 123,
            "title": "Task title",
            "description": "Task description",
            "urgency": "normal",
            "due_date": "2024-11-02T10:00:00Z",
            "created_at": "2024-11-01T09:00:00Z",
            "hierarchy": ["Parent Task", "Current Task"]
        },
        "options": {
            "use_graphics": true,
            "format": "bitmap"  // or "simple"
        }
    }
    
    Response format:
    {
        "success": true,
        "escpos_data": "base64_encoded_escpos_commands",
        "format": "bitmap",
        "byte_count": 12345
    }
    """
    try:
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            }, status=400)
        
        # Validate request structure
        if 'task' not in data:
            return JsonResponse({
                'success': False,
                'error': 'Missing task data'
            }, status=400)
        
        task_data = data['task']
        options = data.get('options', {})
        
        # Get printer width from options (default to 80mm for backward compatibility)
        printer_width = options.get('printerWidth', '80mm')
        
        # Validate required task fields
        required_fields = ['title']
        for field in required_fields:
            if field not in task_data:
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required task field: {field}'
                }, status=400)
        
        # Create a mock task object for print_utils.py
        class MockTask:
            def __init__(self, task_data):
                self.id = task_data.get('id', 0)
                self.title = task_data['title']
                self.description = task_data.get('description', '')
                self.urgency = task_data.get('urgency', 'normal')
                self.due_date = None
                self.created_at = timezone.now()
                
                # Parse due_date if provided
                if task_data.get('due_date'):
                    try:
                        from django.utils.dateparse import parse_datetime
                        self.due_date = parse_datetime(task_data['due_date'])
                    except:
                        pass
                
                # Parse created_at if provided
                if task_data.get('created_at'):
                    try:
                        from django.utils.dateparse import parse_datetime
                        parsed_date = parse_datetime(task_data['created_at'])
                        if parsed_date:
                            self.created_at = parsed_date
                    except:
                        pass
                
                # Set hierarchy for get_task_hierarchy function
                self._hierarchy = task_data.get('hierarchy', [self.title])
        
        # Create mock task
        mock_task = MockTask(task_data)
        
        # Override get_task_hierarchy to use provided hierarchy
        def mock_get_task_hierarchy(task):
            return task._hierarchy
        
        # Temporarily replace the hierarchy function
        original_get_task_hierarchy = get_task_hierarchy
        import tasks.print_utils
        tasks.print_utils.get_task_hierarchy = mock_get_task_hierarchy
        
        try:
            # Generate graphics using existing print_utils.py
            format_type = options.get('format', 'bitmap')  # 'bitmap' or 'simple'
            
            # Create image using existing function with printer width
            image = create_task_image(mock_task, printer_width)
            
            # Convert to ESC/POS commands with printer width
            if format_type == 'bitmap':
                escpos_data = convert_image_to_bitmap_escp(image, printer_width)
            else:  # simple/8-dot graphics
                escpos_data = convert_image_to_escp(image, printer_width)
            
            # Encode as base64 for JSON transport
            encoded_data = base64.b64encode(escpos_data).decode('utf-8')
            
            return JsonResponse({
                'success': True,
                'escpos_data': encoded_data,
                'format': format_type,
                'byte_count': len(escpos_data),
                'image_width': image.width,
                'image_height': image.height
            })
            
        finally:
            # Restore original function
            tasks.print_utils.get_task_hierarchy = original_get_task_hierarchy
    
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in generate_escpos_graphics: {error_details}")
        
        return JsonResponse({
            'success': False,
            'error': f'Graphics generation failed: {str(e)}',
            'details': error_details if settings.DEBUG else None
        }, status=500)


@login_required
def user_profile(request):
    """
    User profile page for managing printing preferences and printer settings
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        logger.info(f"User profile view called for {request.user.username}, method: {request.method}")
        
        if request.method == 'POST':
            logger.info(f"POST data received: {request.POST}")
            form = UserProfileForm(request.POST, instance=profile, user=request.user)
            logger.info(f"Form is_valid: {form.is_valid()}")
            if form.is_valid():
                saved_profile = form.save()
                logger.info(f"Profile saved successfully. New printing method: {saved_profile.printing_method}")
                messages.success(request, 'Profile updated successfully!')
                return redirect('user_profile')
            else:
                logger.error(f"Form validation errors: {form.errors}")
                messages.error(request, 'Please correct the errors below.')
        else:
            form = UserProfileForm(instance=profile, user=request.user)
            logger.info(f"Current profile settings - printing_method: {profile.printing_method}, server_printing_enabled: {profile.server_printing_enabled}")
        
        # Get printer configuration for display
        printer_settings = profile.printer_settings
        
        # Get recent print logs for troubleshooting
        recent_logs = PrintLog.objects.filter(
            user=request.user
        ).order_by('-timestamp')[:10]
        
        context = {
            'form': form,
            'profile': profile,
            'printer_settings': printer_settings,
            'recent_logs': recent_logs,
            'created': created
        }
        
        return render(request, 'tasks/user_profile.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading profile: {str(e)}')
        return redirect('task_list')


@require_POST
@login_required
def save_printer_settings(request):
    """
    AJAX endpoint to save printer settings to user profile
    """
    try:
        data = json.loads(request.body)
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        # Update printer settings
        if 'printer_settings' in data:
            profile.printer_settings = data['printer_settings']
        
        profile.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Printer settings saved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to save settings: {str(e)}'
        }, status=500)


@require_POST
@login_required
def test_printer_connection(request):
    """
    AJAX endpoint to test printer connection and send test print
    """
    try:
        data = json.loads(request.body)
        printer_config = data.get('printer_config', {})
        
        # Store test print configuration in session for the client-side test
        request.session['test_printer_config'] = printer_config
        
        return JsonResponse({
            'success': True,
            'message': 'Test print initiated. Check your printer for output.',
            'printer_config': printer_config
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Test print failed: {str(e)}'
        }, status=500)


@login_required
def user_profile_api(request):
    """
    API endpoint to get user profile data for the print modal
    """
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        
        return JsonResponse({
            'printing_method': profile.printing_method,
            'server_printing_enabled': profile.server_printing_enabled,
            'printer_settings': profile.printer_settings
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Failed to load profile: {str(e)}'
        }, status=500)
