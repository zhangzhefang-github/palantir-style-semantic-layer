"""
Fail-closed tests for dependency builder and cycle detection.
"""

import pytest

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.dependency_builder import DependencyBuilder

from tests.fixtures.semantic_fixtures import (
    create_metric,
    create_version,
    create_logical_definition,
    create_mapping,
)


def test_unresolved_metric_reference_fail_closed(test_db_path):
    metric_id = create_metric(
        test_db_path, "BadMetric", "bad", "[]", "quality"
    )
    version_id = create_version(
        test_db_path, metric_id, "BadMetric_v1", "2024-01-01 00:00:00"
    )
    logical_id = create_logical_definition(
        test_db_path, version_id, "{{ metric:DoesNotExist }} + 1", "line,day", "bad", "[]"
    )
    create_mapping(
        test_db_path, logical_id, "SELECT 1", '{"line":"string","start_date":"date","end_date":"date"}'
    )

    store = SQLiteMetadataStore(test_db_path)
    builder = DependencyBuilder(store)

    with pytest.raises(ValueError, match="Unresolved metric reference"):
        builder.build_dependencies("BadMetric", "BadMetric_v1")


def test_cycle_detection_fail_closed(test_db_path):
    a_id = create_metric(test_db_path, "MetricA", "A", "[]", "quality")
    b_id = create_metric(test_db_path, "MetricB", "B", "[]", "quality")

    a_v = create_version(test_db_path, a_id, "MetricA_v1", "2024-01-01 00:00:00")
    b_v = create_version(test_db_path, b_id, "MetricB_v1", "2024-01-01 00:00:00")

    a_logical = create_logical_definition(
        test_db_path, a_v, "{{ metric:MetricB }} + 1", "line,day", "A", "[]"
    )
    b_logical = create_logical_definition(
        test_db_path, b_v, "{{ metric:MetricA }} + 1", "line,day", "B", "[]"
    )

    create_mapping(
        test_db_path, a_logical, "SELECT 1", '{"line":"string","start_date":"date","end_date":"date"}'
    )
    create_mapping(
        test_db_path, b_logical, "SELECT 1", '{"line":"string","start_date":"date","end_date":"date"}'
    )

    store = SQLiteMetadataStore(test_db_path)
    builder = DependencyBuilder(store)

    with pytest.raises(ValueError, match="Dependency cycles detected"):
        builder.rebuild_all()
