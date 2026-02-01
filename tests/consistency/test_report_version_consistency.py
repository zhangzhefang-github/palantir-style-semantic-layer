import sqlite3

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.impact_analysis import ImpactAnalyzer
from semantic_layer.dependency_builder import DependencyBuilder

from tests.fixtures.semantic_fixtures import (
    create_version,
    create_logical_definition,
    create_mapping,
)


def test_report_version_consistency(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    builder = DependencyBuilder(store)
    analyzer = ImpactAnalyzer(store)

    metric = store.get_semantic_object_by_name("QualityScore")
    base_versions = store.get_versions_for_object(metric.id)
    base_version = next(v for v in base_versions if v.version_name == "QualityScore_v1")

    new_version_name = "QualityScore_v2_consistency"
    new_version_id = create_version(
        test_db_path, metric.id, new_version_name, "2024-01-03 00:00:00"
    )
    logical_id = create_logical_definition(
        test_db_path, new_version_id,
        "0.5*{{ metric:FPY }} + 0.5*(1-{{ metric:DefectRate }})",
        "line,day", "consistency", "[]"
    )
    create_mapping(
        test_db_path, logical_id, "SELECT 1", '{"line":"string","start_date":"date","end_date":"date"}'
    )

    builder.rebuild_for_metric("QualityScore")

    report = analyzer.generate_report("QualityScore", "QualityScore_v1", new_version_name)

    summary = report["summary"]
    assert summary["version_b_id"] == new_version_id

    rows = _fetch_dependencies(test_db_path, metric.id, new_version_id)
    assert rows
    for downstream_metric_id, downstream_version_id in rows:
        assert downstream_metric_id == metric.id
        assert downstream_version_id == new_version_id

    evidence_params = report["evidence"]["params"]
    assert evidence_params["version_b_id"] == summary["version_b_id"]


def _fetch_dependencies(db_path: str, metric_id: int, version_id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT downstream_metric_id, downstream_version_id
        FROM metric_dependency
        WHERE downstream_metric_id = ? AND downstream_version_id = ?
        """,
        (metric_id, version_id)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
