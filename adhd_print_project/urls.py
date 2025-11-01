"""
URL configuration for adhd_print_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

# Import debug view
import sys
sys.path.append('/Users/volker/adhd-print')
from debug_print_view import debug_print_modal
from auth_check_view import auth_check, auth_check_public

# Customize admin site
admin.site.site_header = "Task Management Admin"
admin.site.site_title = "Task Management"
admin.site.index_title = "Welcome to Task Management Administration"


class CustomLoginView(auth_views.LoginView):
    """Custom login view that always redirects to tasks page"""

    def get_success_url(self):
        return '/tasks/'


urlpatterns = [
    path(
        'admin/login/',
        CustomLoginView.as_view(
            template_name='admin/login.html'),
        name='admin_login'),
    path(
        'admin/',
        admin.site.urls),
    path(
        'debug-print/',
        debug_print_modal,
        name='debug_print'),
    path(
        'auth-check/',
        auth_check_public,
        name='auth_check'),
    path(
        '',
        include('tasks.urls')),
]
