from django.contrib import admin
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import Task, MaintenanceLog


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
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
        ('periodic_parent', admin.EmptyFieldListFilter),
    ]
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'periodic_instances_count']
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
                'periodicity_detail',
                'end_date',
                'periodic_parent',
                'periodic_instances_count'
            ),
            'classes': ('collapse',),
            'description': (
                'Configure recurring task behavior. Templates have '
                'is_periodic=True, instances have periodic_parent set.'
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
            icon = "🔄"  # Recurring template
        elif obj.periodic_parent:
            icon = "📅"  # Periodic instance
        else:
            icon = "📋"  # Regular task

        return f"{icon} {level_indicator}{obj.title}"
    hierarchical_title.short_description = 'Title'
    hierarchical_title.admin_order_field = 'title'

    def task_type(self, obj):
        """Show what type of task this is"""
        if obj.is_periodic:
            return format_html(
                '<span style="color: blue; font-weight: bold;">Template</span>')
        elif obj.periodic_parent:
            parent_link = reverse(
                'admin:tasks_task_change', args=[
                    obj.periodic_parent.id])
            return format_html(
                '<span style="color: green;">Instance</span><br><a href="{}" style="font-size: 0.8em;">→ {}</a>',
                parent_link,
                obj.periodic_parent.title[:20] + ('...' if len(obj.periodic_parent.title) > 20 else '')
            )
        else:
            return format_html('<span style="color: gray;">Regular</span>')
    task_type.short_description = 'Type'

    def periodic_status(self, obj):
        """Show periodic task status and details"""
        if obj.is_periodic:
            if obj.periodicity_type:
                status = f"{obj.periodicity_type.title()}"
                if obj.periodicity_detail:
                    if obj.periodicity_type == 'weekly' and 'weekdays' in obj.periodicity_detail:
                        weekdays = obj.periodicity_detail['weekdays']
                        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                        selected_days = [days[i] for i in weekdays]
                        status += f" ({', '.join(selected_days)})"
                return format_html('<span style="color: blue;">{}</span>', status)
            return format_html(
                '<span style="color: orange;">Template (incomplete)</span>')
        elif obj.periodic_parent:
            return format_html('<span style="color: green;">Instance</span>')
        return '-'
    periodic_status.short_description = 'Periodic Status'

    def periodic_instances_count(self, obj):
        """Show count of periodic instances"""
        if obj.is_periodic:
            from django.utils import timezone
            total = obj.periodic_instances.count()
            completed = obj.periodic_instances.filter(done=True).count()
            pending = total - completed

            # Count future instances that would be deleted
            current_date = timezone.now().date()
            future_instances = obj.periodic_instances.filter(
                due_date__date__gte=current_date
            ).count()

            return format_html(
                'Total: {} | Completed: {} | Pending: {}<br>'
                '<span style="color: red; font-size: 0.9em;">⚠️ {} future instances will be deleted if template is removed</span>',
                total,
                completed,
                pending,
                future_instances)
        return '-'
    periodic_instances_count.short_description = 'Instance Statistics'

    def get_queryset(self, request):
        """Order tasks to show hierarchy clearly and optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'parent',
            'owner',
            'periodic_parent').prefetch_related('periodic_instances')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize foreign key fields"""
        if db_field.name == "parent":
            # Only show tasks that can have subtasks (level < 2) and are not periodic
            # instances
            kwargs["queryset"] = Task.objects.filter(
                models.Q(
                    parent__isnull=True) | models.Q(
                    parent__parent__isnull=True)).filter(
                periodic_parent__isnull=True)  # Exclude periodic instances from being parents
        elif db_field.name == "periodic_parent":
            # Only show periodic templates
            kwargs["queryset"] = Task.objects.filter(is_periodic=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Customize form behavior"""
        form = super().get_form(request, obj, **kwargs)

        # Add help text for JSON field
        if 'periodicity_detail' in form.base_fields:
            form.base_fields['periodicity_detail'].help_text = mark_safe(
                'JSON format examples:<br>'
                '• Weekly: <code>{"weekdays": [0, 1, 2, 3, 4]}</code> (Mon-Fri)<br>'
                '• Monthly: <code>{"day_of_month": 15}</code> (15th of each month)<br>'
                'Weekdays: 0=Monday, 1=Tuesday, ..., 6=Sunday'
            )

        return form

    def delete_model(self, request, obj):
        """Override delete to handle validation and provide feedback"""
        try:
            # Count what will be deleted for periodic tasks
            if obj.is_periodic:
                from django.utils import timezone
                current_date = timezone.now().date()
                future_instances = obj.periodic_instances.filter(
                    due_date__date__gte=current_date
                )

                # Count total subtasks that will be deleted
                total_subtasks = 0
                for instance in future_instances:
                    total_subtasks += self._count_subtasks_recursive(instance)

                obj.delete()
                messages.success(
                    request, f'Periodic task template "{
                        obj.title}" was deleted successfully. ' f'CASCADE DELETION: This also removed {
                        future_instances.count()} future instances ' f'and {total_subtasks} associated subtasks.')
            elif not obj.is_periodic and obj.has_incomplete_subtasks():
                # This should trigger the ValidationError in the model
                obj.delete()
            else:
                obj.delete()
                if obj.periodic_parent:
                    messages.success(
                        request, f'Periodic instance "{
                            obj.title}" was deleted successfully.')
                else:
                    messages.success(
                        request, f'Task "{
                            obj.title}" was deleted successfully.')
        except ValidationError as e:
            messages.error(request, str(e))

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
        total_instances_deleted = 0
        total_subtasks_deleted = 0

        for obj in queryset:
            try:
                # Count what will be deleted for periodic tasks
                if obj.is_periodic:
                    from django.utils import timezone
                    current_date = timezone.now().date()
                    future_instances = obj.periodic_instances.filter(
                        due_date__date__gte=current_date
                    )

                    # Count total subtasks that will be deleted
                    for instance in future_instances:
                        total_subtasks_deleted += self._count_subtasks_recursive(
                            instance)

                    total_instances_deleted += future_instances.count()

                obj.delete()
                deleted_count += 1
            except ValidationError as e:
                errors.append(f'"{obj.title}": {str(e)}')

        if deleted_count > 0:
            success_msg = f'{deleted_count} task(s) deleted successfully.'
            if total_instances_deleted > 0:
                success_msg += f' This also removed {total_instances_deleted} future periodic instances and {total_subtasks_deleted} associated subtasks.'
            messages.success(request, success_msg)

        if errors:
            for error in errors:
                messages.error(request, error)

    def save_model(self, request, obj, form, change):
        """Override save to handle validation and periodic task generation"""
        try:
            if not change:  # If creating new task
                if not obj.owner:
                    obj.owner = request.user
            obj.save()

            # Generate periodic instances if this is a new periodic task
            if obj.is_periodic and not change:
                from .periodic_utils import generate_periodic_task_instances
                instances = generate_periodic_task_instances(obj)
                if instances:
                    messages.info(
                        request, f'Generated {
                            len(instances)} periodic task instances.')

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
            # Make periodic_parent readonly for existing tasks to prevent confusion
            if obj.periodic_parent:
                readonly_fields.extend(['is_periodic', 'periodic_parent'])
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
        from .periodic_utils import generate_periodic_task_instances

        periodic_tasks = queryset.filter(is_periodic=True)
        total_instances = 0

        for task in periodic_tasks:
            instances = generate_periodic_task_instances(task)
            total_instances += len(instances)

        if total_instances > 0:
            messages.success(
                request, f'Generated {total_instances} periodic task instances from {
                    periodic_tasks.count()} template(s).')
        else:
            messages.info(
                request,
                'No new instances were generated (they may already exist).')
    generate_periodic_instances.short_description = "Generate periodic instances for selected templates"


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
