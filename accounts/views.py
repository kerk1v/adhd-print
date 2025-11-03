from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.http import Http404
import logging

from .forms import UserRegistrationForm, ResendActivationForm
from .models import UserActivationToken, UserRegistrationAttempt

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get the client IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def send_activation_email(user, request):
    """Send activation email to the user"""
    try:
        # Create or get activation token
        token, created = UserActivationToken.objects.get_or_create(
            user=user,
            defaults={'is_used': False}
        )
        
        # If token exists but is expired, create a new one
        if not created and token.is_expired():
            token.delete()
            token = UserActivationToken.objects.create(user=user)
        
        # Build activation URL
        activation_url = request.build_absolute_uri(
            reverse('accounts:activate', kwargs={'token': str(token.token)})
        )
        
        # Prepare email context
        context = {
            'user': user,
            'activation_url': activation_url,
            'site_name': 'ADHD Print Task Manager',
            'expiry_days': settings.ACCOUNT_ACTIVATION_DAYS,
        }
        
        # Render email content
        subject = 'Activate your ADHD Print Task Manager account'
        message = render_to_string('accounts/activation_email.txt', context)
        html_message = render_to_string('accounts/activation_email.html', context)
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"Activation email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
        return False


@csrf_protect
@never_cache
def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('task_list')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save the user (inactive)
            user = form.save()
            
            # Track registration attempt
            registration_attempt = UserRegistrationAttempt.objects.create(
                email=user.email,
                username=user.username,
                ip_address=get_client_ip(request),
                activation_sent=False
            )
            
            # Send activation email
            if send_activation_email(user, request):
                registration_attempt.activation_sent = True
                registration_attempt.save()
                
                messages.success(
                    request,
                    f'Registration successful! We\'ve sent an activation link to {user.email}. '
                    f'Please check your email and click the link to activate your account.'
                )
                return redirect('accounts:registration_complete')
            else:
                messages.error(
                    request,
                    'Registration successful, but we couldn\'t send the activation email. '
                    'Please contact support or try resending the activation email.'
                )
                return redirect('accounts:resend_activation')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
@never_cache
def activate(request, token):
    """Account activation view"""
    try:
        activation_token = get_object_or_404(UserActivationToken, token=token)
        
        if not activation_token.is_valid():
            if activation_token.is_expired():
                messages.error(
                    request,
                    'This activation link has expired. Please request a new one.'
                )
                return redirect('accounts:resend_activation')
            else:
                messages.error(
                    request,
                    'This activation link has already been used.'
                )
                return redirect('accounts:login')
        
        # Activate the user
        user = activation_token.user
        user.is_active = True
        user.save()
        
        # Mark token as used
        activation_token.is_used = True
        activation_token.save()
        
        # Update registration attempt
        try:
            reg_attempt = UserRegistrationAttempt.objects.filter(
                email=user.email,
                username=user.username
            ).latest('timestamp')
            reg_attempt.activated = True
            reg_attempt.activated_at = timezone.now()
            reg_attempt.save()
        except UserRegistrationAttempt.DoesNotExist:
            pass
        
        # Log the user in automatically
        login(request, user)
        
        messages.success(
            request,
            f'Welcome to ADHD Print Task Manager, {user.first_name} {user.last_name}! '
            f'Your account has been successfully activated.'
        )
        
        logger.info(f"User {user.username} ({user.email}) activated their account")
        return redirect('task_list')
        
    except Exception as e:
        logger.error(f"Error during account activation: {str(e)}")
        messages.error(
            request,
            'An error occurred during account activation. Please try again or contact support.'
        )
        return redirect('accounts:login')


@csrf_protect
@never_cache
def resend_activation(request):
    """Resend activation email view"""
    if request.user.is_authenticated:
        return redirect('task_list')
    
    if request.method == 'POST':
        form = ResendActivationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email, is_active=False)
                
                if send_activation_email(user, request):
                    messages.success(
                        request,
                        f'A new activation link has been sent to {email}. '
                        f'Please check your email and click the link to activate your account.'
                    )
                    return redirect('accounts:registration_complete')
                else:
                    messages.error(
                        request,
                        'Failed to send activation email. Please try again later or contact support.'
                    )
            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                messages.success(
                    request,
                    f'If an inactive account with the email {email} exists, '
                    f'a new activation link has been sent.'
                )
                return redirect('accounts:registration_complete')
    else:
        form = ResendActivationForm()
    
    return render(request, 'accounts/resend_activation.html', {'form': form})


def registration_complete(request):
    """Registration complete view"""
    return render(request, 'accounts/registration_complete.html')


def terms_of_use(request):
    """Terms of use and privacy policy view"""
    return render(request, 'accounts/terms_of_use.html')
