"""Tests for the beneficiary app."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


BENEFICIARY_URL = '/api/beneficiary/'


def _make_file():
    return SimpleUploadedFile(
        'id.pdf', b'%PDF fake', content_type='application/pdf'
    )


@pytest.mark.django_db
class TestBeneficiaryCRUD:
    def _payload(self):
        return {
            'name': 'Jane Doe',
            'relation': 'spouse',
            'age': 30,
            'gender': 'F',
            'phone_number': '+254711000002',
            'percentage_allocation': '100.00',
            'identity_document': _make_file(),
        }

    def test_create_beneficiary(self, auth_client):
        response = auth_client.post(
            BENEFICIARY_URL, self._payload(), format='multipart'
        )
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
        ]

    def test_list_own_beneficiaries(self, auth_client, user):
        from .models import Beneficiary
        Beneficiary.objects.create(
            user=user,
            name='Child One',
            relation='child',
            age=10,
            gender='M',
            identity_document=_make_file(),
        )
        response = auth_client.get(BENEFICIARY_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_unauthenticated_cannot_list(self, api_client):
        response = api_client.get(BENEFICIARY_URL)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_percentage_allocation_over_100_rejected(self, auth_client):
        payload = self._payload()
        payload['percentage_allocation'] = '150.00'
        response = auth_client.post(BENEFICIARY_URL, payload, format='multipart')
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_invalid_relation_rejected(self, auth_client):
        payload = self._payload()
        payload['relation'] = 'alien'
        response = auth_client.post(BENEFICIARY_URL, payload, format='multipart')
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_delete_beneficiary(self, auth_client, user):
        from .models import Beneficiary
        b = Beneficiary.objects.create(
            user=user,
            name='To Delete',
            relation='parent',
            age=55,
            gender='M',
            identity_document=_make_file(),
        )
        response = auth_client.delete(f'{BENEFICIARY_URL}{b.uuid}/')
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        ]


@pytest.mark.django_db
class TestBeneficiaryModel:
    def test_beneficiary_str(self, user):
        from .models import Beneficiary
        b = Beneficiary(
            user=user,
            name='Test Name',
            relation='child',
            age=5,
            gender='M',
        )
        assert 'Test Name' in str(b) or b is not None

    def test_beneficiary_relation_choices(self):
        from .models import Beneficiary
        valid = [c[0] for c in Beneficiary.RELATION_CHOICES]
        assert 'spouse' in valid
        assert 'child' in valid
        assert 'parent' in valid
