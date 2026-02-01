"""
Grain validator gate tests.
"""

import pytest

from datetime import datetime
from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.grain_validator import GrainValidator
from semantic_layer.orchestrator import SemanticOrchestrator
from semantic_layer.models import ExecutionContext


def test_grain_validator_refuse_with_suggestions(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    validator = GrainValidator(store)

    metric = store.get_semantic_object_by_name("FPY")
    versions = store.get_versions_for_object(metric.id)
    logical_def = store.get_logical_definition(versions[0].id)

    params = {
        "line": "A",
        "start_date": "2026-01-27",
        "end_date": "2026-01-27",
        "dimensions": ["sku"]
    }
    validation = validator.validate(metric.id, params, logical_def.grain or "")
    assert validation["status"] == "FAIL"
    assert validation["action"] == "REFUSE"
    assert "suggestions" in validation


def test_grain_gate_blocks_execution_with_message(test_db_path):
    orchestrator = SemanticOrchestrator(test_db_path)
    context = ExecutionContext(user_id=1, role="operator", parameters={}, timestamp=datetime.now())

    result = orchestrator.query(
        question="按SKU看一次合格率",
        parameters={
            "line": "A",
            "start_date": "2026-01-27",
            "end_date": "2026-01-27",
            "dimensions": ["sku"]
        },
        context=context
    )

    assert result["status"] == "error"
    assert "Suggestions" in result.get("error", "")
