from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes and styling
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
        
        # Update help text
        self.fields['username'].help_text = 'Enter the username you used when registering.'


class UserRegistrationForm(UserCreationForm):
    """Enhanced user registration form with email validation"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text='A valid email address is required for account activation.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        }),
        help_text='Your first name is required for personalization.'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        }),
        help_text='Your last name is required for personalization.'
    )
    
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input me-2'
        }),
        label='I accept the Terms of Use and Privacy Policy',
        error_messages={
            'required': 'You must accept the Terms of Use and Privacy Policy to register.'
        }
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields except checkboxes
        for field_name, field in self.fields.items():
            if field_name not in ['email', 'first_name', 'last_name', 'accept_terms']:  # Already have classes
                field.widget.attrs.update({'class': 'form-control'})
        
        # Update help texts and placeholders
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Confirm your password'
        })
        
        # Update help texts to be more ADHD-friendly
        self.fields['username'].help_text = 'Choose a username you\'ll remember easily. Letters, digits and @/./+/-/_ only.'
        self.fields['password1'].help_text = '''
        <ul>
            <li>Your password can't be too similar to your other personal information.</li>
            <li>Your password must contain at least 8 characters.</li>
            <li>Your password can't be a commonly used password.</li>
            <li>Your password can't be entirely numeric.</li>
        </ul>
        '''
    
    def clean_email(self):
        """Validate that the email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError(
                "A user with this email address already exists. "
                "Please use a different email or try logging in instead."
            )
        return email
    
    def save(self, commit=True):
        """Save the user with email and set inactive until confirmed"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = False  # User must activate account via email
        
        if commit:
            user.save()
        return user


class ResendActivationForm(forms.Form):
    """Form for resending activation email"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        help_text='Enter the email address you used to register.'
    )
    
    def clean_email(self):
        """Validate that the email exists and needs activation"""
        email = self.cleaned_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                if user.is_active:
                    raise ValidationError(
                        "This account is already active. Please try logging in instead."
                    )
            except User.DoesNotExist:
                raise ValidationError(
                    "No account found with this email address. Please register first."
                )
        return email