"""Tests for the reports app — member reports and activity logs."""
import pytest
from io import BytesIO
from rest_framework import status

from .models import Report, ActivityLog


REPORTS_URL = '/api/reports/'
ACTIVITY_LOGS_URL = '/api/reports/activity-logs/'


@pytest.mark.django_db
class TestReportCRUD:
    def _payload(self, **overrides):
        data = {
            'title': 'Test Report',
            'report_type': 'FEEDBACK',
        }
        data.update(overrides)
        return data

    def test_create_report(self, auth_client):
        response = auth_client.post(REPORTS_URL, self._payload())
        assert response.status_code == status.HTTP_201_CREATED

    def test_report_belongs_to_authenticated_user(self, auth_client, user):
        # Regression test: perform_create() used to reference a bare
        # `request.user` (a NameError, since `request` isn't in scope)
        # instead of `self.request.user`, so every plain create crashed.
        auth_client.post(REPORTS_URL, self._payload())
        report = Report.objects.get(user=user)
        assert report.user == user
        assert report.generated_by == user

    def test_unauthenticated_cannot_create_report(self, api_client):
        response = api_client.post(REPORTS_URL, self._payload())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_returns_only_own_reports(self, auth_client, user):
        from conftest import UserFactory
        other_user = UserFactory()
        Report.objects.create(user=user, title='Mine', report_type='FEEDBACK', generated_by=user)
        Report.objects.create(user=other_user, title='Not mine', report_type='FEEDBACK', generated_by=other_user)

        response = auth_client.get(REPORTS_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if hasattr(response.data, 'get') else response.data
        titles = [r.get('title') for r in results]
        assert 'Mine' in titles
        assert 'Not mine' not in titles

    def test_admin_sees_all_reports(self, admin_client, user):
        Report.objects.create(user=user, title='Visible to admin', report_type='FEEDBACK', generated_by=user)
        response = admin_client.get(REPORTS_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if hasattr(response.data, 'get') else response.data
        titles = [r.get('title') for r in results]
        assert 'Visible to admin' in titles


@pytest.mark.django_db
class TestReportDashboard:
    def test_dashboard_summary_returns_200(self, auth_client):
        response = auth_client.get(f'{REPORTS_URL}dashboard_summary/')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_contributions' in response.data

    def test_admin_summary_requires_admin(self, auth_client):
        response = auth_client.get(f'{REPORTS_URL}summary/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_summary_returns_200_for_admin(self, admin_client):
        response = admin_client.get(f'{REPORTS_URL}summary/')
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data

    def test_deposit_trends_requires_admin(self, auth_client):
        response = auth_client.get(f'{REPORTS_URL}deposit_trends/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_deposit_trends_returns_200_for_admin(self, admin_client):
        response = admin_client.get(f'{REPORTS_URL}deposit_trends/')
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestGenerateFinancialReport:
    def test_generate_financial_report_success(self, auth_client, user, mocker):
        mocker.patch(
            'apps.reports.views.generate_financial_pdf_report',
            return_value=BytesIO(b'%PDF-1.4 fake report'),
        )
        mocker.patch(
            'apps.reports.views.upload_report_to_supabase',
            return_value='financial/fake-report.pdf',
        )
        mocker.patch(
            'apps.reports.views.generate_signed_url',
            return_value='https://example.supabase.co/signed/fake-report.pdf',
        )
        mocker.patch('apps.reports.views.send_report_email')

        response = auth_client.post(f'{REPORTS_URL}generate_financial_report/', {})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True

        report = Report.objects.get(user=user, report_type='FINANCIAL')
        assert report.status == 'RESOLVED'

    def test_generate_financial_report_handles_upload_failure(self, auth_client, mocker):
        mocker.patch(
            'apps.reports.views.generate_financial_pdf_report',
            return_value=BytesIO(b'%PDF-1.4 fake report'),
        )
        mocker.patch(
            'apps.reports.views.upload_report_to_supabase',
            side_effect=Exception('Supabase is down'),
        )

        response = auth_client.post(f'{REPORTS_URL}generate_financial_report/', {})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['success'] is False


@pytest.mark.django_db
class TestActivityLog:
    def test_list_returns_only_own_activity(self, auth_client, user):
        from conftest import UserFactory
        other_user = UserFactory()
        ActivityLog.objects.create(user=user, action='deposit_created')
        ActivityLog.objects.create(user=other_user, action='deposit_created')

        response = auth_client.get(ACTIVITY_LOGS_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data) if hasattr(response.data, 'get') else response.data
        assert len(results) == 1

    def test_unauthenticated_cannot_list_activity(self, api_client):
        response = api_client.get(ACTIVITY_LOGS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
