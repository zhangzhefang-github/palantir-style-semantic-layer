"""
End-to-end change impact flow tests.
"""

import sqlite3
import json
import pytest

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.dependency_builder import DependencyBuilder
from semantic_layer.impact_analysis import ImpactAnalyzer
from semantic_layer.grain_validator import GrainValidator

from tests.fixtures.db_fixtures import exec_sql, fetch_all
from tests.fixtures.semantic_fixtures import (
    create_version,
    create_logical_definition,
    create_mapping,
)


def _get_metric_ids(store: SQLiteMetadataStore):
    fpy = store.get_semantic_object_by_name("FPY")
    defect = store.get_semantic_object_by_name("DefectRate")
    quality = store.get_semantic_object_by_name("QualityScore")
    return fpy.id, defect.id, quality.id


def _get_version_id(store: SQLiteMetadataStore, metric_id: int, version_name: str) -> int:
    versions = store.get_versions_for_object(metric_id)
    for v in versions:
        if v.version_name == version_name:
            return v.id
    raise ValueError("version not found")


def _assert_dependency_versions(db_path: str, downstream_version_id: int):
    rows = fetch_all(
        db_path,
        """
        SELECT downstream_version_id, upstream_version_id
        FROM metric_dependency
        WHERE downstream_version_id = ?
        """,
        (downstream_version_id,)
    )
    for downstream_id, upstream_id in rows:
        assert downstream_id == downstream_version_id
        assert upstream_id is not None


