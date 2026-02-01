"""
Tests for impact analysis and DAG diff.
"""

import sqlite3
from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.impact_analysis import ImpactAnalyzer
from semantic_layer.dependency_builder import DependencyBuilder


class TestImpactAnalysis:
    def test_impact_metric_dependency(self, test_db_path):
        store = SQLiteMetadataStore(test_db_path)
        analyzer = ImpactAnalyzer(store)

        # FPY change should impact QualityScore
        impact = analyzer.impact("metric", 1)  # FPY
        assert 4 in impact["impacted_metrics"]  # QualityScore

    def test_diff_versions(self, test_db_path):
        store = SQLiteMetadataStore(test_db_path)
        analyzer = ImpactAnalyzer(store)

        diff = analyzer.diff("FPY", "FPY_v1_standard", "FPY_v2_rework")
        assert diff["risk"] in {"L2", "L3"}

    def test_generate_report(self, test_db_path):
        store = SQLiteMetadataStore(test_db_path)
        analyzer = ImpactAnalyzer(store)

        report = analyzer.generate_report("FPY", "FPY_v1_standard", "FPY_v2_rework")
        assert "markdown" in report
        assert "evidence" in report
        assert "audit_query" in report["evidence"]
        assert "version_a_id" in report["summary"]
        assert "version_b_id" in report["summary"]
        assert "version_a_id" in report["evidence"]["params"]
        assert report["summary"]["risk"] in {"L2", "L3"}


class TestDependencyBuilder:
    def test_build_dependencies_from_expression(self, test_db_path):
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Create a composite metric with explicit refs
        cursor.execute("""
            INSERT INTO semantic_object (name, description, aliases, domain, status)
            VALUES ('CompositeMetric', 'Composite Metric', '[]', 'quality', 'active')
        """)
        metric_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description)
            VALUES (?, 'Composite_v1', '2024-01-01 00:00:00', NULL, 1, 0, 'Composite')
        """, (metric_id,))
        version_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables)
            VALUES (?, '0.5*{{ metric:FPY }} + 0.5*{{ metric:DefectRate }}', 'line,day', 'Composite', '[]')
        """, (version_id,))

        conn.commit()
        conn.close()

        store = SQLiteMetadataStore(test_db_path)
        builder = DependencyBuilder(store)

        deps = builder.build_dependencies("CompositeMetric", "Composite_v1")
        assert len(deps) == 2
