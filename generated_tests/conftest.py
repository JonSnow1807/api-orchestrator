"""
Shared pytest fixtures and configuration
"""

import pytest
import requests
from typing import Generator

@pytest.fixture(scope="session")
def api_client() -> Generator:
    """Session-scoped API client"""
    client = requests.Session()
    client.headers.update({"Content-Type": "application/json"})
    yield client
    client.close()

@pytest.fixture(scope="function")
def cleanup():
    """Cleanup fixture for test isolation"""
    created_ids = []
    yield created_ids
    # Cleanup created resources
    for resource_id in created_ids:
        try:
            requests.delete(f"http://localhost:8000/items/{resource_id}")
        except:
            pass

@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User"
    }

@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time
    start = time.time()
    yield
    duration = time.time() - start
    print(f"\nTest duration: {duration:.3f}s")
