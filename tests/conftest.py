import pytest

from app.repository import seed_repository


@pytest.fixture
def repo():
    return seed_repository()
