import json
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from semantic_layer.impact_analysis import ImpactAnalyzer
from semantic_layer.sqlite_stores import SQLiteMetadataStore


def build_approval_package(change_context: Dict[str, Any], output_dir: str) -> Dict[str, str]:
    """
    Build approval package based on existing governance outputs.

    change_context requires:
      - db_path
      - metric_name
      - version_a
      - version_b
    """
    db_path = change_context["db_path"]
    metric_name = change_context["metric_name"]
    version_a = change_context["version_a"]
    version_b = change_context["version_b"]

    store = SQLiteMetadataStore(db_path)
    analyzer = ImpactAnalyzer(store)
    report = analyzer.generate_report(metric_name, version_a, version_b)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    report_json_path = output / "impact_report.json"
    report_md_path = output / "impact_report.md"
    evidence_sql_path = output / "evidence_queries.sql"
    sample_sql_path = output / "sample_queries.sql"
    summary_path = output / "summary.json"
    manifest_path = output / "manifest.json"

    report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md_path.write_text(report["markdown"], encoding="utf-8")

    evidence = report["evidence"]
    evidence_sql_path.write_text(evidence["audit_query"], encoding="utf-8")
    sample_queries = "\n".join(q["sql"] for q in evidence.get("sample_queries", []))
    sample_sql_path.write_text(sample_queries, encoding="utf-8")

    summary = {
        "metric": report["summary"]["metric"],
        "version_a": report["summary"]["version_a"],
        "version_b": report["summary"]["version_b"],
        "risk": report["summary"]["risk"],
        "impact_counts": {
            "metrics": len(report["impact"]["impacted_metrics"]),
            "mappings": len(report["impact"]["impacted_mappings"]),
            "entities": len(report["impact"]["impacted_entities"]),
            "dimensions": len(report["impact"]["impacted_dimensions"]),
            "attributes": len(report["impact"]["impacted_attributes"]),
        }
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = _build_manifest(
        change_context,
        {
            "impact_report_md": report_md_path,
            "impact_report_json": report_json_path,
            "evidence_queries_sql": evidence_sql_path,
            "sample_queries_sql": sample_sql_path,
            "summary_json": summary_path
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "impact_report_json": str(report_json_path),
        "impact_report_md": str(report_md_path),
        "evidence_queries_sql": str(evidence_sql_path),
        "sample_queries_sql": str(sample_sql_path),
        "summary_json": str(summary_path),
        "manifest_json": str(manifest_path)
    }


def _build_manifest(change_context: Dict[str, Any], files: Dict[str, Path]) -> Dict[str, Any]:
    package_id = str(uuid.uuid4())
    generated_at = datetime.now(timezone.utc).isoformat()
    file_entries = {k: str(v) for k, v in files.items()}
    checksums = {k: _checksum_file(v) for k, v in files.items()}

    return {
        "package_id": package_id,
        "generated_at": generated_at,
        "change_context": {
            "metric": change_context.get("metric_name"),
            "version_a": change_context.get("version_a"),
            "version_b": change_context.get("version_b"),
            "change_type": change_context.get("change_type", "version_change")
        },
        "files": file_entries,
        "checksums": checksums
    }


def _checksum_file(path: Path) -> str:
    sha = hashlib.sha256()
    sha.update(path.read_bytes())
    return sha.hexdigest()
