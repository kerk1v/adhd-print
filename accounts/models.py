from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid


class UserActivationToken(models.Model):
    """Model to store user activation tokens for email confirmation"""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='activation_token'
    )
    token = models.UUIDField(
        default=uuid.uuid4, 
        unique=True, 
        editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "User Activation Token"
        verbose_name_plural = "User Activation Tokens"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration time based on settings
            from django.conf import settings
            days = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 7)
            self.expires_at = timezone.now() + timedelta(days=days)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if the activation token has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if the token is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def __str__(self):
        return f"Activation token for {self.user.username}"


class UserRegistrationAttempt(models.Model):
    """Model to track registration attempts for analytics and security"""
    
    email = models.EmailField()
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    activation_sent = models.BooleanField(default=False)
    activated = models.BooleanField(default=False)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "User Registration Attempt"
        verbose_name_plural = "User Registration Attempts"
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Activated" if self.activated else "Pending"
        return f"{self.username} ({self.email}) - {status}"
