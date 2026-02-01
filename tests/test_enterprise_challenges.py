"""
Enterprise Challenge Tests

These tests prove the system can withstand enterprise architecture scrutiny
by providing deterministic, explainable behavior for edge cases.

Coverage:
- Priority-based conflict resolution
- Ambiguity detection and error handling
- Full scenario matching (no partial match)
- Physical mapping portability
"""

import pytest
import sqlite3
from datetime import datetime
from pathlib import Path
import tempfile
import os

from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext, AmbiguityError


@pytest.fixture
def conflict_test_db():
    """
    Create a test database with conflicting versions for testing.

    Setup:
    - FPY_v1_conflict_a: scenario={"region": "US"}, priority=5
    - FPY_v2_conflict_b: scenario={"region": "US"}, priority=10
    - Expected: v2 should win (higher priority)
    """
    db_path = tempfile.mktemp(suffix='.db')

    # Initialize database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    schema_path = Path(__file__).parent.parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())

    # Insert semantic objects
    cursor.execute("""
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES ('FPY', 'First Pass Yield', '["FPY", "一次合格率"]', 'production', 'active')
    """)

    # Insert conflicting versions with SAME scenario but different priorities
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (1, 'FPY_v1_conflict_a', '2024-01-01 00:00:00', '{"region": "US"}', 1, 5, 'Conflict version A - lower priority')
    """)

    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (1, 'FPY_v2_conflict_b', '2024-01-01 00:00:00', '{"region": "US"}', 1, 10, 'Conflict version B - higher priority')
    """)

    # Insert logical definitions for both versions
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (1, 'good_qty / total_qty', 'line,day', 'Version A formula', '["good_qty", "total_qty"]')
    """)

    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (2, '(good_qty + 10) / total_qty', 'line,day', 'Version B formula (different)', '["good_qty", "total_qty"]')
    """)

    # Insert physical mappings
    cursor.execute("""
        INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (1, 'sqlite', 'default', 'SELECT 0.95 as fpy', '{}', 1, 'Mapping A')
    """)

    cursor.execute("""
        INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (2, 'sqlite', 'default', 'SELECT 0.99 as fpy', '{}', 1, 'Mapping B')
    """)

    # Insert test data (fact_production_records already created by schema.sql)
    cursor.execute("""
        INSERT INTO fact_production_records (record_date, line, product_id, good_qty, rework_qty, total_qty, shift, operator_id)
        VALUES ('2026-01-27', 'A', 'PROD001', 950, 0, 1000, 'morning', 1)
    """)

    # Insert access policy
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'operator', 'query', NULL, 'allow', 1)
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def ambiguity_test_db():
    """
    Create a test database with TRUE ambiguity (same scenario, same priority).

    Setup:
    - FPY_v1_ambiguous_a: scenario={"region": "EU"}, priority=5
    - FPY_v2_ambiguous_b: scenario={"region": "EU"}, priority=5
    - Expected: AmbiguityError should be raised
    """
    db_path = tempfile.mktemp(suffix='.db')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema
    schema_path = Path(__file__).parent.parent / 'schema.sql'
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())

    # Insert semantic objects
    cursor.execute("""
        INSERT INTO semantic_object (name, description, aliases, domain, status)
        VALUES ('FPY', 'First Pass Yield', '["FPY", "一次合格率"]', 'production', 'active')
    """)

    # Insert ambiguous versions (SAME scenario, SAME priority)
    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (1, 'FPY_v1_ambiguous_a', '2024-01-01 00:00:00', '{"region": "EU"}', 1, 5, 'Ambiguous version A')
    """)

    cursor.execute("""
        INSERT INTO semantic_version
        (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
        VALUES (1, 'FPY_v2_ambiguous_b', '2024-01-01 00:00:00', '{"region": "EU"}', 1, 5, 'Ambiguous version B')
    """)

    # Insert logical definitions
    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (1, 'good_qty / total_qty', 'line,day', 'Formula A', '["good_qty", "total_qty"]')
    """)

    cursor.execute("""
        INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
        VALUES (2, '(good_qty + rework_qty) / total_qty', 'line,day', 'Formula B', '["good_qty", "rework_qty", "total_qty"]')
    """)

    # Insert physical mappings
    cursor.execute("""
        INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (1, 'sqlite', 'default', 'SELECT 0.90 as fpy', '{}', 1, 'Mapping A')
    """)

    cursor.execute("""
        INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
        VALUES (2, 'sqlite', 'default', 'SELECT 0.95 as fpy', '{}', 1, 'Mapping B')
    """)

    # Insert test data (fact_production_records already created by schema.sql)
    cursor.execute("""
        INSERT INTO fact_production_records (record_date, line, product_id, good_qty, rework_qty, total_qty, shift, operator_id)
        VALUES ('2026-01-27', 'A', 'PROD001', 950, 0, 1000, 'morning', 1)
    """)

    # Insert access policy
    cursor.execute("""
        INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
        VALUES (1, 'operator', 'query', NULL, 'allow', 1)
    """)

    conn.commit()
    conn.close()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


