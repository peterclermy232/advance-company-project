from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserRegistrationTests(APITestCase):
    """Test user registration flow"""
    
    def setUp(self):
        self.register_url = reverse('user-register')
        self.valid_data = {
            'email': 'test@example.com',
            'phone_number': '+254712345678',
            'full_name': 'Test User',
            'password': 'TestPass123!@#',
            'password_confirm': 'TestPass123!@#',
            'role': 'user'
        }
    
    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        
        user = User.objects.first()
        self.assertEqual(user.email, 'test@example.com')
        self.assertFalse(user.is_active)  # Should be inactive until verified
        self.assertFalse(user.email_verified)
        
        # Check verification email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verify', mail.outbox[0].subject.lower())
    
    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = self.valid_data.copy()
        data['password_confirm'] = 'DifferentPassword123!'
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
    
    def test_registration_weak_password(self):
        """Test registration with weak password"""
        data = self.valid_data.copy()
        data['password'] = 'weak'
        data['password_confirm'] = 'weak'
        
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registration_duplicate_email(self):
        """Test registration with existing email"""
        User.objects.create_user(
            email='test@example.com',
            phone_number='+254712345679',
            full_name='Existing User',
            password='Password123!'
        )
        
        response = self.client.post(self.register_url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailVerificationTests(APITestCase):
    """Test email verification flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+254712345678',
            full_name='Test User',
            password='TestPass123!',
            is_active=False,
            email_verified=False
        )
        self.user.generate_verification_token()
        self.verify_url = reverse('user-verify-email')
    
    def test_successful_verification(self):
        """Test successful email verification"""
        data = {
            'email': self.user.email,
            'token': self.user.email_verification_token
        }
        
        response = self.client.post(self.verify_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.email_verification_token)
    
    def test_verification_invalid_token(self):
        """Test verification with invalid token"""
        data = {
            'email': self.user.email,
            'token': 'invalid-token'
        }
        
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
    
    def test_verification_expired_token(self):
        """Test verification with expired token"""
        # Set token as sent 25 hours ago
        self.user.email_verification_sent_at = timezone.now() - timedelta(hours=25)
        self.user.save()
        
        data = {
            'email': self.user.email,
            'token': self.user.email_verification_token
        }
        
        response = self.client.post(self.verify_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Test login functionality"""
    
    def setUp(self):
        self.login_url = reverse('user-login')
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+254712345678',
            full_name='Test User',
            password='TestPass123!',
            email_verified=True,
            is_active=True
        )
    
    def test_successful_login(self):
        """Test successful login"""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
    
    def test_login_unverified_email(self):
        """Test login with unverified email"""
        self.user.email_verified = False
        self.user.save()
        
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('verify', response.data['error'].lower())
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_account_lockout_after_failed_attempts(self):
        """Test account lockout after multiple failed login attempts"""
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword!'
        }
        
        # Make 5 failed attempts
        for i in range(5):
            response = self.client.post(self.login_url, data)
        
        # 6th attempt should be locked
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('locked', response.data['error'].lower())


class PasswordResetTests(APITestCase):
    """Test password reset flow"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='+254712345678',
            full_name='Test User',
            password='OldPass123!',
            email_verified=True,
            is_active=True
        )
        self.forgot_url = reverse('user-forgot-password')
    
    def test_forgot_password_request(self):
        """Test forgot password request"""
        data = {'email': 'test@example.com'}
        
        response = self.client.post(self.forgot_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('reset', mail.outbox[0].subject.lower())
    
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email"""
        data = {'email': 'nonexistent@example.com'}
        
        response = self.client.post(self.forgot_url, data)
        
        # Should still return 200 to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
