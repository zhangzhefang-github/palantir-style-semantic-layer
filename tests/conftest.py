"""
Pytest configuration and shared fixtures for semantic layer tests.
"""

import pytest
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_db_path():
    """Create a temporary database for testing."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    db_path = str(Path(temp_dir) / "test_semantic_layer.db")

    # Create schema
    with open(Path(__file__).parent.parent / 'schema.sql', 'r') as f:
        schema_sql = f.read()

    with open(Path(__file__).parent.parent / 'seed_data.sql', 'r') as f:
        seed_sql = f.read()

    # Initialize database
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.executescript(seed_sql)
    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_context():
    """Create a test execution context."""
    from semantic_layer.models import ExecutionContext

    return ExecutionContext(
        user_id=1,
        role='operator',
        parameters={},
        timestamp=datetime.now()
    )


@pytest.fixture
def admin_context():
    """Create an admin execution context."""
    from semantic_layer.models import ExecutionContext

    return ExecutionContext(
        user_id=999,
        role='admin',
        parameters={},
        timestamp=datetime.now()
    )


@pytest.fixture
def anonymous_context():
    """Create an anonymous execution context."""
    from semantic_layer.models import ExecutionContext

    return ExecutionContext(
        user_id=0,
        role='anonymous',
        parameters={},
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_parameters():
    """Sample query parameters."""
    return {
        'line': 'A',
        'start_date': '2026-01-27',
        'end_date': '2026-01-27'
    }


@pytest.fixture
def today_parameters():
    """Sample query parameters for today."""
    return {
        'line': 'B',
        'start_date': '2026-01-28',
        'end_date': '2026-01-28'
    }
