"""Pytest configuration and fixtures for API tests."""
import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


# Store the original activities state
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture
def client():
    """Provide a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities dict to its original state before each test."""
    # Arrange: Clear and restore state
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield
    # Cleanup after test
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
