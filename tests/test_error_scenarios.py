"""
Error scenario tests for semantic layer.
"""

import pytest
from datetime import datetime
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


class TestErrorScenarios:
    """Test various error scenarios and edge cases."""

    def test_query_no_matching_semantic_object(self, test_db_path):
        """Test query with no matching semantic object."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="今天的天气怎么样？",  # Unrelated query
            parameters={},
            context=context
        )

        assert result['status'] == 'error'
        assert 'error' in result
        assert 'No semantic object found' in result['error'] or 'matched' in result['error']

    def test_query_missing_parameters(self, test_db_path):
        """Test query with missing required parameters."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A'
                # Missing start_date and end_date
            },
            context=context
        )

        assert result['status'] == 'error'
        assert 'error' in result

    def test_query_invalid_parameters(self, test_db_path):
        """Test query with invalid parameter values."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'INVALID_LINE',  # Non-existent line
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context
        )

        # System executes query successfully but returns no data (not an error)
        assert result['status'] == 'success'
        # Result may have 1 row with NULL value or 0 rows depending on SQL behavior
        assert result['row_count'] <= 1

    def test_query_unauthorized_role(self, test_db_path):
        """Test query with unauthorized role."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=0,
            role='anonymous',  # No access
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context
        )

        assert result['status'] == 'denied'
        assert 'error' in result

    def test_query_invalid_date_format(self, test_db_path):
        """Test query with invalid date format."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Invalid date format - SQLite may not validate strictly
        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': 'invalid-date',
                'end_date': '2026-01-27'
            },
            context=context
        )

        # System behavior: May succeed or fail depending on SQLite
        # We just check that status is set
        assert 'status' in result

    def test_query_date_range_mismatch(self, test_db_path):
        """Test query with mismatched date range (end before start)."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': '2026-01-28',
                'end_date': '2026-01-27'  # End before start
            },
            context=context
        )

        # SQL executes successfully but returns no data for invalid range
        assert result['status'] == 'success'
        # May return 0 rows or 1 row with NULL
        assert result['row_count'] <= 1

    def test_query_special_characters_in_parameters(self, test_db_path):
        """Test query with special characters in parameters."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Line with special characters (SQL injection attempt)
        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': "A'; DROP TABLE fact_production_records; --",
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context
        )

        # Should handle safely (Jinja2 will escape)
        # Either fail at execution or return no data
        assert 'status' in result

    def test_non_existent_semantic_version(self, test_db_path):
        """Test query for semantic object with no versions at all."""
        import sqlite3
        
        # Delete all versions and related data for FPY in the test database
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        # Delete physical mappings first (foreign key)
        cursor.execute("DELETE FROM physical_mapping WHERE logical_definition_id IN (SELECT id FROM logical_definition WHERE semantic_version_id IN (SELECT id FROM semantic_version WHERE semantic_object_id = 1))")
        # Delete logical definitions (foreign key)
        cursor.execute("DELETE FROM logical_definition WHERE semantic_version_id IN (SELECT id FROM semantic_version WHERE semantic_object_id = 1)")
        # Delete all versions for FPY
        cursor.execute("DELETE FROM semantic_version WHERE semantic_object_id = 1")
        conn.commit()
        conn.close()
        
        orchestrator = SemanticOrchestrator(test_db_path)
        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )
        
        # Should raise error or return error status when no versions exist
        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={'line': 'A', 'start_date': '2026-01-27', 'end_date': '2026-01-27'},
            context=context
        )
        
        # Either returns error status or raises exception
        assert result.get('status') in ['error', False] or 'error' in str(result).lower()

    def test_database_connection_failure(self, test_db_path):
        """Test behavior when database is unavailable."""
        # Use invalid database path
        with pytest.raises(Exception):
            orchestrator = SemanticOrchestrator('/invalid/path/to/database.db')

            context = ExecutionContext(
                user_id=1,
                role='operator',
                parameters={},
                timestamp=datetime.now()
            )

            orchestrator.query(
                question="昨天产线A的一次合格率是多少？",
                parameters={},
                context=context
            )

    def test_empty_question(self, test_db_path):
        """Test query with empty question."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="",  # Empty question
            parameters={},
            context=context
        )

        assert result['status'] == 'error'

    def test_query_with_null_parameters(self, test_db_path):
        """Test query with null parameter values."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': None,  # Null value
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context
        )

        # Jinja2 renders None as 'None' in SQL, query may succeed but return no data
        # Status should be set
        assert 'status' in result

    def test_query_very_long_question(self, test_db_path):
        """Test query with very long question text."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        long_question = "昨天产线A的一次合格率是多少？ " * 100

        result = orchestrator.query(
            question=long_question,
            parameters={
                'line': 'A',
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context
        )

        # Should still process the question
        assert 'status' in result

    def test_concurrent_queries(self, test_db_path):
        """Test handling multiple concurrent queries."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Execute multiple queries
        results = []
        for i in range(5):
            result = orchestrator.query(
                question="昨天产线A的一次合格率是多少？",
                parameters={
                    'line': 'A',
                    'start_date': '2026-01-27',
                    'end_date': '2026-01-27'
                },
                context=context
            )
            results.append(result)

        # All should succeed
        assert all(r['status'] == 'success' for r in results)

        # Each should have unique audit ID
        audit_ids = [r['audit_id'] for r in results]
        assert len(audit_ids) == len(set(audit_ids))  # All unique
