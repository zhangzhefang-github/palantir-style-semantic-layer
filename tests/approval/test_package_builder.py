from pathlib import Path
import json

from governance.approval_package import build_approval_package


def test_build_approval_package(test_db_path, tmp_path):
    output_dir = tmp_path / "pkg"
    result = build_approval_package(
        {
            "db_path": test_db_path,
            "metric_name": "FPY",
            "version_a": "FPY_v1_standard",
            "version_b": "FPY_v2_rework"
        },
        str(output_dir)
    )

    for key, path in result.items():
        assert Path(path).exists()

    summary = json.loads(Path(result["summary_json"]).read_text(encoding="utf-8"))
    assert summary["risk"] in {"L2", "L3"}
