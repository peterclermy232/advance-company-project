"""Tests for the analytics app — admin member/contribution analytics."""
import pytest
from decimal import Decimal
from rest_framework import status

from apps.financial.models import Deposit, FinancialAccount


ANALYTICS_MEMBERS_URL = '/api/admin/analytics/members/'
ANALYTICS_SUMMARY_URL = '/api/admin/analytics/summary/'
ANALYTICS_EXPORT_URL = '/api/admin/analytics/export/'


def _make_completed_deposit(user, amount, ref):
    return Deposit.objects.create(
        user=user, amount=amount, payment_method='mpesa',
        status='completed', transaction_reference=ref,
    )


@pytest.mark.django_db
class TestAdminAnalyticsMembers:
    def test_admin_can_view_member_analytics(self, admin_client, user):
        FinancialAccount.objects.get_or_create(user=user, defaults={'total_contributions': Decimal('20000.00')})
        _make_completed_deposit(user, 20000, 'ANALYTICS-REF-001')

        response = admin_client.get(ANALYTICS_MEMBERS_URL)
        assert response.status_code == status.HTTP_200_OK
        assert 'members' in response.data
        assert 'summary' in response.data
        assert 'monthly_trends' in response.data

    def test_completed_deposits_are_counted(self, admin_client, user):
        # Regression test: analytics used to filter deposits by a
        # non-existent status="APPROVED" instead of the real 'completed'
        # value, so this always reported zero deposits regardless of data.
        account, _ = FinancialAccount.objects.get_or_create(user=user)
        account.total_contributions = Decimal('20000.00')
        account.save()
        _make_completed_deposit(user, 20000, 'ANALYTICS-REF-002')

        response = admin_client.get(ANALYTICS_MEMBERS_URL)
        member = next(m for m in response.data['members'] if m['id'] == str(user.uuid))
        assert member['total_deposits'] == 1

    def test_pending_deposits_are_not_counted(self, admin_client, user):
        Deposit.objects.create(
            user=user, amount=20000, payment_method='mpesa',
            status='pending', transaction_reference='ANALYTICS-REF-003',
        )
        response = admin_client.get(ANALYTICS_MEMBERS_URL)
        member = next(m for m in response.data['members'] if m['id'] == str(user.uuid))
        assert member['total_deposits'] == 0

    def test_regular_user_cannot_view_member_analytics(self, auth_client):
        response = auth_client.get(ANALYTICS_MEMBERS_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_cannot_view_member_analytics(self, api_client):
        response = api_client.get(ANALYTICS_MEMBERS_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAdminAnalyticsSummary:
    def test_admin_can_view_summary(self, admin_client, user):
        _make_completed_deposit(user, 20000, 'ANALYTICS-REF-004')
        response = admin_client.get(ANALYTICS_SUMMARY_URL)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_deposits_count'] == 1

    def test_regular_user_cannot_view_summary(self, auth_client):
        response = auth_client.get(ANALYTICS_SUMMARY_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAdminAnalyticsExport:
    def test_export_requires_admin(self, auth_client):
        response = auth_client.get(ANALYTICS_EXPORT_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_export_excel_returns_xlsx(self, admin_client, user):
        response = admin_client.get(ANALYTICS_EXPORT_URL, {'export_format': 'excel'})
        assert response.status_code == status.HTTP_200_OK
        assert 'spreadsheetml' in response['Content-Type']

    def test_export_invalid_format_rejected(self, admin_client):
        response = admin_client.get(ANALYTICS_EXPORT_URL, {'export_format': 'csv'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
