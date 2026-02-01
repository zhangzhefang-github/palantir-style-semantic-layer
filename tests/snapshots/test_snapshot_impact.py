import json
from pathlib import Path

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.impact_analysis import ImpactAnalyzer
from tests.utils.snapshot_diff import diff_json, format_json_diff, load_json


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _normalize_impact(payload):
    return {
        "target": payload["target"],
        "impacted_metrics": payload["impacted_metrics"],
        "impacted_mappings": payload["impacted_mappings"],
        "impacted_entities": payload["impacted_entities"],
        "impacted_dimensions": payload["impacted_dimensions"],
        "impacted_attributes": payload["impacted_attributes"],
    }


def _normalize_diff(payload):
    return {
        "metric": payload["metric"],
        "version_a": payload["version_a"],
        "version_b": payload["version_b"],
        "logical_change": payload["logical_change"],
        "mapping_change": payload["mapping_change"],
        "risk": payload["risk"],
    }


def _load_snapshot(name):
    return load_json(SNAPSHOT_DIR / name)


def _assert_snapshot(name, actual):
    expected = _load_snapshot(name)
    if actual != expected:
        changes = diff_json(expected, actual)
        raise AssertionError(format_json_diff(changes))


def test_snapshot_impact_cases(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)

    cases = [
        ("impact_fpy.json", ("metric", 1)),
        ("impact_quality.json", ("metric", 4)),
        ("impact_defect.json", ("metric", 3)),
    ]

    for snapshot, (target_type, target_id) in cases:
        impact = analyzer.impact(target_type, target_id)
        _assert_snapshot(snapshot, _normalize_impact(impact))


def test_snapshot_diff_cases(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)

    cases = [
        ("diff_fpy.json", ("FPY", "FPY_v1_standard", "FPY_v2_rework")),
        ("diff_quality.json", ("QualityScore", "QualityScore_v1", "QualityScore_v1")),
        ("diff_defect.json", ("DefectRate", "DefectRate_v1", "DefectRate_v1")),
    ]

    for snapshot, args in cases:
        diff = analyzer.diff(*args)
        _assert_snapshot(snapshot, _normalize_diff(diff))
