import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from tests.factories import UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client_factory():
    def _make_client(user: User) -> APIClient:
        client = APIClient()
        refresh = RefreshToken.for_user(user)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        return client

    return _make_client


@pytest.fixture
def admin_user(db):
    return UserFactory(email="admin@helpdesk.local", role=User.Role.ADMIN, is_staff=True)


@pytest.fixture
def manager_user(db):
    return UserFactory(email="manager@helpdesk.local", role=User.Role.MANAGER)


@pytest.fixture
def engineer_user(db):
    return UserFactory(email="engineer@helpdesk.local", role=User.Role.ENGINEER)


@pytest.fixture
def employee_user(db):
    return UserFactory(email="employee@helpdesk.local", role=User.Role.EMPLOYEE)