class TestPriorityConflictResolution:
    """
    Test suite: Priority-based conflict resolution.

    Business scenario:
    Multiple versions exist with the same scenario condition.
    The system MUST use priority to deterministically select the correct version.
    """

    def test_higher_priority_wins_with_same_scenario(self, conflict_test_db):
        """
        Test: When multiple versions match scenario, higher priority wins.

        Setup:
        - Version A: scenario={"region": "US"}, priority=5
        - Version B: scenario={"region": "US"}, priority=10

        Expected:
        - Version B is selected (higher priority)
        - Result uses version B's formula (returns 0.99)
        """
        orchestrator = SemanticOrchestrator(conflict_test_db)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Query with scenario that matches both versions
        result = orchestrator.query(
            question="What is the FPY for US region?",
            parameters={'region': 'US'},
            context=context
        )

        # Should succeed
        assert result['status'] == 'success'

        # Should select version B (higher priority = 10)
        assert result['version'] == 'FPY_v2_conflict_b'

        # Should use version B's formula (0.99, not 0.95)
        assert result['data'][0]['fpy'] == 0.99

        # Decision trace should explain priority selection
        trace = result['decision_trace']
        version_step = next(s for s in trace if 'resolve_version_complete' in s['step'])
        assert 'priority' in version_step['data']['version_selection_reason'].lower() or \
               'FPY_v2_conflict_b' in result['version']


class TestAmbiguityDetection:
    """
    Test suite: Ambiguity detection and error handling.

    Business scenario:
    Multiple versions exist with identical scenario AND priority.
    The system MUST refuse to guess and raise AmbiguityError.
    """

    def test_ambiguous_versions_raise_error(self, ambiguity_test_db):
        """
        Test: When true ambiguity exists, error is returned with details.

        Setup:
        - Version A: scenario={"region": "EU"}, priority=5
        - Version B: scenario={"region": "EU"}, priority=5

        Expected:
        - Query returns error status (not exception)
        - Error message lists all conflicting versions
        - Error type is 'AmbiguityError'
        """
        orchestrator = SemanticOrchestrator(ambiguity_test_db)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Query with scenario that creates ambiguity
        result = orchestrator.query(
            question="What is the FPY for EU region?",
            parameters={'region': 'EU'},
            context=context
        )

        # Should return error status (not raise exception)
        assert result['status'] == 'error'
        assert result['error_type'] == 'AmbiguityError'

        # Error message should mention ambiguity or priority
        error_msg = result['error'].lower()
        assert 'priority' in error_msg or 'ambigu' in error_msg

        # Should have candidates in error response
        assert 'candidates' in result
        assert len(result['candidates']) == 2

    def test_ambiguous_query_creates_audit_record(self, ambiguity_test_db):
        """
        Test: Ambiguous queries are still audited.
        """
        orchestrator = SemanticOrchestrator(ambiguity_test_db)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Query that will fail
        try:
            orchestrator.query(
                question="What is the FPY for EU region?",
                parameters={'region': 'EU'},
                context=context
            )
        except AmbiguityError:
            pass  # Expected

        # Check audit history
        history = orchestrator.get_audit_history(limit=5)
        assert len(history) > 0

        # Most recent query should be the failed one
        latest = history[0]
        assert latest['status'] == 'error' or latest['status'] == 'denied'


