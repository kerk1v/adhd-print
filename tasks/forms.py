from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Task, UserProfile


class TaskForm(forms.ModelForm):
    # Add weekday selection for weekly tasks
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input me-2'
        }),
        required=False,
        help_text="Select days of the week for weekly recurring tasks"
    )
    
    # Custom fields for interval-based periodicities
    interval_days = forms.IntegerField(
        min_value=1,
        max_value=365,
        required=False,
        help_text="Number of days between repetitions (1-365)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control interval-field', 
            'data-type': 'every_x_days',
            'placeholder': 'Enter days...'
        })
    )
    
    interval_weeks = forms.IntegerField(
        min_value=1,
        max_value=52,
        required=False,
        help_text="Number of weeks between repetitions (1-52)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control interval-field', 
            'data-type': 'every_x_weeks',
            'placeholder': 'Enter weeks...'
        })
    )
    
    interval_months = forms.IntegerField(
        min_value=1,
        max_value=24,
        required=False,
        help_text="Number of months between repetitions (1-24)",
        widget=forms.NumberInput(attrs={
            'class': 'form-control interval-field', 
            'data-type': 'every_x_months',
            'placeholder': 'Enter months...'
        })
    )

    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'urgency',
            'due_date',
            'done',
            'is_periodic',
            'start_date',
            'periodicity_type',
            'end_date',
            'periodicity_detail']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title...'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description...'
            }),
            'urgency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'done': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_periodic': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'togglePeriodicFields()'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'periodicity_type': forms.Select(attrs={
                'class': 'form-select',
                'onchange': 'toggleWeekdaySelection()'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['description'].required = False
        self.fields['due_date'].required = False
        self.fields['start_date'].required = False
        self.fields['end_date'].required = False

        # Set default start date to today for new periodic tasks
        if not self.instance.pk and not self.initial.get('start_date'):
            self.fields['start_date'].initial = timezone.now().date()

        # Initialize fields if editing an existing periodic task
        if (self.instance.pk and self.instance.is_periodic
                and self.instance.periodicity_detail):
            
            interval = self.instance.periodicity_detail.get('interval', 1)
            weekdays = self.instance.periodicity_detail.get('weekdays', [])
            
            # Populate interval fields based on periodicity type
            if self.instance.periodicity_type == 'every_x_days':
                self.fields['interval_days'].initial = interval
            elif self.instance.periodicity_type == 'every_x_weeks':
                self.fields['interval_weeks'].initial = interval
            elif self.instance.periodicity_type == 'every_x_months':
                self.fields['interval_months'].initial = interval
            elif self.instance.periodicity_type == 'weekly':
                self.fields['weekdays'].initial = weekdays

    def clean(self):
        cleaned_data = super().clean()
        is_periodic = cleaned_data.get('is_periodic')
        start_date = cleaned_data.get('start_date')
        periodicity_type = cleaned_data.get('periodicity_type')
        end_date = cleaned_data.get('end_date')
        weekdays = cleaned_data.get('weekdays')

        if is_periodic:
            if not start_date:
                raise ValidationError("Start date is required for periodic tasks.")
            if not periodicity_type:
                raise ValidationError(
                    "Periodicity type is required for periodic tasks.")
            if end_date and end_date < start_date:
                raise ValidationError("End date must be after start date.")

            # Handle interval-based periodicities
            if periodicity_type == 'every_x_days':
                interval = cleaned_data.get('interval_days')
                if not interval:
                    raise ValidationError({
                        'interval_days': 'This field is required for "Every X Days" periodicity.'
                    })
                cleaned_data['periodicity_detail'] = {'interval': interval}
                
            elif periodicity_type == 'every_x_weeks':
                interval = cleaned_data.get('interval_weeks')
                if not interval:
                    raise ValidationError({
                        'interval_weeks': 'This field is required for "Every X Weeks" periodicity.'
                    })
                cleaned_data['periodicity_detail'] = {'interval': interval}
                
            elif periodicity_type == 'every_x_months':
                interval = cleaned_data.get('interval_months')
                if not interval:
                    raise ValidationError({
                        'interval_months': 'This field is required for "Every X Months" periodicity.'
                    })
                cleaned_data['periodicity_detail'] = {'interval': interval}
                
            elif periodicity_type == 'weekly':
                # For weekly tasks, save weekdays to periodicity_detail
                if weekdays:
                    cleaned_data['periodicity_detail'] = {
                        'weekdays': [int(day) for day in weekdays]}
                else:
                    # Default to the same weekday as start_date
                    if start_date:
                        cleaned_data['periodicity_detail'] = {
                            'weekdays': [start_date.weekday()]}

        return cleaned_data


class TaskAdminForm(forms.ModelForm):
    """Custom form for Task admin with dynamic periodicity fields"""
    
    # Custom fields for interval-based periodicities
    interval_days = forms.IntegerField(
        min_value=1,
        max_value=365,
        required=False,
        help_text="Number of days between repetitions (1-365)",
        widget=forms.NumberInput(attrs={'class': 'interval-field', 'data-type': 'every_x_days'})
    )
    
    interval_weeks = forms.IntegerField(
        min_value=1,
        max_value=52,
        required=False,
        help_text="Number of weeks between repetitions (1-52)",
        widget=forms.NumberInput(attrs={'class': 'interval-field', 'data-type': 'every_x_weeks'})
    )
    
    interval_months = forms.IntegerField(
        min_value=1,
        max_value=24,
        required=False,
        help_text="Number of months between repetitions (1-24). Note: If you enter 12, consider using Yearly instead.",
        widget=forms.NumberInput(attrs={'class': 'interval-field', 'data-type': 'every_x_months'})
    )

    # Weekday selection for weekly tasks (keeping existing functionality)
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    weekdays = forms.MultipleChoiceField(
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select days of the week for weekly recurring tasks"
    )

    class Meta:
        model = Task
        fields = '__all__'
        widgets = {
            'periodicity_detail': forms.HiddenInput(),  # Hide the JSON field, we'll populate it automatically
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing an existing task, populate interval fields from periodicity_detail
        if self.instance.pk and self.instance.periodicity_detail:
            interval = self.instance.periodicity_detail.get('interval', 1)
            weekdays = self.instance.periodicity_detail.get('weekdays', [])
            
            if self.instance.periodicity_type == 'every_x_days':
                self.fields['interval_days'].initial = interval
            elif self.instance.periodicity_type == 'every_x_weeks':
                self.fields['interval_weeks'].initial = interval
            elif self.instance.periodicity_type == 'every_x_months':
                self.fields['interval_months'].initial = interval
            elif self.instance.periodicity_type == 'weekly':
                self.fields['weekdays'].initial = weekdays

    def clean(self):
        cleaned_data = super().clean()
        is_periodic = cleaned_data.get('is_periodic')
        periodicity_type = cleaned_data.get('periodicity_type')
        
        if is_periodic and periodicity_type:
            # Validate and set periodicity_detail based on periodicity_type
            if periodicity_type == 'every_x_days':
                interval = cleaned_data.get('interval_days')
                if not interval:
                    raise ValidationError({
                        'interval_days': 'This field is required for "Every X Days" periodicity.'
                    })
                cleaned_data['periodicity_detail'] = {'interval': interval}
                
            elif periodicity_type == 'every_x_weeks':
                interval = cleaned_data.get('interval_weeks')
                if not interval:
                    raise ValidationError({
                        'interval_weeks': 'This field is required for "Every X Weeks" periodicity.'
                    })
                cleaned_data['periodicity_detail'] = {'interval': interval}
                
            elif periodicity_type == 'every_x_months':
                interval = cleaned_data.get('interval_months')
                if not interval:
                    raise ValidationError({
                        'interval_months': 'This field is required for "Every X Months" periodicity.'
                    })
                
                # Suggest yearly if interval is 12
                if interval == 12:
                    self.add_error('interval_months', 
                        'Consider using "Yearly" periodicity instead of "Every 12 Months" for better clarity.')
                
                cleaned_data['periodicity_detail'] = {'interval': interval}
                
            elif periodicity_type == 'weekly':
                # Handle existing weekly logic
                weekdays = cleaned_data.get('weekdays')
                if weekdays:
                    cleaned_data['periodicity_detail'] = {
                        'weekdays': [int(day) for day in weekdays]
                    }
                else:
                    # Default to same weekday as start_date if no specific weekdays set
                    start_date = cleaned_data.get('start_date')
                    if start_date:
                        cleaned_data['periodicity_detail'] = {
                            'weekdays': [start_date.weekday()]
                        }
        
        return cleaned_data

    class Media:
        css = {
            'all': ('admin/css/periodic-task-admin.css',)
        }
        js = ('admin/js/periodic-task-admin.js',)


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile and printing preferences"""
    
    # Add custom field for printer width
    printer_width = forms.ChoiceField(
        choices=[
            ('80mm', '80mm (Standard receipts)'),
            ('57mm', '57mm (Narrow receipts)'),
        ],
        initial='80mm',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Printer Width',
        help_text='Select the width of your thermal printer paper'
    )
    
    class Meta:
        model = UserProfile
        fields = ['printing_method', 'server_printing_enabled']
        widgets = {
            'printing_method': forms.RadioSelect(attrs={
                'class': 'form-check-input',
                'onchange': 'togglePrintingMethod()'
            }),
            'server_printing_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'printing_method': 'Preferred Printing Method',
            'server_printing_enabled': 'Enable Server-Based Printing (only when local printing is not available)'
        }
        help_texts = {
            'printing_method': 'Choose your preferred method for printing tasks',
            'server_printing_enabled': 'Allow fallback to server printing when local printing fails or is unavailable'
        }

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs to check admin status
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes and customize labels
        self.fields['printing_method'].widget.attrs.update({
            'class': 'form-check-input'
        })
        
        # Customize choices based on server printing availability
        available_choices = [
            ('local', 'Local Printing (USB/Serial) - Print directly to connected thermal printer'),
        ]
        
        # Only show server printing option if it's enabled for this user
        if self.instance and self.instance.pk and self.instance.server_printing_enabled:
            available_choices.append(
                ('server', 'Server Printing - Print via network printer (requires server setup)')
            )
        
        self.fields['printing_method'].choices = available_choices
        
        # Only show server_printing_enabled field for admin users
        if not (self.user and self.user.is_staff):
            # Hide the server_printing_enabled field for non-admin users
            self.fields['server_printing_enabled'].widget = forms.HiddenInput()
            self.fields['server_printing_enabled'].label = ""
            self.fields['server_printing_enabled'].help_text = ""
        
        # Load printer width from printer_settings
        if self.instance and self.instance.pk:
            printer_width = self.instance.printer_settings.get('width', '80mm')
            self.fields['printer_width'].initial = printer_width

    def clean(self):
        cleaned_data = super().clean()
        printing_method = cleaned_data.get('printing_method')
        server_printing_enabled = cleaned_data.get('server_printing_enabled')
        
        # Validate that user can only select server printing if it's enabled for them
        if printing_method == 'server':
            if not (self.instance and self.instance.pk and self.instance.server_printing_enabled):
                raise ValidationError(
                    "Server printing is not enabled for your account. Please contact an administrator."
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Save printer width to printer_settings
        if not instance.printer_settings:
            instance.printer_settings = {}
        instance.printer_settings['width'] = self.cleaned_data['printer_width']
        
        if commit:
            instance.save()
        return instance
