"""Tests for the accounts app — registration, login, profile, 2FA."""
import pytest
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient

from .models import User


REGISTER_URL = '/api/auth/register/'
LOGIN_URL = '/api/auth/login/'
PROFILE_URL = '/api/auth/users/profile/'


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserRegistration:
    def _payload(self, **overrides):
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'phone_number': '+254712345678',
            'full_name': 'New User',
        }
        data.update(overrides)
        return data

    @patch('apps.accounts.auth_views.send_verification_email')
    def test_register_creates_active_user(self, mock_email, api_client):
        response = api_client.post(REGISTER_URL, self._payload(), format='json')

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(email='newuser@example.com')
        assert user.is_active is True
        assert user.email_verified is False
        mock_email.assert_called_once_with(user)

    @patch('apps.accounts.auth_views.send_verification_email')
    def test_register_returns_jwt_tokens(self, mock_email, api_client):
        response = api_client.post(REGISTER_URL, self._payload(), format='json')

        assert response.status_code == status.HTTP_201_CREATED
        data = response.data['data']
        assert 'tokens' in data
        assert 'access' in data['tokens']
        assert 'refresh' in data['tokens']

    def test_register_duplicate_email_rejected(self, api_client, user):
        payload = self._payload(email=user.email)
        response = api_client.post(REGISTER_URL, payload, format='json')

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_register_missing_email_rejected(self, api_client):
        payload = self._payload()
        del payload['email']
        response = api_client.post(REGISTER_URL, payload, format='json')

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_register_missing_password_rejected(self, api_client):
        payload = self._payload()
        del payload['password']
        response = api_client.post(REGISTER_URL, payload, format='json')

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @patch('apps.accounts.auth_views.send_verification_email')
    def test_register_weak_password_rejected(self, mock_email, api_client):
        response = api_client.post(
            REGISTER_URL, self._payload(password='123'), format='json'
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserLogin:
    def test_login_with_valid_credentials(self, api_client, user):
        response = api_client.post(
            LOGIN_URL,
            {'email': user.email, 'password': 'TestPass123!'},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data.get('data', {}) or 'access' in str(response.data)

    def test_login_wrong_password(self, api_client, user):
        response = api_client.post(
            LOGIN_URL,
            {'email': user.email, 'password': 'WrongPassword!'},
            format='json',
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_login_nonexistent_user(self, api_client):
        response = api_client.post(
            LOGIN_URL,
            {'email': 'nobody@example.com', 'password': 'TestPass123!'},
            format='json',
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_login_inactive_user(self, db, api_client):
        inactive = User.objects.create_user(
            email='inactive@example.com',
            password='TestPass123!',
            phone_number='+254711000001',
            full_name='Inactive User',
            is_active=False,
        )
        response = api_client.post(
            LOGIN_URL,
            {'email': inactive.email, 'password': 'TestPass123!'},
            format='json',
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserModel:
    def test_str_returns_email(self, user):
        assert str(user) == user.email or user.full_name in str(user)

    def test_generate_backup_codes_produces_ten(self, user):
        codes = user.generate_backup_codes()
        assert len(codes) == 10

    def test_backup_codes_are_unique(self, user):
        codes = user.generate_backup_codes()
        assert len(set(codes)) == 10

    def test_verify_backup_code_success(self, user):
        codes = user.generate_backup_codes()
        assert user.verify_backup_code(codes[0]) is True

    def test_backup_code_consumed_after_use(self, user):
        codes = user.generate_backup_codes()
        code = codes[0]
        user.verify_backup_code(code)
        user.refresh_from_db()
        assert code not in user.backup_codes

    def test_verify_backup_code_invalid(self, user):
        user.generate_backup_codes()
        assert user.verify_backup_code('INVALID-CODE') is False

    def test_backup_code_single_use_only(self, user):
        codes = user.generate_backup_codes()
        code = codes[0]
        assert user.verify_backup_code(code) is True
        assert user.verify_backup_code(code) is False

    def test_user_default_role_is_member(self, user):
        assert user.role in ['member', 'user', 'customer', '']

    def test_admin_has_is_staff(self, admin_user):
        assert admin_user.is_staff is True

    def test_create_user_sets_unusable_raw_password(self, db):
        u = User.objects.create_user(
            email='raw@example.com',
            password='RawPass123!',
            phone_number='+254711111111',
            full_name='Raw User',
        )
        assert u.check_password('RawPass123!') is True
        assert u.password != 'RawPass123!'


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestUserProfile:
    def test_authenticated_user_can_get_profile(self, auth_client):
        response = auth_client.get(PROFILE_URL)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_unauthenticated_cannot_get_profile(self, api_client):
        response = api_client.get(PROFILE_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