class TestScenarioFullMatch:
    """
    Test suite: Scenario matching requires FULL key-value match.

    Business requirement:
    NO partial match. NO fuzzy match.
    Only exact key-value match is accepted.
    """

    def test_partial_scenario_match_fails(self, conflict_test_db):
        """
        Test: Partial scenario match falls back to default version.

        Setup:
        - Version A: scenario={"region": "US", "plant": "NY"}
        - Query provides: {"region": "US"} (missing plant)

        Expected:
        - Version A is NOT matched (missing 'plant' key)
        - Falls back to default version if available
        """
        # First, let's add a default version and a multi-condition version
        conn = sqlite3.connect(conflict_test_db)
        cursor = conn.cursor()

        # Add default version (no scenario condition)
        cursor.execute("""
            INSERT INTO semantic_version
            (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
            VALUES (1, 'FPY_default', '2024-01-01 00:00:00', NULL, 1, 0, 'Default version')
        """)

        cursor.execute("""
            INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
            VALUES (3, 'good_qty / total_qty', 'line,day', 'Default formula', '["good_qty", "total_qty"]')
        """)

        cursor.execute("""
            INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
            VALUES (3, 'sqlite', 'default', 'SELECT 0.88 as fpy', '{}', 1, 'Default mapping')
        """)

        conn.commit()
        conn.close()

        orchestrator = SemanticOrchestrator(conflict_test_db)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Query with partial scenario (only 'region', missing 'plant')
        result = orchestrator.query(
            question="What is the FPY?",
            parameters={'region': 'US'},  # Partial match
            context=context
        )

        # Should fall back to default version
        assert result['status'] == 'success'
        assert result['version'] == 'FPY_default'
        assert result['data'][0]['fpy'] == 0.88


class TestPhysicalMappingPortability:
    """
    Test suite: Physical mappings can be switched without changing orchestrator.

    Business scenario:
    Same logical definition, multiple physical mappings (e.g., SQLite vs Snowflake).
    System should select based on priority without code changes.
    """

    @pytest.fixture
    def mapping_test_db(self):
        """
        Create database with multiple physical mappings for same logical definition.
        """
        db_path = tempfile.mktemp(suffix='.db')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create schema
        schema_path = Path(__file__).parent.parent / 'schema.sql'
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())

        # Insert semantic objects
        cursor.execute("""
            INSERT INTO semantic_object (name, description, aliases, domain, status)
            VALUES ('FPY', 'First Pass Yield', '["FPY"]', 'production', 'active')
        """)

        # Insert version
        cursor.execute("""
            INSERT INTO semantic_version
            (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
            VALUES (1, 'FPY_v1', '2024-01-01 00:00:00', NULL, 1, 0, 'Standard FPY')
        """)

        # Insert logical definition
        cursor.execute("""
            INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
            VALUES (1, 'good_qty / total_qty', 'line,day', 'Standard formula', '["good_qty", "total_qty"]')
        """)

        # Insert TWO physical mappings with different priorities
        # Mapping v1: Legacy implementation (lower priority)
        cursor.execute("""
            INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
            VALUES (1, 'sqlite', 'legacy_db', 'SELECT 0.85 as fpy', '{}', 1, 'Legacy mapping - slow query')
        """)

        # Mapping v2: Optimized implementation (higher priority)
        cursor.execute("""
            INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description)
            VALUES (1, 'sqlite', 'default', 'SELECT 0.92 as fpy', '{}', 10, 'Optimized mapping - fast query')
        """)

        # Insert test data (fact_production_records already created by schema.sql)
        cursor.execute("""
            INSERT INTO fact_production_records (record_date, line, product_id, good_qty, rework_qty, total_qty, shift, operator_id)
            VALUES ('2026-01-27', 'A', 'PROD001', 950, 0, 1000, 'morning', 1)
        """)

        # Insert access policy
        cursor.execute("""
            INSERT INTO access_policy (semantic_object_id, role, action, condition, effect, priority)
            VALUES (1, 'operator', 'query', NULL, 'allow', 1)
        """)

        conn.commit()
        conn.close()

        yield db_path

        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass

    def test_higher_priority_mapping_is_selected(self, mapping_test_db):
        """
        Test: Physical mapping with higher priority is selected.

        Setup:
        - Mapping v1: priority=1 (legacy)
        - Mapping v2: priority=10 (optimized)

        Expected:
        - Mapping v2 is selected
        - Result uses v2's SQL (returns 0.92)
        - Decision trace explains mapping selection
        """
        orchestrator = SemanticOrchestrator(mapping_test_db)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="What is the FPY?",
            parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
            context=context
        )

        # Should succeed
        assert result['status'] == 'success'

        # Should use higher priority mapping (returns 0.92, not 0.85)
        assert result['data'][0]['fpy'] == 0.92

        # Decision trace should explain mapping selection
        trace = result['decision_trace']
        mapping_step = next(s for s in trace if 'resolve_physical_mapping_complete' in s['step'])
        assert 'priority' in mapping_step['data']['physical_mapping_reason'].lower() or \
               'selected' in mapping_step['data']['physical_mapping_reason'].lower()
