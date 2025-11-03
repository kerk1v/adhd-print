from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from .models import UserActivationToken, UserRegistrationAttempt


class UserRegistrationTests(TestCase):
    """Test user registration functionality"""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
    
    def test_registration_page_loads(self):
        """Test that the registration page loads correctly"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')
        self.assertContains(response, 'Terms of Use and Privacy Policy')
    
    def test_checkbox_styling(self):
        """Test that the accept_terms checkbox has correct Bootstrap classes"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        
        # Check that the checkbox has the correct Bootstrap classes
        self.assertContains(response, 'class="form-check-input me-2"')
        
        # Verify it's inside a form-check div structure
        self.assertContains(response, '<div class="form-check">')
        self.assertContains(response, 'class="form-check-label"')
    
    def test_successful_registration(self):
        """Test successful user registration"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'accept_terms': True
        }
        
        response = self.client.post(self.register_url, data)
        
        # Should redirect to registration complete page
        self.assertEqual(response.status_code, 302)
        
        # User should be created but inactive
        user = User.objects.get(username='testuser')
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, 'test@example.com')
        
        # Activation token should be created
        self.assertTrue(hasattr(user, 'activation_token'))
        
        # Registration attempt should be tracked
        reg_attempt = UserRegistrationAttempt.objects.get(username='testuser')
        self.assertTrue(reg_attempt.activation_sent)
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate your ADHD Print', mail.outbox[0].subject)
    
    def test_duplicate_email_registration(self):
        """Test that duplicate email addresses are rejected"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='password123'
        )
        
        data = {
            'username': 'newuser',
            'email': 'test@example.com',  # Same email
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'accept_terms': True
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertContains(response, 'already exists')
    
    def test_password_mismatch(self):
        """Test password confirmation validation"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'differentpass!',  # Different password
            'accept_terms': True
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertContains(response, 'password')
    
    def test_missing_required_fields(self):
        """Test that required fields are validated"""
        # Test missing first name
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'accept_terms': True
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertContains(response, 'This field is required')
        
        # Test missing last name
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'password1': 'testpass123!',
            'password2': 'testpass123!',
            'accept_terms': True
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertContains(response, 'This field is required')
        
        # Test missing terms acceptance
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123!',
            'password2': 'testpass123!'
            # accept_terms missing
        }
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on form
        self.assertContains(response, 'You must accept the Terms of Use')


class UserActivationTests(TestCase):
    """Test user activation functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=False
        )
        self.token = UserActivationToken.objects.create(user=self.user)
        self.activate_url = reverse('accounts:activate', kwargs={'token': str(self.token.token)})
    
    def test_successful_activation(self):
        """Test successful account activation"""
        response = self.client.get(self.activate_url)
        
        # Should redirect (user is logged in)
        self.assertEqual(response.status_code, 302)
        
        # User should be activated
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        
        # Token should be marked as used
        self.token.refresh_from_db()
        self.assertTrue(self.token.is_used)
    
    def test_expired_token_activation(self):
        """Test activation with expired token"""
        # Make token expired
        self.token.expires_at = timezone.now() - timedelta(days=1)
        self.token.save()
        
        response = self.client.get(self.activate_url)
        
        # Should redirect to resend activation
        self.assertEqual(response.status_code, 302)
        
        # User should remain inactive
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
    
    def test_invalid_token_activation(self):
        """Test activation with invalid token"""
        import uuid
        invalid_token = uuid.uuid4()  # Valid UUID format but invalid token
        invalid_url = reverse('accounts:activate', kwargs={'token': str(invalid_token)})
        response = self.client.get(invalid_url)
        
        # Since the view catches exceptions and redirects to login, expect 302
        self.assertEqual(response.status_code, 302)


class LoginTests(TestCase):
    """Test login functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        self.login_url = reverse('accounts:login')
    
    def test_login_page_loads(self):
        """Test that the login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
        self.assertContains(response, 'ADHD Print')
    
    def test_successful_login(self):
        """Test successful login"""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Should redirect to tasks
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/tasks/', fetch_redirect_response=False)
    
    def test_inactive_user_login(self):
        """Test that inactive users cannot log in"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data)
        
        # Should stay on login page with error
        self.assertEqual(response.status_code, 200)


class ResendActivationTests(TestCase):
    """Test resend activation functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_active=False
        )
        self.resend_url = reverse('accounts:resend_activation')
    
    def test_resend_activation_page_loads(self):
        """Test that the resend activation page loads"""
        response = self.client.get(self.resend_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resend Activation Email')
    
    def test_resend_activation_email(self):
        """Test resending activation email"""
        data = {'email': 'test@example.com'}
        
        response = self.client.post(self.resend_url, data)
        
        # Should redirect to registration complete
        self.assertEqual(response.status_code, 302)
        
        # Email should be sent
        self.assertEqual(len(mail.outbox), 1)
    
    def test_resend_for_active_user(self):
        """Test resending activation for already active user"""
        self.user.is_active = True
        self.user.save()
        
        data = {'email': 'test@example.com'}
        
        response = self.client.post(self.resend_url, data)
        
        # Should stay on form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already active')
