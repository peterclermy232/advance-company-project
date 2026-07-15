"""Tests for the applications app — member requests and admin approval workflow."""
import pytest
from rest_framework import status

from .models import Application


APPLICATIONS_URL = '/api/applications/'


def application_action_url(pk, action):
    return f'{APPLICATIONS_URL}{pk}/{action}/'


@pytest.mark.django_db
class TestApplicationCRUD:
    def _payload(self, **overrides):
        data = {
            'application_type': 'statement_request',
            'reason': 'Need a statement for the last 6 months.',
        }
        data.update(overrides)
        return data

    def test_create_application(self, auth_client):
        response = auth_client.post(APPLICATIONS_URL, self._payload())
        assert response.status_code == status.HTTP_201_CREATED

    def test_application_belongs_to_authenticated_user(self, auth_client, user):
        auth_client.post(APPLICATIONS_URL, self._payload())
        assert Application.objects.filter(user=user).exists()

    def test_application_initial_status_is_pending(self, auth_client, user):
        auth_client.post(APPLICATIONS_URL, self._payload())
        application = Application.objects.get(user=user)
        assert application.status == 'pending'

    def test_unauthenticated_cannot_create(self, api_client):
        response = api_client.post(APPLICATIONS_URL, self._payload())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_reason_rejected(self, auth_client):
        payload = self._payload()
        del payload['reason']
        response = auth_client.post(APPLICATIONS_URL, payload)
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_list_returns_only_own_applications(self, auth_client, user):
        from conftest import UserFactory
        other_user = UserFactory()
        Application.objects.create(
            user=user, application_type='other', reason='mine',
        )
        Application.objects.create(
            user=other_user, application_type='other', reason='not mine',
        )
        response = auth_client.get(APPLICATIONS_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if hasattr(response.data, 'get') else response.data
        reasons = [a.get('reason') for a in results]
        assert 'mine' in reasons
        assert 'not mine' not in reasons

    def test_admin_sees_all_applications(self, admin_client, user):
        Application.objects.create(user=user, application_type='other', reason='visible to admin')
        response = admin_client.get(APPLICATIONS_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if hasattr(response.data, 'get') else response.data
        reasons = [a.get('reason') for a in results]
        assert 'visible to admin' in reasons


@pytest.mark.django_db
class TestApplicationChoices:
    def test_choices_endpoint_returns_types_and_statuses(self, auth_client):
        response = auth_client.get(f'{APPLICATIONS_URL}choices/')
        assert response.status_code == status.HTTP_200_OK
        assert 'application_types' in response.data
        assert 'status_choices' in response.data


@pytest.mark.django_db
class TestApplicationApprovalWorkflow:
    def test_admin_can_approve_application(self, admin_client, user):
        application = Application.objects.create(
            user=user, application_type='other', reason='approve me',
        )
        response = admin_client.post(application_action_url(application.id, 'approve'))
        assert response.status_code == status.HTTP_200_OK

        application.refresh_from_db()
        assert application.status == 'approved'
        assert application.approved_at is not None

    def test_admin_can_reject_application(self, admin_client, user):
        application = Application.objects.create(
            user=user, application_type='other', reason='reject me',
        )
        response = admin_client.post(
            application_action_url(application.id, 'reject'),
            {'comments': 'Not eligible'},
        )
        assert response.status_code == status.HTTP_200_OK

        application.refresh_from_db()
        assert application.status == 'rejected'

    def test_admin_can_mark_under_review(self, admin_client, user):
        application = Application.objects.create(
            user=user, application_type='other', reason='review me',
        )
        response = admin_client.post(application_action_url(application.id, 'review'))
        assert response.status_code == status.HTTP_200_OK

        application.refresh_from_db()
        assert application.status == 'under_review'

    def test_regular_user_cannot_approve_application(self, auth_client, user):
        application = Application.objects.create(
            user=user, application_type='other', reason='not admin',
        )
        response = auth_client.post(application_action_url(application.id, 'approve'))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_approve_creates_activity_record(self, admin_client, user):
        application = Application.objects.create(
            user=user, application_type='other', reason='track activity',
        )
        admin_client.post(application_action_url(application.id, 'approve'))
        assert application.activities.filter(action='approved').exists()
