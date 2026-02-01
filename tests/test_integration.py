"""
Integration tests for end-to-end semantic layer workflows.
"""

import pytest
from datetime import datetime
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext, AmbiguityError

SEED_YESTERDAY = '2026-01-27'
SEED_TODAY = '2026-01-28'


class TestSemanticOrchestratorIntegration:
    """Test end-to-end semantic query workflows."""

    def test_successful_query_fpy(self, test_db_path):
        """Test complete successful query for FPY."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        yesterday = SEED_YESTERDAY

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': yesterday,
                'end_date': yesterday
            },
            context=context
        )

        assert result['status'] == 'success'
        assert result['semantic_object'] == 'FPY'
        assert result['version'] == 'FPY_v1_standard'
        assert result['logic'] == 'good_qty / total_qty'
        assert result['row_count'] == 1
        assert 'audit_id' in result
        assert len(result['decision_trace']) > 0

        # Check FPY value
        fpy_value = result['data'][0]['fpy']
        assert fpy_value is not None
        assert 0 <= fpy_value <= 1

    def test_successful_query_outputqty(self, test_db_path):
        """Test complete successful query for OutputQty."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        today = SEED_TODAY

        result = orchestrator.query(
            question="今天产线B的产量是多少？",
            parameters={
                'line': 'B',
                'start_date': today,
                'end_date': today
            },
            context=context
        )

        assert result['status'] == 'success'
        assert result['semantic_object'] == 'OutputQty'
        assert result['logic'] == 'SUM(good_qty)'

        # Check output value
        output_qty = result['data'][0]['output_qty']
        assert output_qty is not None
        assert output_qty > 0

    def test_query_preview_mode(self, test_db_path):
        """Test query in preview mode (no execution)."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        result = orchestrator.query(
            question="产线A的一次合格率",
            parameters={
                'line': 'A',
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context,
            preview_only=True
        )

        assert result['status'] == 'preview'
        assert 'sql' in result
        assert 'fact_production_records' in result['sql']
        # No data in preview mode
        assert 'data' not in result or result.get('data') is None

    def test_query_policy_denied(self, test_db_path):
        """Test query with policy denial."""
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
        assert 'Access denied' in result['error'] or 'denied' in result['error'].lower()

    def test_query_ambiguous(self, test_db_path):
        """Test query with ambiguous semantic object."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        # Query with ambiguous term "指标" (metric)
        result = orchestrator.query(
            question="产线A的指标是多少？",
            parameters={},
            context=context
        )

        # Should return error (no matching semantic object)
        assert result['status'] == 'error'
        assert 'error' in result

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
            parameters={'line': 'A'},  # Missing dates
            context=context
        )

        # Should fail at SQL rendering stage
        assert result['status'] == 'error'
        assert 'error' in result

    def test_list_semantic_objects(self, test_db_path):
        """Test listing all semantic objects."""
        orchestrator = SemanticOrchestrator(test_db_path)

        objects = orchestrator.list_semantic_objects()

        assert len(objects) == 5  # FPY, OutputQty, DefectRate, QualityScore, GrossMargin
        assert any(obj['name'] == 'FPY' for obj in objects)
        assert any(obj['name'] == 'OutputQty' for obj in objects)
        assert any(obj['name'] == 'DefectRate' for obj in objects)

        # Check structure
        for obj in objects:
            assert 'id' in obj
            assert 'name' in obj
            assert 'description' in obj
            assert 'domain' in obj
            assert 'aliases' in obj

    def test_get_audit_history(self, test_db_path):
        """Test retrieving audit history."""
        orchestrator = SemanticOrchestrator(test_db_path)

        # Execute a query first
        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        yesterday = SEED_YESTERDAY

        orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': yesterday,
                'end_date': yesterday
            },
            context=context
        )

        # Get audit history
        history = orchestrator.get_audit_history(limit=10)

        assert len(history) > 0

        # Check structure
        for record in history:
            assert 'audit_id' in record
            assert 'question' in record
            assert 'semantic_object_name' in record
            assert 'status' in record
            assert 'executed_at' in record

    def test_get_audit_history_for_user(self, test_db_path):
        """Test retrieving audit history for specific user."""
        orchestrator = SemanticOrchestrator(test_db_path)

        history = orchestrator.get_audit_history(limit=10, user_id=1)

        # Should return history for user 1
        # May be empty if no queries by user 1 yet
        assert isinstance(history, list)

        for record in history:
            assert record['user_id'] == 1 or record['user_role'] == 'operator'

    def test_decision_trace_completeness(self, test_db_path):
        """Test that decision trace captures all steps."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        yesterday = SEED_YESTERDAY

        result = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': yesterday,
                'end_date': yesterday
            },
            context=context
        )

        # Check decision trace has expected steps
        trace = result['decision_trace']
        step_names = [step['step'] for step in trace]

        # Should include these key steps
        assert 'resolve_semantic_object_start' in step_names
        assert 'resolve_semantic_object_complete' in step_names
        assert 'resolve_version_start' in step_names
        assert 'resolve_version_complete' in step_names
        assert 'resolve_logic_start' in step_names
        assert 'resolve_logic_complete' in step_names
        assert 'resolve_physical_mapping_start' in step_names
        assert 'resolve_physical_mapping_complete' in step_names
        assert 'policy_check_start' in step_names
        assert 'policy_check_complete' in step_names
        assert 'render_sql_start' in step_names
        assert 'render_sql_complete' in step_names
        assert 'execution_start' in step_names
        assert 'execution_complete' in step_names

    def test_sql_generation_correctness(self, test_db_path):
        """Test that generated SQL is correct."""
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
                'start_date': '2026-01-27',
                'end_date': '2026-01-27'
            },
            context=context
        )

        sql = result['sql']

        # Check SQL structure
        assert 'SELECT' in sql
        assert 'good_qty' in sql
        assert 'total_qty' in sql
        assert 'fact_production_records' in sql
        assert ':line' in sql
        assert ':start_date' in sql
        assert ':end_date' in sql

    def test_multiple_queries_same_session(self, test_db_path):
        """Test executing multiple queries in same session."""
        orchestrator = SemanticOrchestrator(test_db_path)

        context = ExecutionContext(
            user_id=1,
            role='operator',
            parameters={},
            timestamp=datetime.now()
        )

        yesterday = SEED_YESTERDAY

        # Query 1: FPY
        result1 = orchestrator.query(
            question="昨天产线A的一次合格率是多少？",
            parameters={
                'line': 'A',
                'start_date': yesterday,
                'end_date': yesterday
            },
            context=context
        )

        assert result1['status'] == 'success'
        audit_id_1 = result1['audit_id']

        # Query 2: OutputQty
        result2 = orchestrator.query(
            question="昨天产线B的产量是多少？",
            parameters={
                'line': 'B',
                'start_date': yesterday,
                'end_date': yesterday
            },
            context=context
        )

        assert result2['status'] == 'success'
        audit_id_2 = result2['audit_id']

        # Audit IDs should be different
        assert audit_id_1 != audit_id_2

        # Check audit history
        history = orchestrator.get_audit_history(limit=5)
        assert len(history) >= 2
