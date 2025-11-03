from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration URLs
    path('register/', views.register, name='register'),
    path('activate/<uuid:token>/', views.activate, name='activate'),
    path('resend-activation/', views.resend_activation, name='resend_activation'),
    path('registration-complete/', views.registration_complete, name='registration_complete'),
    
    # Static pages
    path('terms-of-use/', views.terms_of_use, name='terms_of_use'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password reset URLs
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]