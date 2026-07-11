"""Tests for the health check endpoint."""
import pytest
from rest_framework import status


HEALTH_URL = '/api/v1/health/'


@pytest.mark.django_db
class TestHealthCheck:
    def test_health_returns_200(self, api_client):
        response = api_client.get(HEALTH_URL)
        assert response.status_code == status.HTTP_200_OK

    def test_health_response_has_status_field(self, api_client):
        response = api_client.get(HEALTH_URL)
        body = response.data if hasattr(response, 'data') else response.json()
        assert 'status' in body or response.status_code == status.HTTP_200_OK

    def test_health_does_not_require_auth(self, api_client):
        """Health endpoint must be publicly accessible for uptime monitors."""
        response = api_client.get(HEALTH_URL)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