@pytest.mark.parametrize("case", [
    # Logical definition changes (L2)
    {"id": "LC1", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "logical", "new_expression": "good_qty / (total_qty + 1)", "expected_risk": "L2"},
    {"id": "LC2", "metric": "DefectRate", "base_version": "DefectRate_v1",
     "change": "logical", "new_expression": "(total_qty - good_qty) / (total_qty + 1)", "expected_risk": "L2"},
    {"id": "LC3", "metric": "QualityScore", "base_version": "QualityScore_v1",
     "change": "logical", "new_expression": "0.6*{{ metric:FPY }} + 0.4*(1-{{ metric:DefectRate }})", "expected_risk": "L2"},
    {"id": "LC4", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "logical", "new_expression": "good_qty / total_qty", "expected_risk": "L1"},
    {"id": "LC5", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "logical", "new_expression": "good_qty / total_qty", "expected_risk": "L1"},

    # Version changes (L1)
    {"id": "VC1", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "version_same_logic", "expected_risk": "L1"},
    {"id": "VC2", "metric": "DefectRate", "base_version": "DefectRate_v1",
     "change": "version_same_logic", "expected_risk": "L1"},
    {"id": "VC3", "metric": "QualityScore", "base_version": "QualityScore_v1",
     "change": "version_same_logic", "expected_risk": "L1"},

    # Mapping changes (L2)
    {"id": "MC1", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "mapping_only", "expected_risk": "L2"},
    {"id": "MC2", "metric": "DefectRate", "base_version": "DefectRate_v1",
     "change": "mapping_only", "expected_risk": "L2"},

    # Entity/relationship changes (impact coverage)
    {"id": "ER1", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "entity_relation", "expected_risk": "L1"},
    {"id": "ER2", "metric": "QualityScore", "base_version": "QualityScore_v1",
     "change": "entity_relation", "expected_risk": "L1"},

    # Grain/Dimension gate (FAIL)
    {"id": "G1", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "grain_fail", "dimensions": ["sku"], "expected_risk": "L1"},
    {"id": "G2", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "grain_fail", "dimensions": ["line", "plant"], "expected_risk": "L1"},
    {"id": "G3", "metric": "QualityScore", "base_version": "QualityScore_v1",
     "change": "grain_fail", "dimensions": ["plant"], "expected_risk": "L1"},

    # Params schema change (mapping L2)
    {"id": "MC3", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "mapping_params", "expected_risk": "L2"},

    # Variable removal (logical L2)
    {"id": "LC6", "metric": "DefectRate", "base_version": "DefectRate_v1",
     "change": "logical", "new_expression": "total_qty / total_qty", "expected_risk": "L2"},
    {"id": "LC7", "metric": "QualityScore", "base_version": "QualityScore_v1",
     "change": "logical", "new_expression": "0.8*{{ metric:FPY }} + 0.2*(1-{{ metric:DefectRate }})", "expected_risk": "L2"},
    {"id": "LC8", "metric": "FPY", "base_version": "FPY_v1_standard",
     "change": "logical", "new_expression": "good_qty / total_qty", "expected_risk": "L1"},
], ids=lambda c: c["id"])
def test_change_impact_flow(test_db_path, case):
    store = SQLiteMetadataStore(test_db_path)
    builder = DependencyBuilder(store)
    analyzer = ImpactAnalyzer(store)
    validator = GrainValidator(store)

    metric = store.get_semantic_object_by_name(case["metric"])
    base_version_id = _get_version_id(store, metric.id, case["base_version"])
    logical_def = store.get_logical_definition(base_version_id)
    base_mapping_row = fetch_all(
        test_db_path,
        "SELECT sql_template, params_schema FROM physical_mapping WHERE logical_definition_id = ?",
        (logical_def.id,)
    )[0]
    base_sql, base_params = base_mapping_row

    new_version_name = f"{case['base_version']}_chg_{case['id']}"
    new_version_id = None

    if case["change"] == "logical":
        new_version_id = create_version(
            test_db_path, metric.id, new_version_name, "2024-01-02 00:00:00"
        )
        logical_id = create_logical_definition(
            test_db_path, new_version_id, case["new_expression"],
            logical_def.grain, "changed", json.dumps(logical_def.variables)
        )
        create_mapping(
            test_db_path,
            logical_id=logical_id,
            sql_template=base_sql,
            params_schema=base_params
        )

    elif case["change"] == "version_same_logic":
        new_version_id = create_version(
            test_db_path, metric.id, new_version_name, "2024-01-02 00:00:00"
        )
        logical_id = create_logical_definition(
            test_db_path, new_version_id, logical_def.expression,
            logical_def.grain, "same", json.dumps(logical_def.variables)
        )
        create_mapping(
            test_db_path,
            logical_id=logical_id,
            sql_template=base_sql,
            params_schema=base_params
        )

    elif case["change"] == "mapping_only":
        new_version_id = create_version(
            test_db_path, metric.id, new_version_name, "2024-01-02 00:00:00"
        )
        logical_id = create_logical_definition(
            test_db_path, new_version_id, logical_def.expression,
            logical_def.grain, "same", json.dumps(logical_def.variables)
        )
        create_mapping(
            test_db_path,
            logical_id=logical_id,
            sql_template=base_sql + " -- changed",
            params_schema=base_params
        )

    elif case["change"] == "mapping_params":
        new_version_id = create_version(
            test_db_path, metric.id, new_version_name, "2024-01-02 00:00:00"
        )
        logical_id = create_logical_definition(
            test_db_path, new_version_id, logical_def.expression,
            logical_def.grain, "same", json.dumps(logical_def.variables)
        )
        create_mapping(
            test_db_path,
            logical_id=logical_id,
            sql_template=base_sql,
            params_schema='{"line":"string","start_date":"date","end_date":"date","shift":"string"}'
        )

    elif case["change"] == "entity_relation":
        exec_sql(test_db_path, [
            ("UPDATE ontology_relationship SET description = ? WHERE id = 1", (f"changed_{case['id']}",))
        ])

    elif case["change"] == "grain_fail":
        pass

    # rebuild dependencies and check cycles
    builder.rebuild_for_metric(metric.name)
    cycles = builder.detect_cycles()
    assert cycles == []

    # dependency version checks for quality score
    if metric.name == "QualityScore":
        _assert_dependency_versions(test_db_path, base_version_id)

    # impact/diff/report checks
    impact = analyzer.impact("metric", metric.id)
    assert metric.id in impact["impacted_metrics"]

    version_a = case["base_version"]
    version_b = new_version_name if new_version_id else case["base_version"]
    diff = analyzer.diff(metric.name, version_a, version_b)
    assert diff["risk"] == case["expected_risk"]

    report = analyzer.generate_report(metric.name, version_a, version_b)
    assert "evidence" in report
    assert "audit_query" in report["evidence"]

    # grain validation gate
    params = {
        "line": "A",
        "start_date": "2026-01-27",
        "end_date": "2026-01-27",
        "dimensions": case.get("dimensions")
    }
    validation = validator.validate(metric.id, params, logical_def.grain or "")
    if case["change"] == "grain_fail":
        assert validation["status"] == "FAIL"
        assert validation["action"] == "REFUSE"
        assert "suggestions" in validation
    else:
        assert validation["status"] in {"PASS", "WARN"}
