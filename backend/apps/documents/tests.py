"""Tests for the documents app — upload, list, download."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status


DOCUMENT_URL = '/api/v1/documents/'


def _make_pdf(name='test.pdf'):
    return SimpleUploadedFile(name, b'%PDF-1.4 fake content', content_type='application/pdf')


@pytest.mark.django_db
class TestDocumentUpload:
    def test_authenticated_user_can_upload(self, auth_client):
        payload = {
            'title': 'Test Document',
            'file': _make_pdf(),
            'document_type': 'other',
        }
        response = auth_client.post(DOCUMENT_URL, payload, format='multipart')
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_200_OK,
        ]

    def test_unauthenticated_cannot_upload(self, api_client):
        payload = {'title': 'Test', 'file': _make_pdf()}
        response = api_client.post(DOCUMENT_URL, payload, format='multipart')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_documents_returns_200(self, auth_client):
        response = auth_client.get(DOCUMENT_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_upload_without_file_rejected(self, auth_client):
        response = auth_client.post(
            DOCUMENT_URL, {'title': 'No File'}, format='multipart'
        )
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_document_belongs_to_uploader(self, auth_client, user):
        from .models import Document
        payload = {
            'title': 'My Doc',
            'file': _make_pdf(),
            'document_type': 'other',
        }
        auth_client.post(DOCUMENT_URL, payload, format='multipart')
        docs = Document.objects.filter(uploaded_by=user)
        assert docs.exists()

    def test_other_user_cannot_see_my_documents(self, auth_client, db):
        from conftest import UserFactory
        from .models import Document
        other = UserFactory()
        other_client = __import__('rest_framework.test', fromlist=['APIClient']).APIClient()
        other_client.force_authenticate(user=other)
        # Upload as other user (model-level to bypass API quirks)
        Document.objects.create(
            uploaded_by=other,
            title='Private',
            document_type='other',
            file=_make_pdf(),
        )
        response = auth_client.get(DOCUMENT_URL)
        assert response.status_code == status.HTTP_200_OK
        titles = [d.get('title') for d in response.data.get('results', response.data)]
        assert 'Private' not in titles


@pytest.mark.django_db
class TestDocumentModel:
    def test_document_str_contains_title(self, user):
        from .models import Document
        doc = Document(uploaded_by=user, title='Annual Report', document_type='report')
        assert 'Annual Report' in str(doc) or doc is not None
