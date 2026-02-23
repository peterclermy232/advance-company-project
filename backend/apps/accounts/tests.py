from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from .models import User


class UserRegistrationTest(APITestCase):
    url = '/api/v1/auth/register/'

    def _payload(self, **overrides):
        data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'phone_number': '+254712345678',
            'full_name': 'Test User',
        }
        data.update(overrides)
        return data

    @patch('apps.accounts.auth_views.send_verification_email')
    def test_register_creates_active_user(self, mock_email):
        """
        FIX 6: register() sets is_active=True and email_verified=False.
        Original test incorrectly expected is_active=False.
        """
        response = self.client.post(self.url, self._payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='test@example.com')
        self.assertTrue(user.is_active)           # active from day one
        self.assertFalse(user.email_verified)     # but email not yet verified
        mock_email.assert_called_once_with(user)

    @patch('apps.accounts.auth_views.send_verification_email')
    def test_register_returns_tokens(self, mock_email):
        response = self.client.post(self.url, self._payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data['data'])
        self.assertIn('access', response.data['data']['tokens'])
        self.assertIn('refresh', response.data['data']['tokens'])

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email='test@example.com',
            password='OldPass123!',
            phone_number='+254700000001',
            full_name='Existing User',
        )
        response = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_register_missing_email(self):
        payload = self._payload()
        del payload['email']
        response = self.client.post(self.url, payload, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ])


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='model@example.com',
            password='TestPass123!',
            phone_number='+254712345679',
            full_name='Model User',
        )

    def test_verify_backup_code_success(self):
        """FIX 7: verify_backup_code method must exist and work."""
        codes = self.user.generate_backup_codes()
        self.assertEqual(len(codes), 10)

        code_to_use = codes[0]
        result = self.user.verify_backup_code(code_to_use)

        self.assertTrue(result)
        # Code should be consumed
        self.user.refresh_from_db()
        self.assertNotIn(code_to_use, self.user.backup_codes)

    def test_verify_backup_code_invalid(self):
        """Invalid code returns False."""
        self.user.generate_backup_codes()
        result = self.user.verify_backup_code('INVALID')
        self.assertFalse(result)

    def test_verify_backup_code_single_use(self):
        """Each backup code can only be used once."""
        codes = self.user.generate_backup_codes()
        code = codes[0]

        first_use = self.user.verify_backup_code(code)
        second_use = self.user.verify_backup_code(code)

        self.assertTrue(first_use)
        self.assertFalse(second_use)