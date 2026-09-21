"""
AngelaMos | 2026
conftest.py

Shared pytest fixtures for the backend test suite

Provides two fixtures: tmp_db_path supplies a temp SQLite path for
test isolation, and test_settings builds a Settings instance pointed
at that path with a known encryption key configuration.
"""

from pathlib import Path

import pytest

from app.config import Settings


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """
    Provide a temporary database path for test isolation
    """
    return tmp_path / "test_c2.db"


@pytest.fixture
def test_settings(tmp_db_path: Path) -> Settings:
    """
    Settings override pointing to a temporary database and test encryption keys
    """
    return Settings(
        DATABASE_PATH=tmp_db_path,
        XOR_KEY="test-xor-key-12345",
        AES_GCM_KEY="0000000000000000000000000000000000000000000000000000000000000000",
        AUTH_KEY="c2-operator-default-secret-auth-key",
        ENVIRONMENT="development",
        DEBUG=True,
    )