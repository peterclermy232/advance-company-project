"""Tests for the financial app — deposits, withdrawals, financial accounts."""
import pytest
from decimal import Decimal
from unittest.mock import patch
from django.urls import reverse
from rest_framework import status

from .models import Deposit, FinancialAccount


DEPOSIT_LIST_URL = '/api/financial/deposits/'


def deposit_approve_url(pk):
    return f'/api/financial/deposits/{pk}/approve_deposit/'


# ---------------------------------------------------------------------------
# Deposit creation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDepositCreation:
    def _payload(self, **overrides):
        data = {
            'amount': 20000,
            'payment_method': 'mpesa',
            'mpesa_phone': '+254712345678',
        }
        data.update(overrides)
        return data

    def test_create_deposit_success(self, auth_client, user):
        response = auth_client.post(DEPOSIT_LIST_URL, self._payload())
        assert response.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.filter(user=user).count() == 1

    def test_deposit_belongs_to_authenticated_user(self, auth_client, user):
        auth_client.post(DEPOSIT_LIST_URL, self._payload())
        deposit = Deposit.objects.get(user=user)
        assert deposit.user == user

    def test_deposit_initial_status_is_processing_for_mpesa(self, auth_client, user):
        # M-Pesa deposits go straight to 'processing' since creation immediately
        # triggers an STK push; only non-M-Pesa methods start as 'pending'.
        auth_client.post(DEPOSIT_LIST_URL, self._payload())
        deposit = Deposit.objects.get(user=user)
        assert deposit.status == 'processing'

    def test_deposit_amount_is_fixed_monthly_amount(self, auth_client, user):
        # DepositViewSet.create() ignores any client-supplied amount and
        # always charges the fixed MONTHLY_DEPOSIT_AMOUNT.
        auth_client.post(DEPOSIT_LIST_URL, self._payload(amount=50000))
        deposit = Deposit.objects.get(user=user)
        assert deposit.amount == Decimal('20000.00')

    def test_cannot_create_duplicate_deposit_same_month(self, auth_client, user):
        Deposit.objects.create(
            user=user,
            amount=20000,
            payment_method='mpesa',
            status='completed',
            transaction_reference='REF001',
        )
        response = auth_client.post(DEPOSIT_LIST_URL, self._payload())
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthenticated_cannot_create_deposit(self, api_client):
        response = api_client.post(DEPOSIT_LIST_URL, self._payload())
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_deposit_missing_mpesa_phone_rejected(self, auth_client):
        # amount isn't client-controlled (see test above), but mpesa_phone is
        # required whenever payment_method='mpesa'.
        payload = self._payload()
        del payload['mpesa_phone']
        response = auth_client.post(DEPOSIT_LIST_URL, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Deposit approval (admin action)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDepositApproval:
    def test_admin_can_approve_deposit(self, admin_client, user):
        deposit = Deposit.objects.create(
            user=user,
            amount=20000,
            payment_method='mpesa',
            status='pending',
            transaction_reference='REF002',
        )
        response = admin_client.post(deposit_approve_url(deposit.uuid))
        assert response.status_code == status.HTTP_200_OK

        deposit.refresh_from_db()
        assert deposit.status == 'completed'

    def test_approved_deposit_updates_financial_account(self, admin_client, user):
        deposit = Deposit.objects.create(
            user=user,
            amount=20000,
            payment_method='mpesa',
            status='pending',
            transaction_reference='REF003',
        )
        admin_client.post(deposit_approve_url(deposit.uuid))

        account = FinancialAccount.objects.get(user=user)
        assert account.total_contributions == Decimal('20000.00')

    def test_approval_records_approver(self, admin_client, admin_user, user):
        deposit = Deposit.objects.create(
            user=user,
            amount=20000,
            payment_method='mpesa',
            status='pending',
            transaction_reference='REF004',
        )
        admin_client.post(deposit_approve_url(deposit.uuid))

        deposit.refresh_from_db()
        assert deposit.approved_by == admin_user

    def test_regular_user_cannot_approve_deposit(self, auth_client, user):
        deposit = Deposit.objects.create(
            user=user,
            amount=20000,
            payment_method='mpesa',
            status='pending',
            transaction_reference='REF005',
        )
        response = auth_client.post(deposit_approve_url(deposit.uuid))
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ]


# ---------------------------------------------------------------------------
# Financial account
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestFinancialAccount:
    def test_financial_account_created_for_user(self, user):
        account, created = FinancialAccount.objects.get_or_create(user=user)
        assert account.user == user

    def test_initial_contributions_zero(self, user):
        account, _ = FinancialAccount.objects.get_or_create(user=user)
        assert account.total_contributions == Decimal('0.00')

    def test_deposit_list_returns_only_own_deposits(self, auth_client, user, db):
        from conftest import UserFactory
        other_user = UserFactory()
        Deposit.objects.create(
            user=user, amount=10000, payment_method='mpesa',
            status='pending', transaction_reference='OWN001',
        )
        Deposit.objects.create(
            user=other_user, amount=10000, payment_method='mpesa',
            status='pending', transaction_reference='OTHER001',
        )
        response = auth_client.get(DEPOSIT_LIST_URL)
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('data', response.data) if hasattr(response.data, 'get') else response.data
        deposit_refs = [d.get('transaction_reference') for d in results]
        assert 'OTHER001' not in deposit_refs
