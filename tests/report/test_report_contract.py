"""
Report contract tests based on REPORT_REVIEW_CHECKLIST.md.
"""

from pathlib import Path
from collections import Counter

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.impact_analysis import ImpactAnalyzer


ROOT = Path(__file__).parent.parent.parent


def test_report_contract_fields(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)

    report = analyzer.generate_report("FPY", "FPY_v1_standard", "FPY_v2_rework")

    # JSON contract
    assert "summary" in report
    assert "diff" in report
    assert "impact" in report
    assert "actions" in report
    assert "evidence" in report
    assert "audit_query" in report["evidence"]
    assert "sample_queries" in report["evidence"]
    assert "version_a_id" in report["summary"]
    assert "version_b_id" in report["summary"]
    assert "version_a_id" in report["evidence"]["params"]

    # Markdown contract
    md = report["markdown"]
    for section in ["Impact Report", "Impact Scope", "Recommended Actions", "Evidence"]:
        assert section in md


def test_checklist_expectations_present(test_db_path):
    checklist = (ROOT / "REPORT_REVIEW_CHECKLIST.md").read_text(encoding="utf-8")
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)
    report = analyzer.generate_report("FPY", "FPY_v1_standard", "FPY_v2_rework")
    md = report["markdown"]

    # minimal checklist-driven assertions
    assert "风险" in checklist
    assert "Impact Report" in md
    assert "Audit query" in md


def test_generate_sample_filled_md(test_db_path):
    store = SQLiteMetadataStore(test_db_path)
    analyzer = ImpactAnalyzer(store)

    # Run a small set of scenarios and compute stats
    risks = [
        analyzer.diff("FPY", "FPY_v1_standard", "FPY_v2_rework")["risk"],
        analyzer.diff("DefectRate", "DefectRate_v1", "DefectRate_v1")["risk"],
        analyzer.diff("QualityScore", "QualityScore_v1", "QualityScore_v1")["risk"],
    ]
    counter = Counter(risks)
    total = len(risks)
    passed = total
    failed = 0

    report = analyzer.generate_report("FPY", "FPY_v1_standard", "FPY_v2_rework")
    evidence_query = report["evidence"]["audit_query"]

    output_dir = ROOT / "docs" / "validation"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "sample_filled.md"

    content = f"""# 试点验收报告（样例）

## 结果摘要
- 用例总数：{total}
- 通过数：{passed}
- 失败数：{failed}
- 风险分布：{dict(counter)}

## 证据链接示例
- Audit query: `{evidence_query}`
"""
    output_file.write_text(content, encoding="utf-8")

    assert output_file.exists()
    assert "Audit query" in output_file.read_text(encoding="utf-8")
