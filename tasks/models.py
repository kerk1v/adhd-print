from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Task(models.Model):
    URGENCY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    PERIODICITY_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    urgency = models.CharField(max_length=10, choices=URGENCY_LEVELS, default='normal')
    due_date = models.DateTimeField(blank=True, null=True)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_tasks')
    parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='subtasks')

    # Periodic task fields
    is_periodic = models.BooleanField(default=False,
                                      help_text="Check if this is a repeating task")
    start_date = models.DateField(
        blank=True,
        null=True,
        help_text="Start date for periodic tasks")
    periodicity_type = models.CharField(
        max_length=20,
        choices=PERIODICITY_TYPES,
        blank=True,
        null=True,
        help_text="How often the task repeats"
    )
    periodicity_detail = models.JSONField(
        blank=True,
        null=True,
        help_text="Additional details for periodicity (e.g., weekdays for weekly tasks)"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="End date for periodic tasks (leave empty for no end)"
    )
    periodic_parent = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='periodic_instances',
        help_text="Reference to the original periodic task template"
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        level_indicator = "  " * self.get_level()
        return f"{level_indicator}{self.title} ({self.get_urgency_display()})"

    def get_level(self):
        """Get the nesting level of this task (0 = root, 1 = level 1, etc.)"""
        level = 0
        current = self.parent
        while current is not None and level < 3:  # Limit to 3 levels
            level += 1
            current = current.parent
        return level

    def can_add_subtask(self):
        """Check if this task can have subtasks (max 3 levels)"""
        return self.get_level() < 2  # 0, 1 can have subtasks; 2 cannot

    def has_incomplete_subtasks(self):
        """Check if this task has any incomplete subtasks at any level"""
        def check_subtasks(task):
            for subtask in task.subtasks.all():
                if not subtask.done:
                    return True
                if check_subtasks(subtask):
                    return True
            return False
        return check_subtasks(self)

    def get_all_subtasks(self):
        """Get all subtasks recursively"""
        all_subtasks = []

        def collect_subtasks(task):
            for subtask in task.subtasks.all():
                all_subtasks.append(subtask)
                collect_subtasks(subtask)

        collect_subtasks(self)
        return all_subtasks

    def get_hierarchy_path(self):
        """Get the full hierarchy path for this task"""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    def get_hierarchy_string(self):
        """Get the hierarchy as a formatted string"""
        path = self.get_hierarchy_path()
        return " → ".join([task.title for task in path])

    def get_periodic_template_info(self):
        """
        Get information about periodic template if this task is part of a periodic hierarchy.
        
        Returns:
            dict with 'is_periodic_instance', 'template', 'instance_root', 'template_counterpart'
        """
        # Check if this task is directly a periodic instance
        if self.periodic_parent:
            return {
                'is_periodic_instance': True,
                'template': self.periodic_parent,
                'instance_root': self,
                'template_counterpart': self.periodic_parent
            }
        
        # Check if this task is part of a periodic hierarchy (instance or template)
        current = self.parent
        while current:
            if current.periodic_parent:
                # Found a periodic instance root
                template = current.periodic_parent
                
                # Build path from instance root to this task
                path_to_task = []
                temp = self
                while temp != current:
                    path_to_task.insert(0, temp.title)
                    temp = temp.parent
                
                # Find corresponding task in template hierarchy
                template_counterpart = template
                for title in path_to_task:
                    try:
                        template_counterpart = template_counterpart.subtasks.get(title=title)
                    except Task.DoesNotExist:
                        template_counterpart = None
                        break
                
                return {
                    'is_periodic_instance': True,
                    'template': template,
                    'instance_root': current,
                    'template_counterpart': template_counterpart
                }
            elif current.is_periodic:
                # Found a periodic template - this task is a template subtask
                template = current
                
                # Build path from template to this task
                path_to_task = []
                temp = self
                while temp != current:
                    path_to_task.insert(0, temp.title)
                    temp = temp.parent
                
                # The template counterpart is this task itself
                return {
                    'is_periodic_instance': False,  # This is template, not instance
                    'template': template,
                    'instance_root': None,
                    'template_counterpart': self  # Template subtask references itself
                }
            current = current.parent
        
        return {
            'is_periodic_instance': False,
            'template': None,
            'instance_root': None,
            'template_counterpart': None
        }

    def clean(self):
        """Custom validation"""
        # Check nesting level
        if self.parent and self.parent.get_level() >= 2:
            raise ValidationError("Tasks can only be nested up to 3 levels deep.")

        # Prevent circular references
        if self.parent:
            current = self.parent
            while current:
                if current.id == self.id:
                    raise ValidationError("A task cannot be a subtask of itself.")
                current = current.parent

        # Periodic task validation
        if self.is_periodic:
            if not self.start_date:
                raise ValidationError("Periodic tasks must have a start date.")
            if not self.periodicity_type:
                raise ValidationError(
                    "Periodic tasks must specify how often they repeat.")
            if self.end_date and self.end_date < self.start_date:
                raise ValidationError("End date must be after start date.")
            if self.parent:
                raise ValidationError("Periodic tasks cannot be subtasks.")

            # Validate periodicity details for weekly tasks
            if self.periodicity_type == 'weekly' and self.periodicity_detail:
                weekdays = self.periodicity_detail.get('weekdays', [])
                if weekdays and not all(0 <= day <= 6 for day in weekdays):
                    raise ValidationError(
                        "Weekly task weekdays must be between 0 (Monday) "
                        "and 6 (Sunday).")

    def is_periodic_instance(self):
        """Check if this task is an instance generated from a periodic task"""
        return self.periodic_parent is not None

    def get_next_occurrence(self, from_date=None):
        """Calculate the next occurrence date for a periodic task"""
        if not self.is_periodic or not self.start_date:
            return None

        if from_date is None:
            from_date = timezone.now().date()

        # Start from the later of from_date or start_date
        current_date = max(from_date, self.start_date)

        # Check if we've passed the end date
        if self.end_date and current_date > self.end_date:
            return None

        if self.periodicity_type == 'daily':
            return current_date

        elif self.periodicity_type == 'weekly':
            weekdays = self.periodicity_detail.get(
                'weekdays', []) if self.periodicity_detail else []
            if not weekdays:
                # Default to the same weekday as start_date
                weekdays = [self.start_date.weekday()]

            # Find the next occurrence
            for i in range(7):  # Check next 7 days
                check_date = current_date + timezone.timedelta(days=i)
                if check_date.weekday() in weekdays:
                    if self.end_date is None or check_date <= self.end_date:
                        return check_date
            return None

        elif self.periodicity_type == 'monthly':
            # Same day of month
            try:
                next_month = current_date.replace(day=self.start_date.day)
                if next_month < current_date:
                    # Move to next month
                    if current_date.month == 12:
                        next_month = next_month.replace(
                            year=current_date.year + 1, month=1)
                    else:
                        next_month = next_month.replace(month=current_date.month + 1)

                if self.end_date is None or next_month <= self.end_date:
                    return next_month
            except ValueError:
                # Handle cases like Feb 31 -> Feb 28/29
                import calendar
                if current_date.month == 12:
                    year, month = current_date.year + 1, 1
                else:
                    year, month = current_date.year, current_date.month + 1

                max_day = calendar.monthrange(year, month)[1]
                day = min(self.start_date.day, max_day)
                next_month = timezone.datetime(year, month, day).date()

                if self.end_date is None or next_month <= self.end_date:
                    return next_month
            return None

        elif self.periodicity_type == 'yearly':
            # Same day and month each year
            try:
                next_year = current_date.replace(
                    year=current_date.year if current_date < self.start_date.replace(
                        year=current_date.year) else current_date.year + 1,
                    month=self.start_date.month,
                    day=self.start_date.day)
                if self.end_date is None or next_year <= self.end_date:
                    return next_year
            except ValueError:
                # Handle leap year edge case (Feb 29)
                year = current_date.year if current_date < self.start_date.replace(
                    year=current_date.year) else current_date.year + 1
                next_year = timezone.datetime(year, self.start_date.month, 28).date()
                if self.end_date is None or next_year <= self.end_date:
                    return next_year
            return None

        return None

    def delete(self, *args, **kwargs):
        """Override delete to handle periodic tasks and prevent deletion of regular tasks with incomplete subtasks"""

        # If this is a periodic template, delete all its instances first (cascade
        # deletion allowed)
        if self.is_periodic:
            # Get all future instances (including today and beyond)
            current_date = timezone.now().date()
            future_instances = self.periodic_instances.filter(
                due_date__date__gte=current_date
            ).order_by('-due_date')  # Delete in reverse order (newest first)

            # Delete each instance and its subtask hierarchy
            for instance in future_instances:
                self._delete_task_hierarchy(instance)

        # For regular tasks (non-periodic), check if they have incomplete subtasks
        # This prevents accidental deletion of regular task hierarchies
        elif not self.is_periodic and self.has_incomplete_subtasks():
            raise ValidationError(
                "Cannot delete task with incomplete subtasks. "
                "Please complete or delete all subtasks first."
            )

        # For periodic instances (tasks with periodic_parent), allow deletion
        # without checking subtasks. This is needed when the template is being
        # deleted and instances need to
        # be cascaded

        super().delete(*args, **kwargs)

    def _delete_task_hierarchy(self, task):
        """
        Recursively delete a task and all its subtasks, starting from the deepest level.
        This ensures foreign key constraints are respected.
        """
        # Get all subtasks at all levels
        def get_all_subtasks(parent_task):
            """Recursively collect all subtasks in depth-first order"""
            subtasks = []
            for subtask in parent_task.subtasks.all():
                subtasks.extend(get_all_subtasks(subtask))  # Get children first
                subtasks.append(subtask)  # Then add the subtask itself
            return subtasks

        # Get all subtasks in reverse hierarchical order (deepest first)
        all_subtasks = get_all_subtasks(task)

        # Delete all subtasks first (deepest to shallowest)
        for subtask in all_subtasks:
            super(Task, subtask).delete()  # Use parent's delete to avoid recursion

        # Finally delete the parent task
        super(Task, task).delete()  # Use parent's delete to avoid recursion

    def save(self, *args, **kwargs):
        # Check if this is a new task being created (not an update)
        is_new_task = self.pk is None

        self.full_clean()
        super().save(*args, **kwargs)

        # If this is a new subtask of a periodic template or its subtasks,
        # create corresponding instances for existing periodic instances
        if is_new_task and self.parent:
            self._handle_new_subtask_creation()

    def _handle_new_subtask_creation(self):
        """
        Handle creation of subtask instances when a new subtask is added to a
        periodic template.
        """
        # Find if this subtask belongs to a periodic template hierarchy
        current_task = self.parent
        periodic_template = None

        # Traverse up the hierarchy to find the periodic template
        while current_task:
            if current_task.is_periodic:
                periodic_template = current_task
                break
            current_task = current_task.parent

        # If we found a periodic template, create instances for existing
        # periodic instances
        if periodic_template:
            from .periodic_utils import (
                create_subtask_instances_for_existing_periodic_instances
            )
            create_subtask_instances_for_existing_periodic_instances(self)


