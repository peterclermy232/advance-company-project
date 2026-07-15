"""Shared pytest fixtures and factories for all apps."""
import pytest
import factory
from factory.django import DjangoModelFactory
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------

class UserFactory(DjangoModelFactory):
    class Meta:
        model = 'accounts.User'

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    full_name = factory.Faker('name')
    phone_number = factory.Sequence(lambda n: f'+25471{n:07d}')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')
    is_active = True
    email_verified = True


class AdminUserFactory(UserFactory):
    email = factory.Sequence(lambda n: f'admin{n}@example.com')
    role = 'admin'
    is_staff = True
    is_superuser = True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return AdminUserFactory()


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def sample_pdf():
    return SimpleUploadedFile(
        name='test_document.pdf',
        content=b'%PDF-1.4 fake pdf content',
        content_type='application/pdf',
    )


@pytest.fixture
def sample_image():
    return SimpleUploadedFile(
        name='test_photo.jpg',
        content=b'\xff\xd8\xff\xe0' + b'\x00' * 100,
        content_type='image/jpeg',
    )


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """
    DRF's AnonRateThrottle classes (RegisterRateThrottle, LoginRateThrottle,
    etc.) key by client IP, and Django's test client always uses the same
    fake IP — so without this, throttle counters accumulate in the cache
    across every test in the session and eventually trip later tests that
    hit the same endpoint, regardless of what they're actually testing.
    """
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def mock_supabase_storage(mocker):
    """Prevent any real Supabase calls during tests."""
    mocker.patch(
        'apps.documents.storage.SupabaseStorage._save',
        side_effect=lambda name, content: f'test/{name}',
    )
    mocker.patch(
        'apps.documents.storage.SupabaseStorage.url',
        return_value='https://example.supabase.co/storage/test/file.pdf',
    )
    mocker.patch(
        'apps.documents.storage.SupabaseStorage.exists',
        return_value=False,
    )
