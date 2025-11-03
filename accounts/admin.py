from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserActivationToken, UserRegistrationAttempt


@admin.register(UserActivationToken)
class UserActivationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'is_valid')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'expires_at')
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Valid'


@admin.register(UserRegistrationAttempt)
class UserRegistrationAttemptAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'timestamp', 'activation_sent', 'activated', 'activated_at', 'ip_address')
    list_filter = ('activation_sent', 'activated', 'timestamp')
    search_fields = ('username', 'email', 'ip_address')
    readonly_fields = ('timestamp', 'activated_at')
    
    def has_add_permission(self, request):
        # Don't allow manual creation of registration attempts
        return False
