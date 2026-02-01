import json
from pathlib import Path

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.impact_analysis import ImpactAnalyzer
from tests.utils.snapshot_diff import diff_json, format_json_diff, diff_markdown_by_heading, format_markdown_diff


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


def _normalize_report(report):
    return {
        "summary": report["summary"],
        "impact": report["impact"],
        "diff": {
            "metric": report["diff"]["metric"],
            "version_a": report["diff"]["version_a"],
            "version_b": report["diff"]["version_b"],
            "logical_change": report["diff"]["logical_change"],
            "mapping_change": report["diff"]["mapping_change"],
            "risk": report["diff"]["risk"],
        },
        "actions": report["actions"],
        "evidence": {
            "audit_query": report["evidence"]["audit_query"],
            "params": report["evidence"]["params"],
        },
    }


def _load_snapshot(name):
    return (SNAPSHOT_DIR / name).read_text(encoding="utf-8")


def test_snapshot_report_json(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)
    report = analyzer.generate_report("FPY", "FPY_v1_standard", "FPY_v2_rework")

    actual = json.dumps(_normalize_report(report), sort_keys=True, ensure_ascii=False, indent=2)
    expected = _load_snapshot("report_fpy.json")
    if actual != expected:
        expected_obj = json.loads(expected)
        actual_obj = json.loads(actual)
        changes = diff_json(expected_obj, actual_obj)
        raise AssertionError(format_json_diff(changes))


def test_snapshot_report_markdown(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)
    report = analyzer.generate_report("FPY", "FPY_v1_standard", "FPY_v2_rework")

    expected = _load_snapshot("report_fpy.md")
    if report["markdown"] != expected:
        changes = diff_markdown_by_heading(expected, report["markdown"])
        raise AssertionError(format_markdown_diff(changes))
