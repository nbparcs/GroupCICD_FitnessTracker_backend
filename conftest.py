import os
import django
import pytest


def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FitnessTrackerApp_backend.settings')
    django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Give all tests access to the database."""
    pass
