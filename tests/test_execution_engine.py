"""
Unit tests for ExecutionEngine.
"""

import pytest
from semantic_layer.execution_engine import ExecutionEngine, ExecutionResult
from semantic_layer.models import MappingNotFoundError


class TestExecutionEngine:
    """Test ExecutionEngine functionality."""

    def test_resolve_physical_mapping(self, test_db_path):
        """Test resolving physical mapping."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        mapping = engine.resolve_physical_mapping(
            logical_definition_id=1,
            engine_type='sqlite'
        )

        assert mapping.id == 1
        assert mapping.engine_type == 'sqlite'
        assert mapping.connection_ref == 'default'
        assert ':line' in mapping.sql_template
        assert mapping.priority == 1

    def test_resolve_physical_mapping_not_found(self, test_db_path):
        """Test resolving non-existent physical mapping."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        with pytest.raises(MappingNotFoundError):
            engine.resolve_physical_mapping(
                logical_definition_id=999,
                engine_type='sqlite'
            )

    def test_render_sql(self, test_db_path):
        """Test SQL rendering with Jinja2 template."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        mapping = engine.resolve_physical_mapping(
            logical_definition_id=1,
            engine_type='sqlite'
        )

        parameters = {
            'line': 'A',
            'start_date': '2026-01-27',
            'end_date': '2026-01-27'
        }

        sql = engine.render_sql(mapping, parameters)

        # Check that parameter placeholders exist
        assert ':line' in sql
        assert ':start_date' in sql
        assert ':end_date' in sql
        assert 'fact_production_records' in sql
        assert 'good_qty' in sql
        assert 'total_qty' in sql

    def test_render_sql_missing_parameters(self, test_db_path):
        """Test SQL rendering with missing parameters."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        mapping = engine.resolve_physical_mapping(
            logical_definition_id=1,
            engine_type='sqlite'
        )

        # Missing required parameters
        with pytest.raises(ValueError, match="Missing required parameters"):
            engine.render_sql(mapping, {'line': 'A'})  # Missing dates

    def test_execute_success(self, test_db_path):
        """Test successful SQL execution."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        sql = "SELECT COUNT(*) as count FROM fact_production_records"
        result = engine.execute(sql)

        assert result.success is True
        assert result.row_count == 1
        assert result.data[0]['count'] > 0
        assert result.execution_time_ms is not None
        assert result.error is None

    def test_execute_error(self, test_db_path):
        """Test SQL execution with error."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        # Invalid SQL
        sql = "SELECT * FROM nonexistent_table"
        result = engine.execute(sql)

        assert result.success is False
        assert result.error is not None
        assert 'no such table' in result.error.lower()

    def test_execute_with_mapping(self, test_db_path):
        """Test execution with physical mapping."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        parameters = {
            'line': 'A',
            'start_date': '2026-01-27',
            'end_date': '2026-01-27'
        }

        result = engine.execute_with_mapping(
            logical_definition_id=1,
            parameters=parameters,
            engine_type='sqlite'
        )

        assert result.success is True
        assert result.row_count == 1
        assert 'fpy' in result.data[0]

        # Check that FPY is calculated correctly
        fpy = result.data[0]['fpy']
        assert fpy is not None
        assert 0 <= fpy <= 1  # FPY should be between 0 and 1

    def test_preview(self, test_db_path):
        """Test preview mode (dry run)."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        parameters = {
            'line': 'A',
            'start_date': '2026-01-27',
            'end_date': '2026-01-27'
        }

        preview = engine.preview(
            logical_definition_id=1,
            parameters=parameters,
            engine_type='sqlite'
        )

        assert 'mapping' in preview
        assert 'sql' in preview
        assert 'parameters' in preview
        assert preview['mapping']['engine_type'] == 'sqlite'
        assert 'fact_production_records' in preview['sql']

    def test_execute_outputqty(self, test_db_path):
        """Test execution for OutputQty metric."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        parameters = {
            'line': 'B',
            'start_date': '2026-01-28',
            'end_date': '2026-01-28'
        }

        result = engine.execute_with_mapping(
            logical_definition_id=3,  # OutputQty (correct ID after adding FPY_v2)
            parameters=parameters,
            engine_type='sqlite'
        )

        assert result.success is True
        assert 'output_qty' in result.data[0]

        # Check that output is positive
        output_qty = result.data[0]['output_qty']
        assert output_qty is not None
        assert output_qty > 0

    def test_execute_defectrate(self, test_db_path):
        """Test execution for DefectRate metric."""
        engine = ExecutionEngine(metadata_db_path=test_db_path, data_db_path=test_db_path)

        parameters = {
            'line': 'A',
            'start_date': '2026-01-27',
            'end_date': '2026-01-27'
        }

        result = engine.execute_with_mapping(
            logical_definition_id=4,  # DefectRate (correct ID after adding FPY_v2)
            parameters=parameters,
            engine_type='sqlite'
        )

        assert result.success is True
        assert 'defect_rate' in result.data[0]

        # Check that defect rate is valid
        defect_rate = result.data[0]['defect_rate']
        assert defect_rate is not None
        assert 0 <= defect_rate <= 1  # Defect rate should be between 0 and 1

    def test_execution_result_to_dict(self, test_db_path):
        """Test ExecutionResult conversion to dict."""
        result = ExecutionResult(
            success=True,
            data=[{'fpy': 0.95}],
            row_count=1,
            sql='SELECT ...',
            execution_time_ms=10
        )

        result_dict = result.to_dict()

        assert result_dict['success'] is True
        assert result_dict['row_count'] == 1
        assert result_dict['sql'] == 'SELECT ...'
        assert result_dict['execution_time_ms'] == 10
        assert len(result_dict['data']) == 1

    def test_execution_result_failure(self, test_db_path):
        """Test ExecutionResult for failed execution."""
        result = ExecutionResult(
            success=False,
            error="Table not found",
            sql='SELECT * FROM missing',
            execution_time_ms=5
        )

        assert result.success is False
        assert result.error == "Table not found"
        assert result.row_count == 0
        assert len(result.data) == 0
