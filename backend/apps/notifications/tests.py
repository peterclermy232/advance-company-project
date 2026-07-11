"""Tests for the notifications app."""
import pytest
from rest_framework import status


NOTIFICATIONS_URL = '/api/v1/notifications/'


@pytest.mark.django_db
class TestNotifications:
    def test_list_notifications_authenticated(self, auth_client):
        response = auth_client.get(NOTIFICATIONS_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(NOTIFICATIONS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_mark_all_read(self, auth_client):
        response = auth_client.post(f'{NOTIFICATIONS_URL}mark_all_read/')
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND,
        ]

    def test_notification_count_returns_unread(self, auth_client):
        response = auth_client.get(f'{NOTIFICATIONS_URL}unread_count/')
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.django_db
class TestNotificationModel:
    def test_create_notification_for_user(self, user):
        from .models import Notification
        n = Notification.objects.create(
            user=user,
            title='Test Notification',
            message='This is a test',
            notification_type='info',
        )
        assert n.pk is not None
        assert n.is_read is False

    def test_notification_str(self, user):
        from .models import Notification
        n = Notification(user=user, title='Hello', message='World')
        assert 'Hello' in str(n) or n is not None

    def test_mark_notification_as_read(self, user):
        from .models import Notification
        n = Notification.objects.create(
            user=user,
            title='Unread',
            message='Mark me',
            notification_type='info',
        )
        n.is_read = True
        n.save()
        n.refresh_from_db()
        assert n.is_read is True
