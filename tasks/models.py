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
        ('every_x_days', 'Every X Days'),
        ('every_x_weeks', 'Every X Weeks'),
        ('every_x_months', 'Every X Months'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    urgency = models.CharField(max_length=10, choices=URGENCY_LEVELS, default='normal')
    due_date = models.DateTimeField(blank=True, null=True)
    is_printed = models.BooleanField(default=False, 
                                   help_text="Whether this task has been printed")
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
                # All subtasks are considered incomplete now (no done field)
                return True
            return False
        return check_subtasks(self)

    def get_all_subtasks(self):
        """Get all subtasks recursively"""
        all_subtasks = []

        def collect_subtasks(task):
            # For virtual periodic tasks (no pk), get subtasks from template
            if not task.pk and hasattr(task, '_template_task'):
                # Virtual task - get subtasks from template
                template_subtasks = task._template_task.subtasks.all()
                for template_subtask in template_subtasks:
                    # Create virtual subtask instances
                    virtual_subtask = Task(
                        title=template_subtask.title,
                        description=template_subtask.description,
                        urgency=template_subtask.urgency,
                        due_date=task.due_date,  # Use parent's due date
                        owner=template_subtask.owner,
                        parent=task,  # Virtual parent
                        is_periodic=False
                    )
                    virtual_subtask._template_task = template_subtask
                    all_subtasks.append(virtual_subtask)
                    collect_subtasks(virtual_subtask)
            else:
                # Regular task with pk - access subtasks normally
                for subtask in task.subtasks.all():
                    all_subtasks.append(subtask)
                    collect_subtasks(subtask)

        collect_subtasks(self)
        return all_subtasks

    @property
    def subtasks_for_template(self):
        """Get subtasks safely for template use - handles virtual instances"""
        if not self.pk and hasattr(self, '_template_task'):
            # Virtual task - return subtasks from template as virtual instances
            virtual_subtasks = []
            for template_subtask in self._template_task.subtasks.all():
                virtual_subtask = Task(
                    title=template_subtask.title,
                    description=template_subtask.description,
                    urgency=template_subtask.urgency,
                    due_date=self.due_date,  # Use parent's due date
                    owner=template_subtask.owner,
                    parent=self,  # Virtual parent
                    is_periodic=False
                )
                virtual_subtask._template_task = template_subtask
                virtual_subtasks.append(virtual_subtask)
            return virtual_subtasks
        else:
            # Regular task with pk - return normal subtasks
            return self.subtasks.all() if self.pk else []

    @property
    def task_identifier(self):
        """Get a unique identifier for this task - handles virtual instances"""
        if self.pk:
            # Regular task with database ID
            return self.pk
        elif hasattr(self, '_template_task') and hasattr(self, '_occurrence_date'):
            # Virtual periodic instance - create identifier from template and date
            return f"virtual_{self._template_task.pk}_{self._occurrence_date.strftime('%Y%m%d')}"
        elif hasattr(self, '_template_task'):
            # Virtual subtask - create identifier from template and parent
            if hasattr(self.parent, 'task_identifier'):
                return f"virtual_sub_{self._template_task.pk}_{self.parent.task_identifier}"
            else:
                return f"virtual_sub_{self._template_task.pk}"
        else:
            # Fallback for other virtual tasks
            return f"virtual_{id(self)}"

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

    def get_occurrences_in_range(self, start_date, end_date):
        """
        Get all occurrences of this periodic task within a date range.
        
        Args:
            start_date: Start date for the range (inclusive)
            end_date: End date for the range (inclusive)
            
        Returns:
            List of date objects representing occurrences
        """
        if not self.is_periodic or not self.start_date:
            return []
            
        occurrences = []
        current_date = max(start_date, self.start_date)
        
        # Check if we've passed the end date
        if self.end_date and current_date > self.end_date:
            return []
            
        while current_date <= end_date:
            # Check if we've passed the task's end date
            if self.end_date and current_date > self.end_date:
                break
                
            # Check if this date should have an occurrence
            if self._should_occur_on_date(current_date):
                occurrences.append(current_date)
                
            # Move to next day to check
            current_date += timezone.timedelta(days=1)
            
        return occurrences
    
    def _should_occur_on_date(self, check_date):
        """
        Check if this periodic task should occur on a specific date.
        
        Args:
            check_date: Date to check
            
        Returns:
            Boolean indicating if task should occur on this date
        """
        if not self.is_periodic or not self.start_date:
            return False
            
        if check_date < self.start_date:
            return False
            
        if self.end_date and check_date > self.end_date:
            return False
            
        if self.periodicity_type == 'daily':
            return True
            
        elif self.periodicity_type == 'weekly':
            weekdays = self.periodicity_detail.get('weekdays', []) if self.periodicity_detail else []
            if not weekdays:
                # Default to the same weekday as start_date
                weekdays = [self.start_date.weekday()]
            return check_date.weekday() in weekdays
            
        elif self.periodicity_type == 'monthly':
            return check_date.day == self.start_date.day
            
        elif self.periodicity_type == 'yearly':
            return (check_date.month == self.start_date.month and 
                   check_date.day == self.start_date.day)
                   
        elif self.periodicity_type == 'every_x_days':
            interval = self.periodicity_detail.get('interval', 1) if self.periodicity_detail else 1
            days_diff = (check_date - self.start_date).days
            return days_diff >= 0 and days_diff % interval == 0
            
        elif self.periodicity_type == 'every_x_weeks':
            interval = self.periodicity_detail.get('interval', 1) if self.periodicity_detail else 1
            # Must be on the same weekday as start_date
            if check_date.weekday() != self.start_date.weekday():
                return False
            weeks_diff = (check_date - self.start_date).days // 7
            return weeks_diff >= 0 and weeks_diff % interval == 0
            
        elif self.periodicity_type == 'every_x_months':
            interval = self.periodicity_detail.get('interval', 1) if self.periodicity_detail else 1
            
            # Calculate months between start_date and check_date
            months_diff = (check_date.year - self.start_date.year) * 12 + (check_date.month - self.start_date.month)
            
            if months_diff < 0 or months_diff % interval != 0:
                return False
                
            # Handle day matching with month-end considerations
            target_day = self.start_date.day
            
            # If the target day doesn't exist in the current month, use the last day of the month
            import calendar
            last_day_of_month = calendar.monthrange(check_date.year, check_date.month)[1]
            
            if target_day > last_day_of_month:
                # Use the last day of the month if target day doesn't exist
                return check_date.day == last_day_of_month
            else:
                return check_date.day == target_day
                   
        return False
    
    def get_virtual_instance_for_date(self, occurrence_date):
        """
        Create a virtual task instance representing this periodic task on a specific date.
        This doesn't create a database object, just returns a Task-like object with
        the appropriate values for the given occurrence date.
        
        Args:
            occurrence_date: Date for the virtual instance
            
        Returns:
            Task object (not saved to database) representing the virtual instance
        """
        if not self.is_periodic:
            return None
            
        # Create a virtual instance
        virtual_instance = Task(
            title=self.title,
            description=self.description,
            urgency=self.urgency,
            due_date=timezone.datetime.combine(
                occurrence_date,
                timezone.datetime.min.time().replace(tzinfo=timezone.get_current_timezone())
            ),
            owner=self.owner,
            parent=None,  # Virtual instances are always top-level
            is_periodic=False,  # Virtual instances are not periodic themselves
            created_at=self.created_at,
            is_printed=False  # Virtual instances are never pre-printed
        )
        
        # Set a special attribute to mark this as a virtual instance
        virtual_instance._is_virtual_periodic_instance = True
        virtual_instance._periodic_template = self
        virtual_instance._template_task = self  # For subtask access
        virtual_instance._occurrence_date = occurrence_date
        
        return virtual_instance

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
        """Override delete to prevent deletion of regular tasks with incomplete subtasks"""

        # For regular tasks (non-periodic), check if they have incomplete subtasks
        # This prevents accidental deletion of regular task hierarchies
        if not self.is_periodic and self.has_incomplete_subtasks():
            raise ValidationError(
                "Cannot delete task with incomplete subtasks. "
                "Please delete all subtasks first."
            )

        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
