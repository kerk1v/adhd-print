from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import Task, MaintenanceLog, UserProfile, PrintLog
from .forms import TaskAdminForm


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm  # Use our custom form
    
    list_display = [
        'hierarchical_title',
        'task_type',
        'urgency',
        'owner',
        'due_date',
        'done',
        'periodic_status',
        'created_at'
    ]
    list_filter = [
        'urgency',
        'done',
        'is_periodic',
        'periodicity_type',
        'created_at',
        'owner',
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
    ordering = ['parent__id', '-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'owner')
        }),
        ('Task Details', {
            'fields': ('urgency', 'due_date', 'done')
        }),
        ('Hierarchy', {
            'fields': ('parent',),
            'description': (
                'Set the parent task to create a subtask hierarchy (max 3 levels)'
            )
        }),
        ('Periodic Task Settings', {
            'fields': (
                'is_periodic',
                'start_date',
                'periodicity_type',
                ('interval_days', 'interval_weeks', 'interval_months'),
                'weekdays',
                'end_date'
            ),
            'classes': ('collapse',),
            'description': (
                'Configure recurring task behavior. For interval-based periodicities, '
                'fill in the appropriate interval field based on your selected type. '
                'With dynamic approach, periodic tasks generate virtual instances when needed.'
            )
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def hierarchical_title(self, obj):
        """Display task title with indentation based on level"""
        level_indicator = "│  " * obj.get_level()
        if obj.get_level() > 0:
            level_indicator += "└─ "

        # Add visual indicators for periodic tasks
        if obj.is_periodic:
            icon = "🔄"  # Recurring periodic task
        else:
            icon = "📋"  # Regular task

        return f"{icon} {level_indicator}{obj.title}"
    hierarchical_title.short_description = 'Title'
    hierarchical_title.admin_order_field = 'title'

    def task_type(self, obj):
        """Show what type of task this is"""
        if obj.is_periodic:
            return format_html(
                '<span style="color: blue; font-weight: bold;">Periodic</span>')
        else:
            return format_html('<span style="color: gray;">Regular</span>')
    task_type.short_description = 'Type'

    def periodic_status(self, obj):
        """Show periodic task status and details"""
        if obj.is_periodic:
            if obj.periodicity_type:
                status = f"{obj.periodicity_type.replace('_', ' ').title()}"
                
                if obj.periodicity_detail:
                    if obj.periodicity_type == 'weekly' and 'weekdays' in obj.periodicity_detail:
                        weekdays = obj.periodicity_detail['weekdays']
                        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        selected_days = [days[i] for i in weekdays]
                        status += f" ({', '.join(selected_days)})"
                    elif obj.periodicity_type in ['every_x_days', 'every_x_weeks', 'every_x_months'] and 'interval' in obj.periodicity_detail:
                        interval = obj.periodicity_detail['interval']
                        if obj.periodicity_type == 'every_x_days':
                            status = f"Every {interval} day{'s' if interval > 1 else ''}"
                        elif obj.periodicity_type == 'every_x_weeks':
                            status = f"Every {interval} week{'s' if interval > 1 else ''}"
                        elif obj.periodicity_type == 'every_x_months':
                            status = f"Every {interval} month{'s' if interval > 1 else ''}"
                
                return format_html('<span style="color: blue;">{}</span>', status)
            return format_html(
                '<span style="color: orange;">Periodic (incomplete)</span>')
        return '-'
    periodic_status.short_description = 'Periodic Status'

    def get_queryset(self, request):
        """Order tasks to show hierarchy clearly and optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('parent', 'owner')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "parent":
            # Only show tasks that can have subtasks (level < 2) and are not periodic instances
            kwargs["queryset"] = Task.objects.filter(
                models.Q(
                    parent__isnull=True) | models.Q(
                    parent__parent__isnull=True))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Customize form behavior"""
        form = super().get_form(request, obj, **kwargs)
        return form

    def delete_model(self, request, obj):
        """Override delete to handle validation and provide feedback"""
        try:
            obj.delete()
            messages.success(
                request,
                f'Task "{obj.title}" was deleted successfully.'
            )
        except Exception as e:
            messages.error(request, f'Error deleting task: {str(e)}')
            raise

    def _count_subtasks_recursive(self, task):
        """Count all subtasks recursively"""
        count = 0
        for subtask in task.subtasks.all():
            count += 1
            count += self._count_subtasks_recursive(subtask)
        return count

    def delete_queryset(self, request, queryset):
        """Override bulk delete to handle validation and provide feedback"""
        deleted_count = 0
        errors = []

        for obj in queryset:
            try:
                obj.delete()
                deleted_count += 1
            except Exception as e:
                errors.append(f'"{obj.title}": {str(e)}')

        if deleted_count > 0:
            success_msg = f'{deleted_count} task(s) deleted successfully.'
            messages.success(request, success_msg)

        if errors:
            for error in errors:
                messages.error(request, error)

    def save_model(self, request, obj, form, change):
        """Override save to handle validation"""
        try:
            if not change:  # If creating new task
                if not obj.owner:
                    obj.owner = request.user
            obj.save()

            if change:
                messages.success(
                    request, f'Task "{
                        obj.title}" was updated successfully.')
            else:
                messages.success(
                    request, f'Task "{
                        obj.title}" was created successfully.')
        except ValidationError as e:
            messages.error(request, str(e))
            raise

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on context"""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing existing task
            readonly_fields.append('owner')
        return readonly_fields

    actions = ['mark_as_done', 'mark_as_not_done', 'generate_periodic_instances']

    def mark_as_done(self, request, queryset):
        """Mark selected tasks as done"""
        updated = queryset.update(done=True)
        messages.success(request, f'{updated} task(s) marked as done.')
    mark_as_done.short_description = "Mark selected tasks as done"

    def mark_as_not_done(self, request, queryset):
        """Mark selected tasks as not done"""
        updated = queryset.update(done=False)
        messages.success(request, f'{updated} task(s) marked as not done.')
    mark_as_not_done.short_description = "Mark selected tasks as not done"

    def generate_periodic_instances(self, request, queryset):
        """Generate instances for selected periodic tasks"""
        periodic_tasks = queryset.filter(is_periodic=True)
        total_instances = 0

        for task in periodic_tasks:
            from django.utils import timezone
            from datetime import timedelta
            
            instances_created = 0
            end_date = timezone.now().date() + timedelta(days=365)  # Generate for next year
            
            # Using the dynamic generation logic for actual instance creation
            start_date = task.created_at.date() if task.created_at else timezone.now().date()
            current_date = start_date
            
            # Create instances up to end_date if they don't exist
            while current_date <= end_date:
                if task._should_occur_on_date(current_date):
                    # Check if we already have a task for this date
                    existing = Task.objects.filter(
                        title=task.title,
                        due_date__date=current_date,
                        parent=None,
                        is_periodic=False
                    ).first()
                    
                    if not existing:
                        # Create the instance
                        Task.objects.create(
                            title=task.title,
                            description=task.description,
                            due_date=timezone.datetime.combine(current_date, task.due_date.time()) if task.due_date else None,
                            priority=task.priority,
                            owner=task.owner,
                            parent=None,
                            is_periodic=False,
                            category=task.category,
                            estimated_duration=task.estimated_duration,
                            energy_level_required=task.energy_level_required,
                            context=task.context
                        )
                        instances_created += 1
                
                # Advance to next potential date
                if task.periodicity == 'D':
                    current_date += timedelta(days=1)
                elif task.periodicity == 'W':
                    current_date += timedelta(weeks=1)
                elif task.periodicity == 'M':
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)
                elif task.periodicity == 'Y':
                    current_date = current_date.replace(year=current_date.year + 1)
                else:
                    break
            
            total_instances += instances_created

        if total_instances > 0:
            messages.success(
                request, f'Generated {total_instances} periodic task instances from {
                    periodic_tasks.count()} periodic task(s).')
        else:
            messages.info(
                request,
                'No new instances were generated (they may already exist).')
    generate_periodic_instances.short_description = "Generate periodic instances for selected periodic tasks"


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = [
        'status_icon',
        'timestamp',
        'templates_processed',
        'instances_created',
        'instances_cleaned',
        'templates_cleaned',
        'runtime_display',
        'error_count']
    list_filter = ['success', 'timestamp']
    readonly_fields = [
        'timestamp',
        'templates_processed',
        'instances_created',
        'instances_cleaned',
        'templates_cleaned',
        'runtime_seconds',
        'errors',
        'success']
    ordering = ['-timestamp']

    def status_icon(self, obj):
        """Display success/failure icon"""
        if obj.success:
            return format_html('<span style="color: green; font-size: 16px;">✅</span>')
        else:
            return format_html('<span style="color: red; font-size: 16px;">❌</span>')
    status_icon.short_description = 'Status'

    def runtime_display(self, obj):
        """Format runtime for display"""
        return f"{obj.runtime_seconds:.2f}s"
    runtime_display.short_description = 'Runtime'
    runtime_display.admin_order_field = 'runtime_seconds'

    def error_count(self, obj):
        """Display number of errors"""
        error_count = len(obj.errors) if obj.errors else 0
        if error_count > 0:
            return format_html(
                '<span style="color: red;">{} errors</span>',
                error_count)
        return "No errors"
    error_count.short_description = 'Errors'

    def has_add_permission(self, request):
        """Prevent manual creation of maintenance logs"""
        return False

    def has_change_permission(self, request, obj=None):
        """Make logs read-only"""
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'printing_method',
        'server_printing_enabled',
        'created_at',
        'updated_at'
    ]
    list_filter = [
        'printing_method',
        'server_printing_enabled',
        'created_at'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Printing Preferences', {
            'fields': ('printing_method', 'server_printing_enabled'),
            'description': 'Configure how this user prefers to print tasks'
        }),
        ('Local Printer Configuration', {
            'fields': ('printer_settings',),
            'description': 'Local printer preferences and settings',
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user"""
        return super().get_queryset(request).select_related('user')


@admin.register(PrintLog)
class PrintLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'user',
        'print_method',
        'print_type',
        'success_indicator',
        'tasks_attempted',
        'tasks_successful',
        'success_rate_display',
        'duration_display',
        'task_link'
    ]
    list_filter = [
        'success',
        'print_method',
        'print_type',
        'timestamp',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['user__username', 'task__title', 'error_message']
    readonly_fields = [
        'timestamp',
        'duration_ms',
        'success_rate_display',
        'print_settings_display',
        'printer_config_display'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Print Operation', {
            'fields': ('user', 'task', 'print_method', 'print_type', 'timestamp')
        }),
        ('Results', {
            'fields': ('success', 'tasks_attempted', 'tasks_successful', 'success_rate_display', 'duration_ms')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('print_settings_display', 'printer_config_display'),
            'classes': ('collapse',)
        }),
    )

    def success_indicator(self, obj):
        """Visual indicator for success/failure"""
        if obj.success:
            return format_html('<span style="color: green; font-weight: bold;">✅ Success</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">❌ Failed</span>')
    success_indicator.short_description = 'Status'
    success_indicator.admin_order_field = 'success'

    def success_rate_display(self, obj):
        """Display success rate as percentage"""
        rate = obj.success_rate()
        if rate == 100:
            color = 'green'
        elif rate >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color,
            rate
        )
    success_rate_display.short_description = 'Success Rate'

    def duration_display(self, obj):
        """Display duration in human-readable format"""
        if obj.duration_ms is None:
            return '-'
        
        if obj.duration_ms < 1000:
            return f"{obj.duration_ms}ms"
        elif obj.duration_ms < 60000:
            return f"{obj.duration_ms / 1000:.1f}s"
        else:
            minutes = obj.duration_ms // 60000
            seconds = (obj.duration_ms % 60000) // 1000
            return f"{minutes}m {seconds}s"
    duration_display.short_description = 'Duration'
    duration_display.admin_order_field = 'duration_ms'

    def task_link(self, obj):
        """Link to the related task if it exists"""
        if obj.task:
            url = reverse('admin:tasks_task_change', args=[obj.task.pk])
            return format_html('<a href="{}">{}</a>', url, obj.task.title[:50])
        return '-'
    task_link.short_description = 'Task'
    task_link.admin_order_field = 'task__title'

    def print_settings_display(self, obj):
        """Display print settings in a readable format"""
        if not obj.print_settings:
            return 'No settings recorded'
        
        settings_html = '<ul>'
        for key, value in obj.print_settings.items():
            settings_html += f'<li><strong>{key}:</strong> {value}</li>'
        settings_html += '</ul>'
        return format_html(settings_html)
    print_settings_display.short_description = 'Print Settings'

    def printer_config_display(self, obj):
        """Display printer configuration in a readable format"""
        if not obj.printer_config:
            return 'No configuration recorded'
        
        config_html = '<ul>'
        for key, value in obj.printer_config.items():
            config_html += f'<li><strong>{key}:</strong> {value}</li>'
        config_html += '</ul>'
        return format_html(config_html)
    printer_config_display.short_description = 'Printer Configuration'

    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        return super().get_queryset(request).select_related('user', 'task')
