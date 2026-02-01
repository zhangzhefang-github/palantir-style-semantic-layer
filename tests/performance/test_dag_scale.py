import sqlite3
import time
from pathlib import Path

from semantic_layer.sqlite_stores import SQLiteMetadataStore
from semantic_layer.dependency_builder import DependencyBuilder
from semantic_layer.impact_analysis import ImpactAnalyzer


MAX_REBUILD_SECONDS = 7.0
MAX_IMPACT_SECONDS = 1.5
MAX_DIFF_SECONDS = 1.5


def _init_db(db_path: str):
    schema_sql = Path(__file__).parent.parent.parent / "schema.sql"
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def test_dag_scale_performance(tmp_path):
    db_path = str(tmp_path / "scale.db")
    _init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    num_metrics = 420
    metrics = []
    for i in range(1, num_metrics + 1):
        name = f"Metric{i}"
        cursor.execute(
            "INSERT INTO semantic_object (name, description, aliases, domain, status) VALUES (?, ?, ?, ?, 'active')",
            (name, name, "[]", "quality")
        )
        metrics.append((cursor.lastrowid, name))

    for metric_id, name in metrics:
        cursor.execute(
            "INSERT INTO semantic_version (semantic_object_id, version_name, effective_from, scenario_condition, is_active, priority, description) "
            "VALUES (?, ?, '2024-01-01 00:00:00', NULL, 1, 0, ?)",
            (metric_id, f"{name}_v1", name)
        )
        version_id = cursor.lastrowid
        idx = int(name.replace("Metric", ""))
        refs = []
        if idx > 6:
            refs = [
                f"{{{{ metric:Metric{idx-1} }}}}",
                f"{{{{ metric:Metric{idx-2} }}}}",
                f"{{{{ metric:Metric{idx-3} }}}}",
                f"{{{{ metric:Metric{idx-4} }}}}",
                f"{{{{ metric:Metric{idx-5} }}}}",
            ]
        expr = " + ".join(refs) if refs else "1"
        cursor.execute(
            "INSERT INTO logical_definition (semantic_version_id, expression, grain, description, variables) "
            "VALUES (?, ?, 'line,day', ?, '[]')",
            (version_id, expr, name)
        )
        logical_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO physical_mapping (logical_definition_id, engine_type, connection_ref, sql_template, params_schema, priority, description) "
            "VALUES (?, 'sqlite', 'default', 'SELECT 1', '{\"line\":\"string\",\"start_date\":\"date\",\"end_date\":\"date\"}', 1, 'scale')",
            (logical_id,)
        )

    conn.commit()
    conn.close()

    store = SQLiteMetadataStore(db_path)
    builder = DependencyBuilder(store)
    analyzer = ImpactAnalyzer(store)

    start = time.perf_counter()
    builder.rebuild_all()
    rebuild_time = time.perf_counter() - start
    assert rebuild_time < MAX_REBUILD_SECONDS

    start = time.perf_counter()
    impact = analyzer.impact("metric", metrics[-1][0])
    impact_time = time.perf_counter() - start
    assert impact_time < MAX_IMPACT_SECONDS
    assert metrics[-1][0] in impact["impacted_metrics"]

    # diff between same version should be fast
    metric_name = metrics[len(metrics) // 2][1]
    start = time.perf_counter()
    diff = analyzer.diff(metric_name, f"{metric_name}_v1", f"{metric_name}_v1")
    diff_time = time.perf_counter() - start
    assert diff_time < MAX_DIFF_SECONDS
    assert diff["risk"] == "L1"
