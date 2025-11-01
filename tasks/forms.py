from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Task


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

        # Initialize weekdays field if editing an existing periodic task
        if (self.instance.pk and self.instance.is_periodic
                and self.instance.periodicity_detail):
            weekdays = self.instance.periodicity_detail.get('weekdays', [])
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

        # For weekly tasks, save weekdays to periodicity_detail
        if is_periodic and periodicity_type == 'weekly':
            if weekdays:
                cleaned_data['periodicity_detail'] = {
                    'weekdays': [int(day) for day in weekdays]}
            else:
                # Default to the same weekday as start_date
                if start_date:
                    cleaned_data['periodicity_detail'] = {
                        'weekdays': [start_date.weekday()]}

        return cleaned_data