class MaintenanceLog(models.Model):
    """
    Log entries for background maintenance operations
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    templates_processed = models.IntegerField(default=0)
    instances_created = models.IntegerField(default=0)
    instances_cleaned = models.IntegerField(default=0)
    templates_cleaned = models.IntegerField(default=0)  # Expired templates deleted
    runtime_seconds = models.FloatField(default=0.0)
    errors = models.JSONField(default=list, blank=True)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Maintenance Log'
        verbose_name_plural = 'Maintenance Logs'

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {
            self.timestamp.strftime('%Y-%m-%d %H:%M')} - {
            self.instances_created} instances created"


class PrintLog(models.Model):
    """
    Log entries for print operations for troubleshooting and history tracking
    """
    PRINT_METHODS = [
        ('server', 'Server-based Printing'),
        ('local', 'Local Printing (USB/Serial)'),
    ]
    
    PRINT_TYPES = [
        ('single_task', 'Single Task'),
        ('task_hierarchy', 'Task with Subtasks'),
        ('todays_tasks', "Today's Tasks"),
        ('bulk_print', 'Bulk Print Operation'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User who initiated the print operation"
    )
    task = models.ForeignKey(
        'Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Primary task being printed (if applicable)"
    )
    print_method = models.CharField(
        max_length=10,
        choices=PRINT_METHODS,
        help_text="Method used for printing"
    )
    print_type = models.CharField(
        max_length=15,
        choices=PRINT_TYPES,
        help_text="Type of print operation"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the print operation was successful"
    )
    tasks_attempted = models.IntegerField(
        default=1,
        help_text="Number of tasks attempted to print"
    )
    tasks_successful = models.IntegerField(
        default=0,
        help_text="Number of tasks successfully printed"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if print failed"
    )
    printer_config = models.JSONField(
        default=dict,
        blank=True,
        help_text="Printer configuration at time of print (for debugging)"
    )
    print_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Print settings used (graphics mode, paper size, etc.)"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Print operation duration in milliseconds"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Print Log'
        verbose_name_plural = 'Print Logs'

    def __str__(self):
        status = "✅" if self.success else "❌"
        method = self.get_print_method_display()
        task_info = f" - {self.task.title}" if self.task else ""
        timestamp_str = self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else "Unsaved"
        return f"{status} {timestamp_str} [{method}] {self.get_print_type_display()}{task_info}"

    def success_rate(self):
        """Calculate success rate as percentage"""
        if self.tasks_attempted == 0:
            return 0
        return round((self.tasks_successful / self.tasks_attempted) * 100, 1)


class UserProfile(models.Model):
    """
    User profile with printing preferences and settings
    """
    PRINTING_METHODS = [
        ('server', 'Server-based Printing'),
        ('local', 'Local Printing (USB/Serial)'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    printing_method = models.CharField(
        max_length=10,
        choices=PRINTING_METHODS,
        default='local',
        help_text="Preferred printing method"
    )
    preferred_local_printer = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stored local printer configuration"
    )
    printer_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="General printer settings (paper size, quality, etc.)"
    )
    server_printing_enabled = models.BooleanField(
        default=False,
        help_text="Whether server-based printing is available for this user"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.get_printing_method_display()})"

    def get_effective_printing_method(self):
        """
        Determine the actual printing method to use based on user preference
        and system capabilities
        """
        if self.printing_method == 'server' and self.server_printing_enabled:
            return 'server'
        else:
            return 'local'

    def has_local_printer_configured(self):
        """Check if user has a local printer configured"""
        return bool(self.preferred_local_printer.get('device_id'))


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Create profile if it doesn't exist (for existing users)
        UserProfile.objects.get_or_create(user=instance)
