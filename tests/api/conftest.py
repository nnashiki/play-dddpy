"""Configuration for API tests."""

import pytest
import os
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="function")
def test_client():
    """Create test client with a clean database for each test."""
    from dddpy.infrastructure.sqlite.database import reset_database
    
    # Ensure db directory exists
    os.makedirs("./db", exist_ok=True)
    
    # Reset database by dropping and recreating tables (safer than file deletion)
    reset_database()
    
    # Return test client
    return TestClient(app)
